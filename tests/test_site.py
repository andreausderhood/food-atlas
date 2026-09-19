import pytest


@pytest.fixture
def payload():
    """Isolated synthetic payload: renderer tests do not require downloaded data."""
    def claim(src, value, **extra):
        return dict(subject="food:apple", group="nutrition", field="vitamin-c", v=value,
                    unit="mg", basis="fresh_weight", food_part="flesh", src=src,
                    tier=1, derivation="analytical", ref=None, flags=[], **extra)

    sources = [dict(id=s, title=f"Source {s}", license="CC0-1.0", url="https://example.org/",
                    publisher="Test publisher", license_class="open", kind="dataset",
                    independence="independent", link_status="ok", claims=1, attribution="Test attribution")
               for s in ("SRC-A", "SRC-B")]
    foods = [dict(id="food:apple", name="Apple", name_de="Apfel roh", level="taxon_food",
                  taxon="org:apple", claims=[claim("SRC-A", 4.6), claim("SRC-B", 7.2)], gaps=[]),
             dict(id="food:apple.honeycrisp", name="Honeycrisp", level="cultivar", name_de=None,
                  taxon="org:apple", is_a="food:apple", claims=[], gaps=[])]
    foods[0]["claims"][1].update(basis="dry_weight", food_part="peel")
    return dict(sources=sources, organisms=[dict(id="org:apple", name="Malus domestica")],
                foods=foods, nutrients={"vitamin-c": {"name": "Vitamin C"}}, molecules={},
                processes={}, gaps=[], stats={"accepted": 2, "gaps": 0})


def test_compare_preserves_every_source_and_amount_context(payload):
    from atlas.site.build import compare_data, compare_rows
    row, = compare_rows(["food:apple", "food:apple.honeycrisp"], payload)
    assert row["label"] == "Vitamin C"
    assert row["values"][1] == "not stated"
    for text in ("4.6 mg", "7.2 mg", "SRC-A", "SRC-B", "fresh_weight", "dry_weight", "flesh", "peel", "per 100 g"):
        assert text in row["values"][0]
    claims = compare_data(payload)["rows"]["food:apple"]["vitamin-c"]
    assert [c["v"] for c in claims] == [4.6, 7.2]
    assert all(c["tier"] == 1 and c["derivation"] == "analytical" for c in claims)
    assert [c["basis"] for c in claims] == ["fresh_weight", "dry_weight"]


def test_render_site_evidence_and_navigation(payload, tmp_path):
    from atlas.site.build import render_site
    food = payload["foods"][0]
    food["claims"].extend([
        dict(subject=food["id"], group="sensory", field="taste", v="crisp", src="SRC-A",
             tier=4, derivation="editorial", flags=[], ref=None),
        dict(subject=food["id"], group="molecules", field="contains:quercetin", v="present",
             src="SRC-B", tier=3, derivation="literature", flags=[], ref="PMC444,PMC555"),
    ])
    gap = dict(subject=food["id"], field="health", rule=8, question="Health wording rejected.",
               would_be_settled_by="Suitable evidence and review.",
               carried_value="An anti-inflammatory food.", src="SRC-A")
    payload["gaps"] = food["gaps"] = [gap]
    payload["molecules"] = {"quercetin": {"name": "Quercetin"}}
    out = tmp_path / "site"
    written = {p.relative_to(out).as_posix() for p in render_site(payload, out)}
    assert written == {"index.html", "compare.html", "gaps.html", "sources.html",
                       "molecules.html", "foods/apple.html", "foods/apple--honeycrisp.html"}
    entry = (out / "foods/apple.html").read_text()
    assert "Malus domestica" in entry
    assert "4.6 mg per 100 g" in entry and "fresh_weight" in entry and "flesh" in entry
    # Sensory evidence appears in its compact profile and the full scientific record.
    assert entry.count('class="chip tier-') == 5
    assert "machine-extracted" in entry and "unvalidated" in entry
    assert "https://pmc.ncbi.nlm.nih.gov/articles/PMC444/" in entry
    assert "https://pmc.ncbi.nlm.nih.gov/articles/PMC555/" in entry
    assert gap["carried_value"] not in entry
    gaps = (out / "gaps.html").read_text()
    assert "Rule 8" in gaps and gap["carried_value"] in gaps and "not food facts" in gaps
    compare = (out / "compare.html").read_text()
    assert "not stated" in compare and "4.6 mg per 100 g" in compare
    assert "7.2 mg per 100 g" in compare and "dry_weight" in compare and "peel" in compare
    assert compare.count('class="chip tier-1"') == 2
    assert 'title="Source SRC-B' in compare and "CC0-1.0" in compare
    assert "CC0-1.0" in (out / "sources.html").read_text()
    index = (out / "index.html").read_text()
    assert "#F2EFE8" in index and "#FF4F00" in index
    assert "[hidden]" in index and "!important" in index
    assert "apple--honeycrisp.html" in index


