"""Ciqual 2025 XML streaming adapter: yields nutrition claims from ANSES data."""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from xml.etree.ElementTree import iterparse

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register


def _parse_unit_from_name(name: str) -> str:
    """Extract unit from Ciqual CONST name, e.g. 'Eau (g/100 g)' → 'g/100g'."""
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        return m.group(1).replace(" ", "")
    return ""


def _strip_text(text: str | None) -> str:
    return (text or "").strip()


class CiqualAdapter(BaseIngestAdapter):
    """Streaming Ciqual 2025 adapter: parses ALIM/CONST/SRC into memory,
    streams COMPO row by row so the 69 MB compo file is never fully loaded."""

    src_id = "SRC-CIQUAL-2025"

    def __init__(self, src_id: str = "SRC-CIQUAL-2025", prefix: str = "prod:ciq") -> None:
        self.src_id = src_id
        self.prefix = prefix

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        # --- Phase 1: load small lookup tables into memory ---
        alim_dir = self._find_alim_dir(root, path)

        foods: dict[str, dict[str, str]] = {}
        for ev, el in iterparse(alim_dir / "alim_2025_11_03.xml", events=("end",)):
            if el.tag == "ALIM":
                code = _strip_text(el.findtext("alim_code"))
                nom_sci_el = el.find("alim_nom_sci")
                nom_sci = ""
                if nom_sci_el is not None and nom_sci_el.get("missing") is None:
                    nom_sci = _strip_text(nom_sci_el.text)
                foods[code] = {
                    "nom_fr": _strip_text(el.findtext("alim_nom_fr")),
                    "nom_eng": _strip_text(el.findtext("alim_nom_eng")),
                    "nom_sci": nom_sci,
                    "grp_code": _strip_text(el.findtext("alim_grp_code")),
                }
                el.clear()

        consts: dict[str, dict[str, str]] = {}
        for ev, el in iterparse(alim_dir / "const_2025_11_03.xml", events=("end",)):
            if el.tag == "CONST":
                code = _strip_text(el.findtext("const_code"))
                consts[code] = {
                    "nom_fr": _strip_text(el.findtext("const_nom_fr")),
                    "nom_eng": _strip_text(el.findtext("const_nom_eng")),
                    "code_infooods": _strip_text(el.findtext("code_INFOODS")),
                    "unit": _parse_unit_from_name(
                        el.findtext("const_nom_fr") or ""
                    ),
                }
                el.clear()

        sources: dict[str, str] = {}
        for ev, el in iterparse(alim_dir / "sources_2025_11_03.xml", events=("end",)):
            if el.tag == "SOURCES":
                code = _strip_text(el.findtext("source_code"))
                citation = el.findtext("ref_citation")
                sources[code] = _strip_text(citation) if citation else ""
                el.clear()

        # --- Phase 2: stream COMPO, yield claims ---
        for ev, el in iterparse(alim_dir / "compo_2025_11_03.xml", events=("end",)):
            if el.tag == "COMPO":
                alim_code = _strip_text(el.findtext("alim_code"))
                const_code = _strip_text(el.findtext("const_code"))
                teneur_raw = _strip_text(el.findtext("teneur"))

                # Skip empty, missing, or non-numeric teneur values
                if not teneur_raw or teneur_raw == "-":
                    el.clear()
                    continue
                try:
                    teneur_val = float(teneur_raw.replace(",", "."))
                except ValueError:
                    # Non-numeric values like "traces" — skip honestly
                    el.clear()
                    continue

                const = consts.get(const_code)
                if const is None:
                    el.clear()
                    continue

                subject = f"{self.prefix}:{alim_code}"
                field = f"nutrient:ciqual:{const_code}"
                unit = const["unit"]
                ref = f"ciqual:{alim_code}:{const_code}"

                # Build flags from confidence code
                conf = _strip_text(el.findtext("code_confiance"))
                flags: tuple[str, ...] = ()
                if conf:
                    flags = (f"confidence:{conf}",)

                claim = Claim(
                    subject=subject,
                    group="nutrition",
                    field=field,
                    v=teneur_val,
                    src=self.src_id,
                    derivation="registry",
                    unit=unit,
                    basis="as_described",
                    food_part="product",
                    ref=ref,
                    flags=flags,
                )
                yield claim

                el.clear()

    def _find_alim_dir(self, root: Path, path: Path) -> Path:
        """Find the Ciqual directory containing the XML files."""
        candidates = [path]
        if path == root:
            candidates.append(root / "data" / "raw" / "ciqual-2025")
        for cand in candidates:
            if (cand / "alim_2025_11_03.xml").exists():
                return cand
        raise FileNotFoundError(
            f"Could not find Ciqual XML files under {path}"
        )


register(CiqualAdapter())