"""Streaming BioFoodComp 4.0 adapter: yields nutrition claims from the FAO
INFOODS Food Biodiversity Database (BioFoodComp), Version 4.0."""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from openpyxl import load_workbook

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register


SKIP_SHEETS = frozenset({
    "Copyright",
    "Codes",
    "Components",
    "Bibliography",
    "09 Fish & Shellfish_Fatty acids",
})

# BioFoodComp type codes → cultivated flag
TYPE_CULTIVATED = frozenset({"C", "V", "BC", "B"})  # Cultivar, Variety, Breeding Clone, Breed
TYPE_WILD = frozenset({"W", "U"})  # Wild, Underutilized

# Mapping of origin/compiler codes to derivation labels
# BioFoodComp is a literature compilation → 'literature'
DERIVATION = "literature"

# Per-100gFA nutrient columns in sheet 09 Fish & Shellfish — skip these
# (they express nutrients per 100g fatty acids, not per 100g food)
FATTY_ACID_TAGS = frozenset({
    "FAT", "FASAT", "FAMU", "FAPU", "FAT18:3", "FAT18:2", "FAT18:1",
    "FAT16:0", "FAT14:0", "FAT12:0", "FAT8:0", "FAT6:0", "FAT4:0",
    "FAT20:4", "FAT20:5", "FAT22:5", "FAT22:6", "FAT16:1", "FAT17:0",
    "FAT15:0", "FAT13:0", "FAT11:0", "FAT9:0", "FAT7:0", "FAT5:0",
    "FAT10:0", "FAT24:0", "FAT24:1", "FAT22:4", "FAT20:3", "FAT18:4",
})

# Trace value markers
TRACE_VALUES = frozenset({"tr", "Tr", "TR"})

# Not-detectable / no-measurable-value marker
NO_VALUE_MARKER = "N"

# Unit extraction from header: e.g. "ENERC(kJ) (original)" → tag="ENERC", unit="kJ"
_UNIT_RE = re.compile(r"\(([^)]+)\)")


def _parse_nutrient_header(header: str) -> tuple[str, str | None]:
    """Extract tag and unit from a BioFoodComp nutrient column header.

    'ENERC(kJ) (original)' → ('ENERC(kJ)', 'kJ')
    'WATER(g)' → ('WATER(g)', 'g')
    'EDIBLE' → ('EDIBLE', None)
    """
    header = str(header).strip()
    if not header:
        return "", None

    # Extract unit from first parenthetical group
    match = _UNIT_RE.search(header)
    unit = match.group(1) if match else None

    # Tag is the component ID including unit in parentheses if present,
    # but without trailing qualifiers like " (original)"
    if match:
        # "ENERC(kJ) (original)" → tag = "ENERC(kJ)"
        tag = header[:match.end()].strip()
    else:
        # No unit in parentheses — use first word
        tag = header.split()[0].strip()

    return tag, unit


def _strip_brackets(value: str) -> str:
    """Remove surrounding brackets from a value string.

    '[418.94]' → '418.94'
    """
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        return v[1:-1].strip()
    return v


def _parse_value(value: object) -> tuple[object, str | None]:
    """Parse a BioFoodComp nutrient cell value.

    Returns (parsed_value, derivation_override) or (None, None) to skip.
    - 'tr'/'Tr'/'TR' → ('tr', 'trace')
    - 'N' → skip (None, None)
    - Bracketed numeric → float
    - Numeric → float
    - Other string → string (let contract decide)
    """
    if value is None:
        return None, None

    s = str(value).strip()
    if s == "" or s == "-":
        return None, None

    # Trace marker
    if s in TRACE_VALUES:
        return "tr", "trace"

    # Not detectable / no measurable value — skip
    if s == NO_VALUE_MARKER:
        return None, None

    # Bracketed numeric value (converted from DM to FW basis)
    stripped = _strip_brackets(s)
    try:
        return float(stripped), DERIVATION
    except ValueError:
        pass

    # Try parsing as float directly
    try:
        return float(s), DERIVATION
    except ValueError:
        pass

    # Non-numeric string — yield honestly, let contract decide
    return s, DERIVATION