def test_html_templates_escape_source_text(payload, tmp_path):
    import json
    import re
    from atlas.site.build import render_site
    text = '<b>literal & "quoted"</b>'
    payload["foods"][0]["name"] = text
    payload["sources"][0]["title"] = text
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert text not in entry
    assert "&lt;b&gt;literal &amp; &#34;quoted&#34;&lt;/b&gt;" in entry
    compare = (tmp_path / "compare.html").read_text()
    embedded = re.search(r'<script id="compare-data" type="application/json">(.*?)</script>', compare, re.S)
    assert embedded is not None
    assert json.loads(embedded[1])["foods"][0]["name"] == text
    assert "<b>" not in embedded[1]


def test_molecule_concentration_does_not_invent_per_100g(payload):
    from atlas.site.build import sections
    food = payload["foods"][0]
    food["claims"] = [dict(group="molecules", field="contains:q", v=2, unit="mg/kg",
                           basis="dry_weight", food_part="peel", tier=3,
                           derivation="literature", src="SRC-B", ref=None)]
    _, claims = sections(food, payload)[0]
    assert claims[0]["display"] == "2 mg/kg"
    assert claims[0]["machine_extracted"] is True


def test_compare_union_and_zero(payload):
    from atlas.site.build import compare_rows
    second = dict(payload["foods"][0]["claims"][0], field="energy", v=0, unit="kcal")
    payload["foods"][1]["claims"] = [second]
    rows = {r["field"]: r["values"] for r in compare_rows([f["id"] for f in payload["foods"]], payload)}
    assert rows["energy"][0] == "not stated"
    assert rows["energy"][1].startswith("0 kcal per 100 g")
    assert compare_rows([], payload) == []


def test_render_site_from_build(project, tmp_path):
    from atlas.build import build
    from atlas.site.build import render_site
    data = build(project).payload
    written = {p.relative_to(tmp_path).as_posix() for p in render_site(data, tmp_path)}
    assert {"index.html", "compare.html", "gaps.html", "sources.html",
            "foods/apple--honeycrisp.html"} <= written
    entry = (tmp_path / "foods/apple--honeycrisp.html").read_text()
    assert "Vitamin C, total ascorbic acid" in entry
    assert "SRC-FDC-FOUNDATION-2026-04" in entry and "fresh_weight" in entry
    assert "machine-extracted" in entry and "unvalidated" in entry and "PMC444" in entry
    apple = (tmp_path / "foods/apple.html").read_text()
    assert "Amount without unit, basis or food part." in apple
    assert "CC0-1.0" in (tmp_path / "sources.html").read_text()
    gaps = (tmp_path / "gaps.html").read_text()
    assert "Rule 8" in gaps and "An anti-inflammatory food." in gaps
    assert "apple--dried.html" in (tmp_path / "index.html").read_text()
    assert "not stated" in (tmp_path / "compare.html").read_text()


def test_compare_rows_marks_blanks(project):
    from atlas.build import build
    from atlas.site.build import compare_rows
    data = build(project).payload
    rows = {r["label"]: r["values"] for r in compare_rows(
        ["food:apple", "food:apple.honeycrisp"], data)}
    assert rows["Vitamin C, total ascorbic acid"][0] == "not stated"
    assert rows["Vitamin C, total ascorbic acid"][1].startswith("4.6 mg per 100 g")


