"""Tests for USDA Pomological Watercolors streaming ingest adapter (Task 32)."""
from __future__ import annotations

import io
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.contract import check
from atlas.ingest.base import get_adapter, registered
from atlas.ingest.pomological import PomologicalAdapter, parse_pomological_fruit
from atlas.registry import load_sources


SAMPLE_CSV = """\
,authors,fruit,image,painting_index,subjects,thumbnail_image,year
0,"Schutt, Ellen Isham, 1873-1955
",Acca sellowiana,https://naldc.nal.usda.gov/download/POM00007435/screen,1,"Acca sellowiana , Acca",https://naldc.nal.usda.gov/download/POM00007435/thumbnail,1909
0,"Newton, Amanda Almira, ca. 1860-1943
",Malus domestica: Abernathy,https://naldc.nal.usda.gov/download/POM00000042/screen,42,"Malus domestica , apples",https://naldc.nal.usda.gov/download/POM00000042/thumbnail,1912
0,"Steadman, Royal Charles, b. 1875
",Prunus avium: Abbess d' Oignies,https://naldc.nal.usda.gov/download/POM00000100/screen,100,"Prunus avium , sweet cherry",https://naldc.nal.usda.gov/download/POM00000100/thumbnail,1915
"""


def test_parse_pomological_fruit():
    taxon, cultivar = parse_pomological_fruit("Acca sellowiana")
    assert taxon == "Acca sellowiana"
    assert cultivar is None

    taxon, cultivar = parse_pomological_fruit("Malus domestica: Abernathy")
    assert taxon == "Malus domestica"
    assert cultivar == "Abernathy"

    taxon, cultivar = parse_pomological_fruit("Prunus avium: Abbess d' Oignies")
    assert taxon == "Prunus avium"
    assert cultivar == "Abbess d' Oignies"

    taxon, cultivar = parse_pomological_fruit("Carya: Delmas")
    assert taxon == "Carya"
    assert cultivar == "Delmas"


def test_adapter_registered():
    assert "SRC-USDA-POMOLOGICAL" in registered()
    adapter = get_adapter("SRC-USDA-POMOLOGICAL")
    assert isinstance(adapter, PomologicalAdapter)
    assert adapter.src_id == "SRC-USDA-POMOLOGICAL"


def test_iter_claims_sample(tmp_path: Path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(SAMPLE_CSV, encoding="utf-8")

    adapter = PomologicalAdapter()
    claims = list(adapter.load(Path("."), csv_file))

    assert len(claims) > 0
    # Acca sellowiana should have photo claims
    acca_claims = [c for c in claims if "acca-sellowiana" in c.subject]
    assert any(c.field == "photo:url" and "POM00007435/screen" in str(c.v) for c in acca_claims)
    assert any(c.field == "photo:thumb_url" for c in acca_claims)
    assert any(c.field == "photo:artist" and "Schutt" in str(c.v) for c in acca_claims)
    assert any(c.field == "photo:year" and c.v == "1909" for c in acca_claims)

    # Malus domestica should have photo claims AND cultivar variety claim
    malus_claims = [c for c in claims if "malus-domestica" in c.subject]
    assert any(c.group == "photos" for c in malus_claims)
    cultivar_claims = [c for c in malus_claims if c.group == "varieties"]
    assert len(cultivar_claims) == 1
    assert cultivar_claims[0].field == "cultivar:name"
    assert cultivar_claims[0].v == "Abernathy"


def test_claims_satisfy_contract(tmp_path: Path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(SAMPLE_CSV, encoding="utf-8")

    sources = load_sources(Path("data/registry/sources.yaml"))
    adapter = PomologicalAdapter()

    for claim in adapter.load(Path("."), csv_file):
        gap = check(claim, sources)
        assert gap.ok, f"Claim violated contract: {gap} for claim {claim}"
