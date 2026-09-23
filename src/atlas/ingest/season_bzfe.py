"""BZfE Saisonkalender ingest adapter — harvest/storage seasonality claims for 76 species.

Streams individual harvest, storage, and protected-cultivation month facts from
the Bundeszentrum für Ernährung seasonal calendar into claims for the `season` group.
Facts are cited per-claim (license_class: cite).
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import species_id

SRC_ID = "SRC-BZFE-SAISONKALENDER"


class BZfESaisonkalenderAdapter(BaseIngestAdapter):
    src_id = SRC_ID

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data:
            sci = str(row.get("sci") or "").strip()
            name_de = str(row.get("name_de") or "").strip()
            if not sci:
                continue

            subj = species_id(sci)
            ref = f"BZfE Saisonkalender, {name_de} (geprüft 2026-09-22)"

            harvest = [int(m) for m in (row.get("harvest") or [])]
            if harvest:
                yield Claim(
                    subject=subj,
                    group="season",
                    field="season:harvest:months",
                    v=json.dumps(sorted(harvest)),
                    src=self.src_id,
                    derivation="editorial",
                    ref=ref,
                    curated=True,
                )

            storage = [int(m) for m in (row.get("storage") or [])]
            if storage:
                yield Claim(
                    subject=subj,
                    group="season",
                    field="season:storage:months",
                    v=json.dumps(sorted(storage)),
                    src=self.src_id,
                    derivation="editorial",
                    ref=ref,
                    curated=True,
                )

            protected = [int(m) for m in (row.get("protected") or [])]
            if protected:
                yield Claim(
                    subject=subj,
                    group="season",
                    field="season:protected:months",
                    v=json.dumps(sorted(protected)),
                    src=self.src_id,
                    derivation="editorial",
                    ref=ref,
                    curated=True,
                )


register(BZfESaisonkalenderAdapter())