def _is_data_row(row: list[object]) -> bool:
    """A row is a real data row if it has a non-empty Food Item ID in col 0."""
    return len(row) > 0 and row[0] is not None and str(row[0]).strip() != ""


def _is_blank_or_placeholder(row: list[object]) -> bool:
    """Skip fully blank rows and placeholder rows like 'to be completed'."""
    if not row:
        return True
    first = str(row[0]).strip() if row[0] is not None else ""
    if first == "" or first.lower() in ("to be completed", ""):
        return True
    return False


def _sheet_has_nutrient_columns(headers: list[str]) -> bool:
    """Check if a sheet has nutrient columns (beyond the metadata columns)."""
    # Standard sheets have nutrient columns starting from col 18 (index 17)
    # Sheet 09 Fish & Shellfish has them starting from col 18 (index 17) too
    for i, h in enumerate(headers):
        if i >= 17 and h is not None and str(h).strip():
            return True
    return False


def _get_nutrient_columns(headers: list[str]) -> list[tuple[int, str, str | None]]:
    """Return list of (column_index, tag, unit) for nutrient columns.

    Detects nutrient columns by matching headers against known nutrient
    tag patterns: short uppercase codes (DEN, EDIBLE, PH, XN) or codes
    with units in parentheses (ENERC(kJ), WATER(g), etc.).
    Metadata columns like 'Publication year' or 'BiblioID' are skipped.
    """
    result = []
    for i, h in enumerate(headers):
        if h is None or str(h).strip() == "":
            continue
        header = str(h).strip()
        tag, unit = _parse_nutrient_header(header)
        if not tag or tag in FATTY_ACID_TAGS:
            continue
        # Skip metadata columns: they have lowercase words or are
        # descriptive strings without unit abbreviations in parens
        # and without being known nutrient short codes.
        # Known nutrient short codes (no unit in parens):
        _SHORT_NUTRIENT_CODES = frozenset({
            "DEN", "EDIBLE", "PH", "XN", "NT", "NNP", "PROTPL", "PROTAN",
            "PROTCNT", "PROTCNP", "PROT-", "FAT", "FATCE", "FAT-",
            "FASAT", "FAMS", "FAPU", "FAUN", "FATRN",
            "CHOAVLDF", "CHOAVL", "CHOCDF", "CHOAVLM", "CHO-",
            "AMYS", "SUGAR", "SUGARM", "SUGRD", "SUGNRD", "SUGAR-",
            "STARCH", "STARCHM", "STARCH-", "STARES",
            "FIBTG", "FIBTS", "NSP", "FIBC", "FIB-", "FIBINS", "FIBSOL",
            "FIBND", "FIBAD", "LIGN", "ALC", "ASH",
            "BRD", "CA", "CO", "CU", "FE", "K", "MN", "MG", "NA", "P",
            "SE", "ZN", "AL", "AS", "B", "CD", "CLD", "CR", "HG", "ID",
            "LI", "NI", "PB", "RB", "S", "SB", "V", "VITA_RAE", "VITA",
            "RETOL", "CARTBEQ", "CARTA", "CARTB", "CRYPX", "CRYPXB",
            "CARTG", "LYCPN", "NEUROSP", "PHYTOENE", "PHYTOFLUENCE",
            "LUTN", "LUTNZEA", "CARTOID", "VITD", "VITDEQ", "ERGCAL",
            "CHOCAL", "CHOCALOH", "VITD-", "VITEA", "VITE", "VITE-",
            "TOCPHA", "TOCPHB", "TOCPHG", "TOCPHD", "TOCPHT", "VITK",
            "THIA", "RIBF", "NIAEQ", "NIA", "NIATRP", "NIA-",
            "PANTAC", "VITB6A", "VITB6C", "VITB6-",
            "FOLSUM", "FOL", "FOLAC", "FOLFD", "DFE", "FOLFRE", "BIOT",
            "VITB12", "ASCL", "VITC", "FRUS", "GLUS", "XYLS", "MALS",
            "GALS", "SUCS", "RAFS", "RAFSM", "RIBS", "STASM", "CELLU",
            "FACID", "F12D0", "F13D0", "F14D0", "F15D0", "F16D0",
            "F17D0", "F18D0", "F20D0", "F21D0", "F22D0", "F24D0",
            "F16D1", "F18D1", "F20D1", "F22D1", "F24D1", "F16D2",
            "F18D2", "F20D2", "F22D2", "F18D3", "F20D4", "WAX", "FAFRE",
            "MGLY", "DGLY", "TGLY", "PHOAC", "PHOSER", "PHOETHN",
            "PHOINOTL", "CHLNP", "ALA", "ARG", "ASN", "ASP", "CYS",
            "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS", "MET",
            "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
            "PHE_A_TYR", "AAE-", "AAA", "AMMON", "BENAC", "PHYTCPPI",
            "PHYTCPPD", "PHYTCPP", "PHYTC-", "PPI", "PPD", "PP-",
            "XP", "IP3", "IP4", "IP5", "IP6", "IP5_A_IP6",
            "IP4_A_IP5_A_IP6", "IPSUM", "PHYT-", "CAFFAC", "FERAC",
            "FLAVD", "FLAVO", "MYRIC", "KAEMF", "PCHOUAC", "QUERCE",
            "VANAC", "SAPON", "SI", "GABA", "TAN", "OXALAC", "CYAN",
        })
        if unit is not None or tag in _SHORT_NUTRIENT_CODES:
            result.append((i, tag, unit))
    return result


