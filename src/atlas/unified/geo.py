"""ISO-3166-1 alpha-2 geography normalization and parsing.

Parses free-text distributions (from EPD, Kew WCVP, etc.) into standardized
ISO-3166-1 alpha-2 two-letter country codes.
"""
from __future__ import annotations

import html
import re
import unicodedata

# All 249 officially assigned ISO-3166-1 alpha-2 codes
ISO_3166_1_ALPHA2: frozenset[str] = frozenset({
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS",
    "BT", "BV", "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE",
    "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF",
    "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT", "JE", "JM",
    "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC",
    "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ", "NA",
    "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG",
    "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS",
    "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO",
    "TR", "TT", "TV", "TW", "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW",
})

# Words that should not be interpreted as 2-letter country codes when lowercase
_STOPWORDS_2LETTER = frozenset({
    "in", "it", "is", "so", "at", "by", "no", "as", "to", "do", "be", "an", "or", "if",
    "my", "on", "he", "we", "us", "am", "me", "up", "of", "go",
})


def _normalize(name: str) -> str:
    """Normalize country string for dictionary lookup: ascii lowercase, uniform spacing."""
    s = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    s = s.lower()
    s = s.replace("&", " and ")
    s = s.replace("’", "'").replace("′", "'").replace("`", "'")
    s = re.sub(r"['\"]", "", s)
    s = re.sub(r"[\-_/]", " ", s)
    s = re.sub(r"[^a-z0-9\s()]+", " ", s)
    return " ".join(s.split())