def test_mobile_filters_and_live_compare(payload, tmp_path):
    """Optional browser regression: runs when a local Node Playwright is available."""
    import shutil
    import subprocess
    from atlas.site.build import render_site
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not installed")
    probe = subprocess.run([node, "-e", "require('playwright')"], capture_output=True)
    if probe.returncode:
        pytest.skip("Local Playwright is not installed")
    render_site(payload, tmp_path)
    script = r"""
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 375, height: 812}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.argv[1] + '/index.html');
    assert.equal(await page.locator('.card:visible').count(), 2);
    await page.locator('#q').fill('apple');
    assert.equal(await page.locator('.card:visible').count(), 1);
    await page.locator('#level').selectOption('cultivar');
    assert.equal(await page.locator('.card:visible').count(), 0);
    await page.locator('#q').fill('');
    assert.equal(await page.locator('.card:visible').count(), 1);
    await page.goto(process.argv[1] + '/compare.html');
    await page.locator('#pick-1').selectOption('food:apple.honeycrisp');
    const text = await page.locator('#cmp').innerText();
    for (const value of ['4.6 mg per 100 g', '7.2 mg per 100 g', 'SRC-A', 'SRC-B',
                         'fresh_weight', 'dry_weight', 'flesh', 'peel', 'not stated']) {
      assert.ok(text.includes(value), value);
    }
    assert.equal(await page.locator('#cmp .chip').count(), 2);
    assert.ok((await page.locator('#cmp .chip').last().getAttribute('title')).includes('CC0-1.0'));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.goto(process.argv[1] + '/foods/apple.html');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    for (const width of [320, 375, 768, 1050, 1280, 1920]) {
      await page.setViewportSize({width, height: 812});
      for (const path of ['/index.html', '/foods/apple.html']) {
        await page.goto(process.argv[1] + path);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${path} overflow at ${width}`);
        assert.ok(await page.evaluate(() => Math.abs(document.querySelector('.brand').getBoundingClientRect().left - document.querySelector('h1').getBoundingClientRect().left) < 1), `header alignment at ${width}`);
      }
      await page.goto(process.argv[1] + '/index.html');
      assert.ok(await page.locator('.card-actions button').evaluateAll(buttons => buttons.every(button => button.getBoundingClientRect().height <= 33)), `wrapped button at ${width}`);
      assert.ok(await page.locator('.card-meta').evaluateAll(items => items.every(item => item.getBoundingClientRect().height < 36)), `wrapped metadata at ${width}`);
    }
    assert.deepEqual(errors, []);
    console.log('Mobile filters, live comparison, evidence chips and page widths verified.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
"""
    result = subprocess.run([node, "-e", script, tmp_path.as_uri()], capture_output=True, text=True, timeout=60)
    if "Executable doesn't exist" in result.stderr:
        pytest.skip("Playwright browser is not installed")
    assert result.returncode == 0, result.stdout + result.stderr


def test_explorer_metadata_and_accepted_molecules(payload, tmp_path):
    from atlas.site.build import index_rows, molecule_rows, render_site
    payload["molecules"] = {"q": {"name": "Quercetin"}, "rejected": {"name": "Rejected only"}}
    payload["foods"][0]["claims"].append(dict(group="molecules", field="contains:q", v="present",
        src="SRC-B", tier=3, derivation="literature", ref="PMC444", flags=[]))
    rows = index_rows(payload)
    assert rows[0]["family"] == "org:apple"
    assert rows[0]["nutrition"] == 2
    assert rows[0]["molecules"] == 1
    assert rows[0]["tiers"] == [1, 3]
    assert "malus domestica" in rows[0]["search"]
    assert [m["name"] for m in molecule_rows(payload)] == ["Quercetin"]
    render_site(payload, tmp_path)
    index = (tmp_path / "index.html").read_text()
    for control in ('id="family"', 'id="evidence"', 'id="result-count"', 'id="reset"',
                    'id="saved-only"', 'id="compare-tray"', 'id="theme"', 'data-save=', 'data-compare='):
        assert control in index
    detail = (tmp_path / "foods/apple--honeycrisp.html").read_text()
    assert "Nutrition not yet available" in detail
    assert 'href="apple.html"' in detail
    assert "Rejected only" not in (tmp_path / "molecules.html").read_text()