def _extract_ref(row: list[object]) -> str:
    """Construct a reference string from Biblioid, Compiler ID, and year."""
    parts = []
    biblioid = row[14] if len(row) > 14 else None
    compiler = row[15] if len(row) > 15 else None
    year = row[13] if len(row) > 13 else None
    if biblioid is not None and str(biblioid).strip():
        parts.append(f"bfc:{biblioid}")
    if compiler is not None and str(compiler).strip():
        parts.append(f"compiler:{compiler}")
    if year is not None and str(year).strip():
        parts.append(f"year:{year}")
    return "; ".join(parts) if parts else ""


def _extract_sci_name(row: list[object]) -> str:
    """Extract scientific name from col 7."""
    if len(row) > 7 and row[7] is not None:
        return str(row[7]).strip()
    return ""


def _extract_variety(row: list[object]) -> str:
    """Extract variety/cultivar name from col 8."""
    if len(row) > 8 and row[8] is not None:
        return str(row[8]).strip()
    return ""


def _extract_cultivated_flag(row: list[object]) -> str:
    """Extract C/U type flag from col 3."""
    if len(row) > 3 and row[3] is not None:
        return str(row[3]).strip()
    return ""


def _extract_food_name(row: list[object]) -> str:
    """Extract English food name from col 5, falling back to col 4."""
    if len(row) > 5 and row[5] is not None and str(row[5]).strip():
        return str(row[5]).strip()
    if len(row) > 4 and row[4] is not None:
        return str(row[4]).strip()
    return ""


def _extract_processing(row: list[object]) -> str:
    """Extract processing code from col 6."""
    if len(row) > 6 and row[6] is not None:
        return str(row[6]).strip()
    return ""


def _extract_food_id(row: list[object]) -> str:
    """Extract Food Item ID from col 0."""
    if len(row) > 0 and row[0] is not None:
        return str(row[0]).strip()
    return ""


def _is_fatty_acid_sheet(sheet_name: str) -> bool:
    """Check if a sheet is the per-100gFA fatty-acid sheet to skip."""
    return sheet_name == "09 Fish & Shellfish_Fatty acids"