# Mapping from raw country name / alias to ISO-3166-1 alpha-2 code
_RAW_COUNTRY_ALIASES: dict[str, str] = {
    # Afghanistan
    "afghanistan": "AF", "afg": "AF",
    # Albania
    "albania": "AL", "alb": "AL",
    # Algeria
    "algeria": "DZ", "dza": "DZ",
    # Andorra
    "andorra": "AD", "and": "AD",
    # Angola
    "angola": "AO", "ago": "AO",
    # Antigua and Barbuda
    "antigua and barbuda": "AG", "antigua & barbuda": "AG", "antigua": "AG", "barbuda": "AG", "atg": "AG",
    # Argentina
    "argentina": "AR", "arg": "AR",
    # Armenia
    "armenia": "AM", "arm": "AM",
    # Australia
    "australia": "AU", "aus": "AU", "tasmania": "AU",
    # Austria
    "austria": "AT", "aut": "AT",
    # Azerbaijan
    "azerbaijan": "AZ", "aze": "AZ",
    # Bahamas
    "bahamas": "BS", "the bahamas": "BS", "bhs": "BS",
    # Bahrain
    "bahrain": "BH", "bhr": "BH",
    # Bangladesh
    "bangladesh": "BD", "bgd": "BD",
    # Barbados
    "barbados": "BB", "brb": "BB",
    # Belarus
    "belarus": "BY", "blr": "BY", "belorussia": "BY", "byelorussia": "BY",
    # Belgium
    "belgium": "BE", "bel": "BE",
    # Belize
    "belize": "BZ", "blz": "BZ",
    # Benin
    "benin": "BJ", "ben": "BJ", "dahomey": "BJ",
    # Bhutan
    "bhutan": "BT", "btn": "BT",
    # Bolivia
    "bolivia": "BO", "bolivia plurinational state of": "BO", "bol": "BO",
    # Bosnia and Herzegovina
    "bosnia and herzegovina": "BA", "bosnia & herzegovina": "BA", "bosnia": "BA", "herzegovina": "BA", "bih": "BA",
    # Botswana
    "botswana": "BW", "bwa": "BW",
    # Brazil
    "brazil": "BR", "brasil": "BR", "bra": "BR",
    # Brunei
    "brunei": "BN", "brunei darussalam": "BN", "brn": "BN",
    # Bulgaria
    "bulgaria": "BG", "bgr": "BG",
    # Burkina Faso
    "burkina faso": "BF", "burkina": "BF", "bfa": "BF", "upper volta": "BF",
    # Burundi
    "burundi": "BI", "bdi": "BI",
    # Cabo Verde / Cape Verde
    "cape verde": "CV", "cabo verde": "CV", "cpv": "CV",
    # Cambodia
    "cambodia": "KH", "khm": "KH", "kampuchea": "KH",
    # Cameroon
    "cameroon": "CM", "cameroun": "CM", "cmr": "CM",
    # Canada
    "canada": "CA", "can": "CA",
    # Central African Republic
    "central african republic": "CF", "caf": "CF", "car": "CF",
    # Chad
    "chad": "TD", "tcd": "TD",
    # Chile
    "chile": "CL", "chl": "CL",
    # China
    "china": "CN", "peoples republic of china": "CN", "prc": "CN", "chn": "CN",
    # Colombia
    "colombia": "CO", "col": "CO",
    # Comoros
    "comoros": "KM", "com": "KM",
    # Congo (Democratic Republic)
    "democratic republic of the congo": "CD", "congo drc": "CD", "dr congo": "CD",
    "congo (drc)": "CD", "drc": "CD", "zaire": "CD", "congo dem rep": "CD",
    "congo democratic republic of the": "CD", "cod": "CD",
    # Congo (Republic)
    "republic of the congo": "CG", "congo republic": "CG", "congo (republic)": "CG",
    "congo brazzaville": "CG", "congo rep": "CG", "congo": "CG", "cog": "CG",
    # Costa Rica
    "costa rica": "CR", "cri": "CR",
    # Cote d'Ivoire
    "cote d'ivoire": "CI", "cote divoire": "CI", "cote d ivoire": "CI", "ivory coast": "CI", "civ": "CI",
    # Croatia
    "croatia": "HR", "hrv": "HR",
    # Cuba
    "cuba": "CU", "cub": "CU",
    # Cyprus
    "cyprus": "CY", "cyp": "CY",
    # Czechia
    "czechia": "CZ", "czech republic": "CZ", "cze": "CZ",
    # Denmark
    "denmark": "DK", "dnk": "DK",
    # Djibouti
    "djibouti": "DJ", "dji": "DJ",
    # Dominica
    "dominica": "DM", "dma": "DM",
    # Dominican Republic
    "dominican republic": "DO", "dom": "DO",
    # Ecuador
    "ecuador": "EC", "ecu": "EC",
    # Egypt
    "egypt": "EG", "egy": "EG",
    # El Salvador
    "el salvador": "SV", "slv": "SV",
    # Equatorial Guinea
    "equatorial guinea": "GQ", "gnq": "GQ",
    # Eritrea
    "eritrea": "ER", "eri": "ER",
    # Estonia
    "estonia": "EE", "est": "EE",
    # Eswatini / Swaziland
    "eswatini": "SZ", "swaziland": "SZ", "swz": "SZ",
    # Ethiopia
    "ethiopia": "ET", "eth": "ET",
    # Fiji
    "fiji": "FJ", "fji": "FJ",
    # Finland
    "finland": "FI", "fin": "FI",
    # France
    "france": "FR", "fra": "FR",
    # French Guiana
    "french guiana": "GF", "french guyana": "GF", "guf": "GF",
    # Gabon
    "gabon": "GA", "gab": "GA",
    # Gambia
    "gambia": "GM", "the gambia": "GM", "gmb": "GM",
    # Georgia
    "georgia": "GE", "geo": "GE",
    # Germany
    "germany": "DE", "deutschland": "DE", "deu": "DE",
    # Ghana
    "ghana": "GH", "gha": "GH",
    # Greece
    "greece": "GR", "grc": "GR",
    # Grenada
    "grenada": "GD", "grd": "GD",
    # Guatemala
    "guatemala": "GT", "gtm": "GT",
    # Guinea
    "guinea": "GN", "guinee": "GN", "gin": "GN",
    # Guinea-Bissau
    "guinea bissau": "GW", "guinea-bissau": "GW", "gnb": "GW",
    # Guyana
    "guyana": "GY", "guy": "GY",
    # Haiti
    "haiti": "HT", "hti": "HT",
    # Honduras
    "honduras": "HN", "hnd": "HN",
    # Hungary
    "hungary": "HU", "hun": "HU",
    # Iceland
    "iceland": "IS", "isl": "IS",
    # India
    "india": "IN", "ind": "IN",
    # Indonesia
    "indonesia": "ID", "idn": "ID",
    # Iran
    "iran": "IR", "iran islamic republic of": "IR", "irn": "IR",
    # Iraq
    "iraq": "IQ", "irq": "IQ",
    # Ireland
    "ireland": "IE", "republic of ireland": "IE", "irl": "IE",
    # Israel
    "israel": "IL", "isr": "IL",
    # Italy
    "italy": "IT", "ita": "IT",
    # Jamaica
    "jamaica": "JM", "jam": "JM",
    # Japan
    "japan": "JP", "jpn": "JP",
    # Jordan
    "jordan": "JO", "jor": "JO",
    # Kazakhstan
    "kazakhstan": "KZ", "kaz": "KZ",
    # Kenya
    "kenya": "KE", "ken": "KE",
    # Kiribati
    "kiribati": "KI", "kir": "KI",
    # North Korea
    "north korea": "KP", "korea north": "KP", "democratic peoples republic of korea": "KP",
    "dprk": "KP", "prk": "KP",
    # South Korea
    "south korea": "KR", "korea south": "KR", "republic of korea": "KR",
    "korea": "KR", "kor": "KR",
    # Kuwait
    "kuwait": "KW", "kwt": "KW",
    # Kyrgyzstan
    "kyrgyzstan": "KG", "kyrgyz republic": "KG", "kgz": "KG",
    # Laos
    "laos": "LA", "lao peoples democratic republic": "LA", "lao pdr": "LA", "lao": "LA",
    # Latvia
    "latvia": "LV", "lva": "LV",
    # Lebanon
    "lebanon": "LB", "lbn": "LB",
    # Lesotho
    "lesotho": "LS", "lso": "LS",
    # Liberia
    "liberia": "LR", "lbr": "LR",
    # Libya
    "libya": "LY", "lby": "LY",
    # Liechtenstein
    "liechtenstein": "LI", "lie": "LI",
    # Lithuania
    "lithuania": "LT", "ltu": "LT",
    # Luxembourg
    "luxembourg": "LU", "lux": "LU",
    # Madagascar
    "madagascar": "MG", "mdg": "MG",
    # Malawi
    "malawi": "MW", "mwi": "MW",
    # Malaysia
    "malaysia": "MY", "mys": "MY",
    # Maldives
    "maldives": "MV", "mdv": "MV",
    # Mali
    "mali": "ML", "mli": "ML",
    # Malta
    "malta": "MT", "mlt": "MT",
    # Marshall Islands
    "marshall islands": "MH", "mhl": "MH",
    # Mauritania
    "mauritania": "MR", "mrt": "MR",
    # Mauritius
    "mauritius": "MU", "mus": "MU",
    # Mexico
    "mexico": "MX", "mex": "MX",
    # Micronesia
    "micronesia": "FM", "federated states of micronesia": "FM", "fsm": "FM",
    # Moldova
    "moldova": "MD", "republic of moldova": "MD", "mda": "MD",
    # Monaco
    "monaco": "MC", "mco": "MC",
    # Mongolia
    "mongolia": "MN", "mng": "MN",
    # Montenegro
    "montenegro": "ME", "mne": "ME",
    # Morocco
    "morocco": "MA", "mar": "MA",
    # Mozambique
    "mozambique": "MZ", "moz": "MZ",
    # Myanmar
    "myanmar": "MM", "burma": "MM", "mmr": "MM",
    # Namibia
    "namibia": "NA", "nam": "NA",
    # Nauru
    "nauru": "NR", "nru": "NR",
    # Nepal
    "nepal": "NP", "npl": "NP",
    # Netherlands
    "netherlands": "NL", "the netherlands": "NL", "holland": "NL", "nld": "NL",
    # New Zealand
    "new zealand": "NZ", "nzl": "NZ",
    # Nicaragua
    "nicaragua": "NI", "nic": "NI",
    # Niger
    "niger": "NE", "ner": "NE",
    # Nigeria
    "nigeria": "NG", "nga": "NG",
    # North Macedonia
    "north macedonia": "MK", "macedonia": "MK", "mkd": "MK",
    # Norway
    "norway": "NO", "nor": "NO",
    # Oman
    "oman": "OM", "omn": "OM",
    # Pakistan
    "pakistan": "PK", "pak": "PK",
    # Palau
    "palau": "PW", "plw": "PW",
    # Palestine
    "palestine": "PS", "state of palestine": "PS", "pse": "PS",
    # Panama
    "panama": "PA", "pan": "PA",
    # Papua New Guinea
    "papua new guinea": "PG", "png": "PG",
    # Paraguay
    "paraguay": "PY", "pry": "PY",
    # Peru
    "peru": "PE", "per": "PE",
    # Philippines
    "philippines": "PH", "the philippines": "PH", "phl": "PH",
    # Poland
    "poland": "PL", "pol": "PL",
    # Portugal
    "portugal": "PT", "prt": "PT",
    # Qatar
    "qatar": "QA", "qat": "QA",
    # Romania
    "romania": "RO", "rou": "RO",
    # Russia
    "russia": "RU", "russian federation": "RU", "rus": "RU",
    # Rwanda
    "rwanda": "RW", "rwa": "RW",
    # Saint Kitts and Nevis
    "saint kitts and nevis": "KN", "st kitts and nevis": "KN", "st. kitts and nevis": "KN", "kna": "KN",
    # Saint Lucia
    "saint lucia": "LC", "st lucia": "LC", "st. lucia": "LC", "lca": "LC",
    # Saint Vincent and the Grenadines
    "saint vincent and the grenadines": "VC", "st vincent and the grenadines": "VC",
    "st. vincent and the grenadines": "VC", "vct": "VC",
    # Samoa
    "samoa": "WS", "western samoa": "WS", "wsm": "WS",
    # San Marino
    "san marino": "SM", "smr": "SM",
    # Sao Tome and Principe
    "sao tome and principe": "ST", "sao tome & principe": "ST", "stp": "ST",
    # Saudi Arabia
    "saudi arabia": "SA", "sau": "SA",
    # Senegal
    "senegal": "SN", "sen": "SN",
    # Serbia
    "serbia": "RS", "srb": "RS",
    # Seychelles
    "seychelles": "SC", "syc": "SC",
    # Sierra Leone
    "sierra leone": "SL", "sle": "SL",
    # Singapore
    "singapore": "SG", "sgp": "SG",
    # Slovakia
    "slovakia": "SK", "slovak republic": "SK", "svk": "SK",
    # Slovenia
    "slovenia": "SI", "svn": "SI",
    # Solomon Islands
    "solomon islands": "SB", "slb": "SB",
    # Somalia
    "somalia": "SO", "som": "SO",
    # South Africa
    "south africa": "ZA", "zaf": "ZA",
    # South Sudan
    "south sudan": "SS", "ssd": "SS",
    # Spain
    "spain": "ES", "espana": "ES", "esp": "ES",
    # Sri Lanka
    "sri lanka": "LK", "ceylon": "LK", "lka": "LK",
    # Sudan
    "sudan": "SD", "sdn": "SD",
    # Suriname
    "suriname": "SR", "surinam": "SR", "sur": "SR",
    # Sweden
    "sweden": "SE", "swe": "SE",
    # Switzerland
    "switzerland": "CH", "che": "CH",
    # Syria
    "syria": "SY", "syrian arab republic": "SY", "syr": "SY",
    # Taiwan
    "taiwan": "TW", "twn": "TW", "republic of china": "TW",
    # Tajikistan
    "tajikistan": "TJ", "tjk": "TJ",
    # Tanzania
    "tanzania": "TZ", "united republic of tanzania": "TZ", "tza": "TZ",
    # Thailand
    "thailand": "TH", "tha": "TH", "siam": "TH",
    # Timor-Leste
    "timor-leste": "TL", "timor leste": "TL", "east timor": "TL", "tls": "TL",
    # Togo
    "togo": "TG", "tgo": "TG",
    # Tonga
    "tonga": "TO", "ton": "TO",
    # Trinidad and Tobago
    "trinidad and tobago": "TT", "trinidad & tobago": "TT", "trinidad": "TT", "tobago": "TT", "tto": "TT",
    # Tunisia
    "tunisia": "TN", "tun": "TN",
    # Turkey
    "turkey": "TR", "turkiye": "TR", "tur": "TR",
    # Turkmenistan
    "turkmenistan": "TM", "tkm": "TM",
    # Tuvalu
    "tuvalu": "TV", "tuv": "TV",
    # Uganda
    "uganda": "UG", "uga": "UG",
    # Ukraine
    "ukraine": "UA", "ukr": "UA",
    # United Arab Emirates
    "united arab emirates": "AE", "uae": "AE", "are": "AE",
    # United Kingdom
    "united kingdom": "GB", "uk": "GB", "great britain": "GB", "britain": "GB",
    "england": "GB", "scotland": "GB", "wales": "GB", "northern ireland": "GB", "gbr": "GB",
    # United States
    "united states": "US", "united states of america": "US", "usa": "US", "us": "US",
    "hawaii": "US", "alaska": "US",
    # Uruguay
    "uruguay": "UY", "ury": "UY",
    # Uzbekistan
    "uzbekistan": "UZ", "uzb": "UZ",
    # Vanuatu
    "vanuatu": "VU", "vut": "VU",
    # Vatican City
    "vatican city": "VA", "holy see": "VA", "vat": "VA",
    # Venezuela
    "venezuela": "VE", "venezuela bolivarian republic of": "VE", "ven": "VE",
    # Vietnam
    "vietnam": "VN", "viet nam": "VN", "vnm": "VN",
    # Yemen
    "yemen": "YE", "yem": "YE",
    # Zambia
    "zambia": "ZM", "zmb": "ZM",
    # Zimbabwe
    "zimbabwe": "ZW", "zwe": "ZW",
    # Territories & dependencies
    "puerto rico": "PR", "pri": "PR",
    "guam": "GU", "gum": "GU",
    "hong kong": "HK", "hkg": "HK",
    "macau": "MO", "macao": "MO", "mac": "MO",
    "reunion": "RE", "reu": "RE",
    "guadeloupe": "GP", "glp": "GP",
    "martinique": "MQ", "mtq": "MQ",
    "mayotte": "YT", "myt": "YT",
    "bermuda": "BM", "bmu": "BM",
    "greenland": "GL", "grl": "GL",
    "curacao": "CW", "cuw": "CW",
    "aruba": "AW", "abw": "AW",
    "sint maarten": "SX", "sxm": "SX",
    "new caledonia": "NC", "ncl": "NC",
    "french polynesia": "PF", "pyf": "PF",
    "isle of man": "IM", "imn": "IM",
    "jersey": "JE", "jey": "JE",
    "guernsey": "GG", "ggy": "GG",
    "gibraltar": "GI", "gib": "GI",
    "cayman islands": "KY", "cym": "KY",
    "turks and caicos islands": "TC", "tca": "TC",
    "british virgin islands": "VG", "virgin islands british": "VG", "vgb": "VG", "bvi": "VG",
    "us virgin islands": "VI", "u s virgin islands": "VI", "virgin islands u s": "VI", "vir": "VI",
    "cook islands": "CK", "cok": "CK",
    "niue": "NU", "niu": "NU",
    "faroe islands": "FO", "fro": "FO",
    "aland islands": "AX", "ala": "AX",
    "american samoa": "AS", "asm": "AS",
    "anguilla": "AI", "aia": "AI",
    "falkland islands": "FK", "flk": "FK",
    "montserrat": "MS", "msr": "MS",
    "northern mariana islands": "MP", "mnp": "MP",
    "saint helena": "SH", "shn": "SH",
    "saint pierre and miquelon": "PM", "spm": "PM",
    "wallis and futuna": "WF", "wlf": "WF",
}

