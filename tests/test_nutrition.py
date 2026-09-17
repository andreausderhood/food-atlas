"""Synthetic test-only claims; no fixture values are shipped to the site."""
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess

from jinja2 import Environment, PackageLoader
import pytest

from atlas.site.nutrition import nutrition_profile


def claim(nutrient=1003, value=0.3, unit="g", **kwargs):
    return dict(group="nutrition", field=f"nutrient:fdc:{nutrient}", v=value,
                unit=unit, src="TEST-FDC", ref="fdc:100", basis="fresh_weight",
                food_part="whole", tier=1, derivation="analytical", method="Test only",
                flags=[]) | kwargs


def profile(*claims):
    return nutrition_profile({"id": "food:test", "name": "Test only", "claims": list(claims)})


def render(data):
    env = Environment(loader=PackageLoader("atlas.site", "templates"), autoescape=True)
    return env.get_template("_nutrition.html.j2").render(nutrition=data, sources={})


def tiles(record):
    return {t["field"]: t for bucket in ("macronutrients", "minerals", "vitamins", "other")
            for t in record[bucket]}


def test_record_isolation_including_basis_and_part():
    result = profile(claim(), claim(1162, 4.6, "mg", ref="fdc:101"),
                     claim(1079, 2.4, src="TEST-OTHER"),
                     claim(1004, 0.1, food_part="flesh"),
                     claim(1005, 13.8, basis="as_sold"))
    assert len(result["records"]) == 5
    for record in result["records"]:
        available = [t for t in tiles(record).values() if t["value"] is not None]
        assert len(available) == 1
        assert all((c["src"], c["ref"], c["basis"], c["food_part"]) ==
                   (record["src"], record["ref"], record["basis"], record["food_part"])
                   for t in available for c in t["claims"])


def test_zero_and_missing_are_not_conflated():
    result = tiles(profile(claim(value=0))["records"][0])
    assert result["nutrient:fdc:1003"]["value"] == 0
    assert result["nutrient:fdc:1003"]["display"] == "0 g"
    assert result["nutrient:fdc:1004"]["value"] is None
    assert result["nutrient:fdc:1004"]["display"] == "Not reported"


def test_fdc_sugar_definitions_are_separate_not_fallbacks_or_sums():
    result = tiles(profile(claim(2000, 10.4), claim(1063, 9.1), claim(1079, 2.4),
                           claim(1005, 13.8), claim(1050, 13.2))["records"][0])
    assert result["nutrient:fdc:2000"]["value"] == 10.4
    assert result["nutrient:fdc:1063"]["value"] == 9.1
    assert result["nutrient:fdc:1005"]["value"] == 13.8
    assert result["nutrient:fdc:1050"]["value"] == 13.2
    assert "by difference" in result["nutrient:fdc:1005"]["label"]
    assert result["nutrient:fdc:2000"]["label"] != result["nutrient:fdc:1063"]["label"]


@pytest.mark.parametrize("changes", [
    {"v": "present"}, {"v": True}, {"v": None}, {"v": -1}, {"v": float("nan")},
    {"v": float("inf")}, {"unit": "mg"}, {"ref": None}, {"ref": "bls:100"},
    {"src": None}, {"basis": None}, {"food_part": None}, {"group": "molecules"},
    {"field": "sugars100"}, {"flags": ["llm_extracted"]},
    {"flags": ["machine_extracted"]}, {"derivation": "extracted"},
])
def test_unsupported_or_non_quantitative_claims_do_not_create_records(changes):
    assert profile(claim(**changes))["records"] == []


def test_unverified_source_derivation_is_retained_honestly():
    data = profile(claim(tier=5, derivation="unverified", flags=["missing_derivation"]))
    tile = tiles(data["records"][0])["nutrient:fdc:1003"]
    assert tile["claims"][0]["tier"] == 5
    assert tile["claims"][0]["flags"] == ["missing_derivation"]


def test_micro_units_are_numeric_not_percentage_and_precision_is_retained():
    result = profile(claim(1162, 4.6, "mg"), claim(1103, 0, "ug"), claim(1089, 0.00012, "mg"))
    record = result["records"][0]
    assert tiles(record)["nutrient:fdc:1103"]["display"] == "0 µg"
    assert tiles(record)["nutrient:fdc:1089"]["value"] == 0.00012
    assert tiles(record)["nutrient:fdc:1162"]["label"] == "Vitamin C, total ascorbic acid"
    assert all(t["bar_value"] is None for t in record["minerals"] + record["vitamins"])
    assert "daily_value" not in json.dumps(result)