def _is_category_sheet(sheet_name: str) -> bool:
    """Check if a sheet is one of the 12 category sheets."""
    return sheet_name.startswith(("01 ", "02 ", "03 ", "04 ", "05 ", "06 ",
                                   "07 ", "08 ", "09 ", "10_", "11 ", "12 "))


def _is_fish_shellfish_sheet(sheet_name: str) -> bool:
    """Check if a sheet is the fish & shellfish sheet (different column layout)."""
    return sheet_name == "09 Fish & Shellfish"


def _iter_sheet_rows(ws) -> Iterator[list[object]]:
    """Iterate over rows in a sheet using read_only mode."""
    for row in ws.iter_rows(values_only=True):
        yield list(row)


def _ingest_sheet(ws, sheet_name: str) -> Iterator[Claim]:
    """Ingest a single BioFoodComp category sheet, yielding claims."""
    rows = list(_iter_sheet_rows(ws))
    if not rows:
        return

    # Find header row (first non-empty row)
    header_idx = 0
    for i, row in enumerate(rows):
        if row and any(c is not None and str(c).strip() for c in row):
            header_idx = i
            break

    headers = [str(c).strip() if c is not None else "" for c in rows[header_idx]]

    # Detect nutrient columns by matching headers against known nutrient tag patterns
    nutrient_cols = _get_nutrient_columns(headers)

    if not nutrient_cols:
        return

    # Data rows start after header + 2 description/abbreviation rows
    # But we must be flexible — skip blank/placeholder rows
    for row in rows[header_idx + 1:]:
        if _is_blank_or_placeholder(row):
            continue
        if not _is_data_row(row):
            continue

        food_id = _extract_food_id(row)
        if not food_id:
            continue

        sci_name = _extract_sci_name(row)
        variety = _extract_variety(row)
        cultivated_flag = _extract_cultivated_flag(row)
        food_name = _extract_food_name(row)
        processing = _extract_processing(row)
        ref = _extract_ref(row)

        # Add scientific name and variety to ref for identity traceability
        ref_parts = [ref]
        if sci_name:
            ref_parts.append(f"sci:{sci_name}")
        if variety:
            ref_parts.append(f"variety:{variety}")
        full_ref = "; ".join(ref_parts)

        for col_idx, tag, unit in nutrient_cols:
            raw_value = row[col_idx] if col_idx < len(row) else None
            parsed_value, derivation_override = _parse_value(raw_value)
            if parsed_value is None:
                continue

            claim_derivation = derivation_override if derivation_override else DERIVATION
            field = f"nutrient:bfc:{tag}"

            claim = Claim(
                subject=f"prod:bfc:{food_id}",
                group="nutrition",
                field=field,
                v=parsed_value,
                src="SRC-BFOODCOMP-4.0",
                derivation=claim_derivation,
                unit=unit,
                basis="as_described",
                food_part="product",
                ref=full_ref if full_ref else None,
                method=None,
            )
            yield claim


class BioFoodCompAdapter(BaseIngestAdapter):
    """Streaming BioFoodComp 4.0 adapter: yields product claims from the Excel workbook."""

    src_id = "SRC-BFOODCOMP-4.0"

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        """Stream claims from all category sheets of the BioFoodComp 4.0 workbook."""
        xlsx_hits = sorted(path.rglob("*.xlsx"))
        if not xlsx_hits:
            return
        wb = load_workbook(xlsx_hits[0], read_only=True, data_only=True)
        try:
            for sheet_name in wb.sheetnames:
                if sheet_name in SKIP_SHEETS:
                    continue
                if _is_fatty_acid_sheet(sheet_name):
                    continue
                if not _is_category_sheet(sheet_name):
                    continue

                ws = wb[sheet_name]
                yield from _ingest_sheet(ws, sheet_name)
        finally:
            wb.close()


register(BioFoodCompAdapter())
