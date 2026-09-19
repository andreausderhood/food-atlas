"""Interview UX contracts; synthetic evidence stays inside tests."""
import json
import subprocess
from pathlib import Path

from test_site import payload


def test_seasons_require_explicit_region_kind_and_valid_months():
    from atlas.site.profiles import season_records
    claims = [dict(group="season", field="season:CH:fresh", v=[8, 9, 10], src="TEST"),
              dict(group="season", field="season:CH:stored", v=[1, 2], src="TEST"),
              dict(group="season", field="season:DE", v="summer", src="TEST"),
              dict(group="season", field="season:CH:fresh", v=[0, 13], src="TEST")]
    assert season_records(claims) == [
        dict(region="CH", kind="fresh", months=[8, 9, 10], src="TEST"),
        dict(region="CH", kind="stored", months=[1, 2], src="TEST")]
    assert season_records([]) == []


def test_research_kind_not_inferred_from_tier_or_molecule_presence():
    from atlas.site.profiles import research_profile
    claims = [dict(group="molecules", field="contains:q", tier=3),
              dict(group="bioactivity", field="antifungal", tier=1, method=None),
              dict(group="bioactivity", field="antifungal", tier=3, method="in_vitro:assay"),
              dict(group="bioactivity", field="antifungal", tier=4, method="tradition:TCM"),
              dict(group="bioactivity", field="antifungal", tier=3, method="human:trial"),
              dict(group="bioactivity", field="antifungal", tier=4, method="model:test@1")]
    groups = research_profile(claims)
    assert {g['label']: len(g['claims']) for g in groups} == {
        'Human studies': 1, 'Laboratory studies': 1, 'Traditional use': 1,
        'Predictions': 1, 'Evidence not classified': 1}
    assert research_profile([claims[0]]) == []


def test_profiles_integrated_and_science_mode_available(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / 'foods/apple.html').read_text()
    for text in ['Nutrition profile', 'Sensory profile', 'Research profile',
                 'Varieties &amp; relatives', 'Growing here', 'Culinary &amp; technical uses',
                 'id="science-mode"', 'id="season-region"', 'id="season-month"',
                 'id="season-mode"', 'data-science', 'No classified bioactivity evidence']:
        assert text in entry
    assert entry.index('class="entry-masthead"') < entry.index('class="profile-grid"')
    assert 'href="apple--honeycrisp.html"' in entry
    assert 'Missing regional data' in entry
    assert 'Linked by top-level registered taxon' in entry
    assert 'botanical family' not in entry


def test_scientific_record_reports_method_or_marks_it_missing(payload, tmp_path):
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(group="bioactivity", field="antifungal", v="growth reduced", src="SRC-A",
             tier=3, derivation="database", method="in_vitro:assay", flags=["evidence_only"]))
    payload["foods"][0]["claims"].append(
        dict(group="bioactivity", field="antiviral", v="reported", src="SRC-A",
             tier=3, derivation="database", method=None, flags=["evidence_only"]))
    render_site(payload, tmp_path)
    entry = (tmp_path / 'foods/apple.html').read_text()
    assert 'Method: in_vitro:assay' in entry
    assert 'Method: not reported' in entry


def test_season_evaluation_runs_in_javascript():
    code = Path('src/atlas/site/templates/_season.js.j2').read_text()
    harness = r'''
const assert = require('node:assert/strict');
const fields = Object.fromEntries(['season-region','season-month','season-mode'].map(id=>[id,{value:'',addEventListener(){}}]));
global.document={getElementById:id=>fields[id]||{textContent:''},querySelectorAll:()=>[],dispatchEvent(){}};
global.localStorage={getItem:()=>null,setItem(){}};
global.location={search:'',href:'http://localhost/index.html'};
global.history={replaceState(){}};
global.window=global;global.CustomEvent=function(){};global.addEventListener=()=>{};
CODE
fields['season-region'].value='CH';fields['season-month'].value='9';fields['season-mode'].value='fresh';
assert.equal(AtlasSeason.evaluate([]),'unknown');
const record={region:'CH',kind:'fresh',months:[9],src:'TEST'};
assert.equal(AtlasSeason.evaluate([record]),'available');
fields['season-month'].value='1';assert.equal(AtlasSeason.evaluate([record]),'unavailable');
fields['season-mode'].value='stored';assert.equal(AtlasSeason.evaluate([record]),'unknown');
fields['season-region'].value='US';assert.equal(AtlasSeason.evaluate([record]),'unknown');
console.log('season missing / fresh / stored / regional isolation verified');
'''.replace('CODE', code)
    result = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