def test_editorial_evidence_is_compact_and_traceable(payload, tmp_path):
    from atlas.site.build import render_site
    payload["stats"]["accepted"] = 2597
    payload["foods"][0]["claims"].extend([
        dict(group="narrative", field=field, v="A readable description.", src="SRC-A",
             tier=4, derivation="editorial", ref="Editorial note", flags=[])
        for field in ("story", "eli5")
    ])
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    # Task 7 retires the "hover or focus a tier marker" evidence line and the eli5
    # lede's chip along with the old entry-header: the masthead's lede is plain text
    # (spec's "no tier marks on the reading surface" constraint), so only the
    # Culinary & technical uses section's "story" claim still carries a compact chip.
    assert 'class="editorial-evidence"' not in entry
    assert entry.count('>T4</span>') == 1
    assert "SRC-A · CC0-1.0 · Editorial note" in entry
    assert "2,597 accepted claims" in (tmp_path / "index.html").read_text()


def test_slug():
    from atlas.site.build import slug
    assert slug("food:apple.honeycrisp") == "apple--honeycrisp"


def test_token_layer_replaces_the_invented_palette(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    index = (tmp_path / "index.html").read_text()
    for token, value in [("--paper", "#F2EFE8"), ("--paper-2", "#E8E4DA"),
                         ("--ink", "#0B0B0B"), ("--accent", "#FF4F00"),
                         ("--cobalt", "#1530FF")]:
        assert f"{token}:{value}" in index or f"{token}: {value}" in index, token
    for retired in ("#B10034", "#F1EEE7", "#25251f"):
        assert retired not in index, retired
    for family in ("Archivo", "Inter Tight", "JetBrains Mono", "Instrument Serif"):
        assert family in index, family


def test_german_food_names_never_reach_the_ui(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    index = (tmp_path / "index.html").read_text()
    assert "Apfel roh" not in entry
    assert "Apfel roh" not in index and "apfel roh" not in index
    assert "Malus domestica" in entry


def test_source_titles_stay_verbatim(payload, tmp_path):
    """A published title is a citation, not UI copy (spec, Global Constraints)."""
    from atlas.site.build import render_site
    payload["sources"][0]["title"] = "Bundeslebensmittelschlüssel (BLS), Version 4.0"
    render_site(payload, tmp_path)
    assert "Bundeslebensmittelschlüssel (BLS), Version 4.0" in (tmp_path / "sources.html").read_text()


def test_square_corners_and_no_shadows(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    index = (tmp_path / "index.html").read_text()
    assert "border-radius:6px" not in index and "border-radius:10px" not in index
    assert "box-shadow:0 8px 36px" not in index


@pytest.mark.xfail(reason="entry-profiles lands in Task 8", strict=True)
def test_masthead_order_identity_then_plate_then_profiles(payload, tmp_path):
    """Composition C: identity first, then the plate, then the profiles (spec §4)."""
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="narrative", field="eli5",
             v="An apple is a fruit you can hold in one hand.",
             src="SRC-A", tier=4, derivation="editorial", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert entry.index('class="entry-masthead"') < entry.index('class="entry-plate"')
    assert entry.index('class="entry-plate"') < entry.index('class="entry-profiles"')


def test_masthead_carries_identity_and_lede(payload, tmp_path):
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="narrative", field="eli5",
             v="An apple is a fruit you can hold in one hand.",
             src="SRC-A", tier=4, derivation="editorial", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert 'class="entry-binomial"' in entry and "Malus domestica" in entry
    assert "An apple is a fruit you can hold in one hand." in entry
    assert 'class="entry-tags"' in entry


def test_season_tag_shows_month_names_not_numbers(payload, tmp_path):
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="season", field="season:CH:fresh",
             v=[10, 11, 12], src="SRC-A", tier=3, derivation="extracted",
             flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert "In season:" in entry and "Oct, Nov, Dec" in entry
    assert "10, 11, 12" not in entry