# Pre-compile the normalized lookup table
COUNTRY_LOOKUP: dict[str, str] = {
    _normalize(k): v for k, v in _RAW_COUNTRY_ALIASES.items()
}


def _lookup_code(chunk: str) -> str | None:
    """Check if chunk represents a single country by 2-letter ISO or name."""
    s = chunk.strip()
    if not s:
        return None

    # Exact 2-letter uppercase ISO code
    if len(s) == 2 and s.isupper() and s in ISO_3166_1_ALPHA2:
        return s

    norm = _normalize(s)
    if not norm:
        return None

    # Check exact match in lookup
    code = COUNTRY_LOOKUP.get(norm)
    if code:
        return code

    # Check without "the " prefix
    if norm.startswith("the "):
        without_the = norm[4:].strip()
        code = COUNTRY_LOOKUP.get(without_the)
        if code:
            return code

    # Check with parentheses stripped
    no_parens = re.sub(r"\(.*?\)", "", norm).strip()
    if no_parens and no_parens != norm:
        code = COUNTRY_LOOKUP.get(no_parens)
        if code:
            return code

    # Lowercase 2-letter code if not an English stopword
    if len(s) == 2 and s.isalpha() and s.upper() in ISO_3166_1_ALPHA2:
        if s.lower() not in _STOPWORDS_2LETTER:
            return s.upper()

    return None


