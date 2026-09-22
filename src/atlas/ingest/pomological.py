"""USDA Pomological Watercolors Collection streaming ingest adapter.

Streams authentic botanical and pomological watercolors from 1886-1942 into
claims for photos (photo:url, photo:thumb_url, photo:artist, photo:year)
and varieties (cultivar:name).
"""
from __future__ import annotations

import csv
import re
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import species_id

SRC_ID = "SRC-USDA-POMOLOGICAL"


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_pomological_fruit(fruit_text: str) -> tuple[str, str | None]:
    """Parse 'Taxon: Cultivar' or 'Taxon' from pomological fruit string."""
    clean = fruit_text.strip()
    if ":" in clean:
        parts = clean.split(":", 1)
        taxon = parts[0].strip()
        cultivar = parts[1].strip() or None
        return taxon, cultivar
    return clean, None


class PomologicalAdapter(BaseIngestAdapter):
    src_id = SRC_ID

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        if path.is_dir():
            csv_path = path / "usda_pomological_watercolors.csv"
            if not csv_path.is_file():
                candidates = sorted(path.rglob("*.csv"))
                if not candidates:
                    raise FileNotFoundError(f"no csv file in {path}")
                csv_path = candidates[0]
        else:
            csv_path = path

        with csv_path.open(encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fruit_raw = str(row.get("fruit") or "").strip()
                if not fruit_raw:
                    continue

                painting_index = str(row.get("painting_index") or "").strip()
                taxon, cultivar = parse_pomological_fruit(fruit_raw)
                if not taxon:
                    continue

                subj = species_id(taxon)
                author = " ".join((row.get("authors") or "").split())
                year = " ".join((row.get("year") or "").split())
                image = str(row.get("image") or "").strip()
                thumb = str(row.get("thumbnail_image") or "").strip()

                ref_parts = [f"USDA Pomological Watercolor #{painting_index}"]
                if year:
                    ref_parts.append(f"({year})")
                if author:
                    ref_parts.append(f"Artist: {author}")
                ref = ", ".join(ref_parts)

                # Photo claims
                if image:
                    yield Claim(
                        subject=subj,
                        group="photos",
                        field="photo:url",
                        v=image,
                        src=self.src_id,
                        derivation="registry",
                        ref=ref,
                    )
                if thumb:
                    yield Claim(
                        subject=subj,
                        group="photos",
                        field="photo:thumb_url",
                        v=thumb,
                        src=self.src_id,
                        derivation="registry",
                        ref=ref,
                    )
                if author:
                    yield Claim(
                        subject=subj,
                        group="photos",
                        field="photo:artist",
                        v=author,
                        src=self.src_id,
                        derivation="registry",
                        ref=ref,
                    )
                if year:
                    yield Claim(
                        subject=subj,
                        group="photos",
                        field="photo:year",
                        v=year,
                        src=self.src_id,
                        derivation="registry",
                        ref=ref,
                    )

                # Varieties claim
                if cultivar:
                    yield Claim(
                        subject=subj,
                        group="varieties",
                        field="cultivar:name",
                        v=cultivar,
                        src=self.src_id,
                        derivation="registry",
                        ref=ref,
                    )


register(PomologicalAdapter())
