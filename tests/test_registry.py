import textwrap

import pytest

from atlas.registry import RegistryError, load_sources

GOOD = """
SRC-A:
  title: A
  publisher: P
  url: https://example.org/a
  license: CC0-1.0
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [nutrition]
  attribution: "P. A."
"""


def write(tmp_path, text, name="sources.yaml"):
    p = tmp_path / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def test_loads_source(tmp_path):
    s = load_sources(write(tmp_path, GOOD))["SRC-A"]
    assert s.license_class == "ship" and s.supports == ("nutrition",) and s.link_status == "unchecked"


@pytest.mark.parametrize("value", ['"false"', '"true"', "1", "0", "null"])
def test_license_read_requires_boolean(tmp_path, value):
    with pytest.raises(RegistryError, match="license_read.*boolean"):
        load_sources(write(tmp_path, GOOD.replace("license_read: true", f"license_read: {value}")))


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False)])
def test_license_read_preserves_boolean(tmp_path, value, expected):
    source = load_sources(write(tmp_path, GOOD.replace("license_read: true", f"license_read: {value}")))["SRC-A"]
    assert source.license_read is expected


def test_missing_field_is_an_error(tmp_path):
    with pytest.raises(RegistryError, match="attribution"):
        load_sources(write(tmp_path, GOOD.replace('  attribution: "P. A."\n', "")))


def test_unknown_license_class(tmp_path):
    with pytest.raises(RegistryError, match="license_class"):
        load_sources(write(tmp_path, GOOD.replace("class: ship", "class: maybe")))


def test_unknown_claim_group(tmp_path):
    with pytest.raises(RegistryError, match="claim groups"):
        load_sources(write(tmp_path, GOOD.replace("[nutrition]", "[vibes]")))


def test_link_status_is_merged(tmp_path):
    status = write(tmp_path, "SRC-A: {status: broken, checked: 2026-09-17}\n", "link_status.yaml")
    assert load_sources(write(tmp_path, GOOD), status)["SRC-A"].link_status == "broken"