def parse_countries(text: str) -> set[str]:
    """Parse a distribution string into a set of uppercase ISO-3166-1 alpha-2 codes.

    Handles comma-, semicolon-, and newline-separated country names, 'and' / '&'
    separators, and gracefully ignores non-country regional descriptors
    (e.g., 'Mediterranean', 'Tropics', 'Worldwide', 'Cultivated').
    """
    if not text or not isinstance(text, str):
        return set()

    # Decode HTML entities (e.g. &amp;)
    cleaned = html.unescape(text)

    # Normalize abbreviations that use dots to prevent false sentence splitting
    cleaned = re.sub(r"\bSt\.\s*", "Saint ", cleaned)
    cleaned = re.sub(r"\bDem\.\s*Rep\.\s*", "Democratic Republic ", cleaned)
    cleaned = re.sub(r"\bRep\.\s*", "Republic ", cleaned)
    cleaned = re.sub(r"\bU\.S\.A\.\b", "USA", cleaned)
    cleaned = re.sub(r"\bU\.S\.\b", "USA", cleaned)
    cleaned = re.sub(r"\bU\.K\.\b", "UK", cleaned)

    # Replace sentence delimiters (period followed by whitespace) and section labels
    cleaned = re.sub(r"\bCountries\s*:\s*", ", ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bCountry\s*:\s*", ", ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\.\s+", ", ", cleaned)
    cleaned = re.sub(r"[\n\r\t;:|/]", ", ", cleaned)
    cleaned = cleaned.rstrip(".")

    results: set[str] = set()
    chunks = [c.strip() for c in cleaned.split(",") if c.strip()]

    for raw_chunk in chunks:
        # Strip extraneous trailing/leading punctuation (e.g. "Africa*", "'France'")
        chunk = raw_chunk.strip().rstrip("*").strip()
        # Remove leading "and " or "& "
        chunk = re.sub(r"^(?:and|&)\s+", "", chunk, flags=re.IGNORECASE).strip()
        if not chunk:
            continue

        # Try matching chunk directly as a country
        code = _lookup_code(chunk)
        if code:
            results.add(code)
            continue

        # If chunk doesn't match directly, check if it contains " and " or " & "
        if re.search(r"\s+(?:and|&)\s+", chunk, flags=re.IGNORECASE):
            parts = re.split(r"\s+(?:and|&)\s+", chunk, flags=re.IGNORECASE)
            for part in parts:
                part_clean = part.strip().rstrip("*").strip()
                part_clean = re.sub(r"^(?:and|&)\s+", "", part_clean, flags=re.IGNORECASE).strip()
                sub_code = _lookup_code(part_clean)
                if sub_code:
                    results.add(sub_code)

    return results


def normalize_distribution(text: str | None) -> tuple[str, ...]:
    """Return a sorted tuple of ISO-3166-1 alpha-2 codes for a distribution text.

    Returns () if text is empty, None, or yields no valid country codes.
    """
    if not text or not isinstance(text, str):
        return ()
    codes = parse_countries(text)
    return tuple(sorted(codes))