def test_bar_overflow_not_silently_clamped():
    tile = tiles(profile(claim(value=101))["records"][0])["nutrient:fdc:1003"]
    assert tile["value"] == 101
    assert tile["bar_value"] is None
    assert "outside" in tile["note"].lower()


def test_conflicting_duplicates_not_overwritten_or_averaged():
    tile = tiles(profile(claim(value=1), claim(value=2))["records"][0])["nutrient:fdc:1003"]
    assert tile["value"] is None
    assert tile["display"] == "Conflicting values"
    assert [c["v"] for c in tile["claims"]] == [1, 2]


def test_energy_definitions_stay_separate():
    result = tiles(profile(claim(1008, 52, "kcal"), claim(2047, 50, "kcal"),
                           claim(2048, 49, "kcal"))["records"][0])
    assert [result[f"nutrient:fdc:{i}"]["value"] for i in (1008, 2047, 2048)] == [52, 50, 49]


def test_science_metadata_and_safe_html_json_render():
    evil = '</script><img src=x onerror="alert(1)">'
    data = profile(claim(src=evil, method=evil, v_min=0, v_max=0.7, n=8))
    html = render(data)
    assert evil not in html
    assert "\\u003c/script\\u003e" in html
    assert "&lt;/script&gt;" in html
    assert "<details" in html and "<summary" in html
    for text in ("Tier", "Reference", "Unit", "Basis", "Part", "fresh_weight", "fdc:100", "analytical"):
        assert text in html
    assert 'role="meter"' in html
    assert 'aria-valuemin="0"' in html and 'aria-valuemax="100"' in html
    assert 'aria-valuenow="0.3"' in html
    assert "0–100 g" in html and "per 100 g" in html
    assert "do not sum" in html and "presence" in html
    assert "innerHTML" not in html and "textContent" in html


def test_no_claims_empty_state():
    html = render(profile())
    assert "No supported FDC quantity record" in html
    assert 'role="meter"' not in html
    assert "Not reported" not in html  # no fabricated empty food record


def test_progressive_enhancement_and_selector_runtime():
    """Execute the actual template JS with a minimal DOM; no browser dependency."""
    if not shutil.which("node"):
        pytest.skip("Node is not installed")
    data = profile(claim(), claim(value=0.8, ref="fdc:101"))
    html = render(data)
    assert 'data-nutrition-controls hidden' in html
    assert not re.search(r'<article[^>]*data-nutrition-record[^>]*\bhidden\b', html)
    scripts = re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S)
    code = next(body for attrs, body in scripts if 'application/json' not in attrs)
    labels = json.loads(next(body for attrs, body in scripts if 'application/json' in attrs))
    harness = '''
const assert = require('node:assert/strict');
const panels = [{hidden:false}, {hidden:false}];
let listener;
const select = {value:'0', addEventListener:(event, fn)=>{assert.equal(event,'change');listener=fn;}};
const controls = {hidden:true};
const status = {textContent:''};
const data = {textContent:JSON.stringify(LABELS)};
const root = {querySelector:s=>({'[data-nutrition-select]':select,'[data-nutrition-controls]':controls,
 '[data-nutrition-status]':status,'[data-nutrition-labels]':data}[s]),
 querySelectorAll:()=>panels};
global.document = {currentScript:{closest:()=>root}};
CODE
assert.equal(controls.hidden,false);
assert.deepEqual(panels.map(p=>p.hidden),[false,true]);
select.value='1'; listener();
assert.deepEqual(panels.map(p=>p.hidden),[true,false]);
assert.ok(status.textContent.includes('fdc:101'));
select.value='bad'; listener();
assert.deepEqual(panels.map(p=>p.hidden),[true,false]);
console.log('selector change and invalid selection verified');
'''.replace("LABELS", json.dumps(labels)).replace("CODE", code)
    run = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert "verified" in run.stdout


@pytest.mark.data
def test_labels_and_units_against_downloaded_fdc_dictionary():
    from atlas.site.nutrition import NUTRIENTS
    paths = list((Path(__file__).resolve().parents[1] / "data/raw/fdc-foundation").glob("*/nutrient.csv"))
    if not paths:
        pytest.skip("Local USDA nutrient.csv is not present; no download performed")
    with paths[0].open(newline="", encoding="utf-8") as stream:
        raw = {f"nutrient:fdc:{row['id']}": row for row in csv.DictReader(stream)}
    for field, spec in NUTRIENTS.items():
        assert spec["label"] == raw[field]["name"]
        assert spec["unit"] == raw[field]["unit_name"].lower()
