"""Discovery contract tests; synthetic labels/seasons are not production evidence."""
import shutil
import subprocess

import pytest
from jinja2 import Environment, PackageLoader


def render_index(tmp_path, rows=None):
    if rows is None:
        rows = [dict(id="food:apple", slug="apple", name="Apple", search="apple malus domestica crisp vitamin c", research=[], seasons=[]),
                dict(id="food:dried", slug="dried", name="Dried apple", search="dried apple vitamin c soft", research=[], seasons=[]),
                dict(id="food:cabbage", slug="cabbage", name="Cabbage", search="cabbage crisp vitamin k", research=[], seasons=[])]
    rows = [dict(family="org:test", family_name="Test family", level="taxon_food", taxon_name="Test taxon",
                 tiers=[1], claims=1, gaps=0, nutrition=1, molecules=0, preview=None) | row for row in rows]
    env = Environment(loader=PackageLoader("atlas.site", "templates"), autoescape=True)
    env.globals.update(image_for=lambda food: None)
    html = env.get_template("index.html.j2").render(rows=rows, atlas_rows=rows, root="",
        payload={"stats": {"accepted": len(rows)}}, sources={}, families={"org:test": "Test family"},
        level_label={"taxon_food": "Food"}, tier_label={1: "Measured"})
    (tmp_path / "index.html").write_text(html)
    return html


def browser_check(tmp_path, body):
    node = shutil.which("node")
    if not node or subprocess.run([node, "-e", "require('playwright')"], capture_output=True).returncode:
        pytest.skip("Local Node Playwright is not installed")
    script = r"""
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless:true});
 try {
  const page = await browser.newPage({viewport:{width:375,height:812}});
  const errors=[]; page.on('pageerror', e=>errors.push(e.message));
  const url=process.argv[1]+'/index.html';
  await page.goto(url);
  const visible=()=>page.locator('#grid .card:visible').evaluateAll(cards=>cards.map(c=>c.dataset.id));
""" + body + r"""
  assert.deepEqual(errors, []);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
"""
    result = subprocess.run([node, "-e", script, tmp_path.as_uri()], capture_output=True, text=True, timeout=60)
    if "Executable doesn't exist" in result.stderr:
        pytest.skip("Playwright browser is not installed")
    assert result.returncode == 0, result.stdout + result.stderr


def test_research_labels_and_missing_are_not_health_claims(tmp_path):
    html = render_index(tmp_path, [
        dict(id="food:lab", slug="lab", name="Lab example", search="example", research=["Laboratory activity"], seasons=[]),
        dict(id="food:unknown", slug="unknown", name="Unknown", search="example", research=[], seasons=[]),
    ])
    assert 'data-research=' in html
    assert 'Evidence not classified' in html
    browser_check(tmp_path, r'''
  assert.deepEqual(await page.locator('#research option').allTextContents(), ['All research categories', 'Laboratory activity', 'Evidence not classified']);
  await page.locator('#research').selectOption({label:'Laboratory activity'});
  assert.deepEqual(await visible(), ['food:lab']);
  await page.locator('#research').selectOption('unclassified');
  assert.deepEqual(await visible(), ['food:unknown']);
  assert.ok((await page.locator('#grid .card:visible').innerText()).includes('Evidence not classified'));
''')


def test_season_filter_separates_unknown_from_unavailable(tmp_path):
    render_index(tmp_path, [
        dict(id="food:fresh", slug="fresh", name="Fresh", search="apple", research=[], seasons=[dict(region="DE", kind="fresh", months=[9], src="TEST")]),
        dict(id="food:stored", slug="stored", name="Stored", search="apple", research=[], seasons=[dict(region="DE", kind="stored", months=[9], src="TEST")]),
        dict(id="food:unknown", slug="unknown", name="Unknown", search="cabbage", research=[], seasons=[]),
    ])
    browser_check(tmp_path, r'''
  assert.equal(await page.locator('[data-seasons]').count(), 3);
  // Isolate discovery's public season integration from the global widget implementation.
  await page.evaluate(()=>{
   window.discoverySeason={region:'DE',month:9,mode:'fresh'};
   window.AtlasSeason={state:()=>window.discoverySeason,evaluate:records=>{
    const {region,month,mode}=window.discoverySeason;
    const matching=records.filter(r=>r.region===region&&r.kind===mode);
    return !matching.length?'unknown':matching.some(r=>r.months.includes(month))?'available':'unavailable';
   }};
   document.dispatchEvent(new CustomEvent('atlas:season'));
  });
  assert.deepEqual(await visible(), ['food:fresh']);
  assert.ok((await page.locator('#season-unknown-count').innerText()).includes('2'));
  await page.locator('#q').fill('apple');
  assert.ok((await page.locator('#season-unknown-count').innerText()).includes('1'));
  await page.evaluate(()=>{discoverySeason.month=1;document.dispatchEvent(new CustomEvent('atlas:season'));});
  assert.deepEqual(await visible(), []);
  assert.ok((await page.locator('#season-unknown-count').innerText()).includes('1'));
  await page.evaluate(()=>{discoverySeason.mode='';document.dispatchEvent(new CustomEvent('atlas:season'));});
  assert.deepEqual(await visible(), ['food:fresh','food:stored']);
  assert.equal(await page.locator('#season-unknown-count').isVisible(), false);
''')


def test_url_saved_compare_and_view_survive_filtering(tmp_path):
    render_index(tmp_path)
    browser_check(tmp_path, r'''
  await page.goto(url+'?q=apple&exclude=dried&research=unclassified&family=org%3Atest&level=taxon_food&evidence=1&view=list&region=DE&month=9#main');
  assert.deepEqual(await visible(), ['food:apple']);
  assert.equal(await page.locator('#exclude').inputValue(), 'dried');
  assert.equal(await page.locator('#view-list').getAttribute('aria-pressed'), 'true');
  await page.locator('[data-save="food:apple"]').click();
  await page.locator('#saved-only').check();
  await page.locator('[data-compare="food:apple"]').click();
  assert.equal(await page.locator('#compare-tray').isVisible(), true);
  await page.reload();
  assert.deepEqual(await visible(), ['food:apple']);
  assert.equal(await page.locator('#saved-only').isChecked(), true);
  assert.equal(await page.locator('[data-compare="food:apple"]').getAttribute('aria-pressed'), 'true');
  let params=new URL(page.url()).searchParams;
  assert.equal(params.get('exclude'), 'dried');
  assert.equal(params.get('research'), 'unclassified');
  assert.equal(params.get('region'), 'DE');
  assert.equal(params.get('month'), '9');
  await page.locator('#reset').click();
  assert.equal((await visible()).length, 3);
  assert.equal(await page.locator('#exclude').inputValue(), '');
  assert.equal(await page.locator('#research').inputValue(), '');
  assert.equal(await page.locator('#saved-only').isChecked(), false);
  assert.equal(await page.locator('[data-save="food:apple"]').getAttribute('aria-pressed'), 'true');
  assert.equal(new URL(page.url()).hash, '#main');
  await page.evaluate(()=>{
    history.pushState(null,'','?q=cabbage&exclude=apple&view=cards');
    dispatchEvent(new PopStateEvent('popstate'));
  });
  assert.deepEqual(await visible(), ['food:cabbage']);
  assert.equal(await page.locator('#exclude').inputValue(), 'apple');
  assert.equal(await page.locator('#view-cards').getAttribute('aria-pressed'), 'true');
''')


def test_empty_dataset_keeps_unclassified_option(tmp_path):
    html = render_index(tmp_path, [])
    assert 'Evidence not classified' in html
    browser_check(tmp_path, r'''
  assert.deepEqual(await page.locator('#research option').allTextContents(), ['All research categories', 'Evidence not classified']);
  await page.locator('#research').selectOption('unclassified');
  assert.equal(await page.locator('#empty').isVisible(), true);
  assert.equal(await page.locator('#result-count').innerText(), '0 of 0 foods');
''')


def test_keyword_and_phrase_inclusion_exclusion(tmp_path):
    render_index(tmp_path)
    browser_check(tmp_path, r'''
  assert.ok((await page.locator('#search-help').innerText()).includes('Keyword search'));
  await page.locator('#q').fill('APPLE "vitamin c" -dried');
  assert.deepEqual(await visible(), ['food:apple']);
  await page.locator('#q').fill('apple');
  await page.locator('#exclude').fill('"vitamin c"');
  assert.deepEqual(await visible(), []);
  await page.locator('#exclude').fill('dried cabbage');
  assert.deepEqual(await visible(), ['food:apple']);
  await page.locator('#exclude').fill('');
  await page.locator('#q').fill('-"vitamin c"');
  assert.deepEqual(await visible(), ['food:cabbage']);
  await page.locator('#q').fill('apple "vitamin c');
  assert.deepEqual(await visible(), ['food:apple', 'food:dried']);
  await page.locator('#q').fill('apple vitamin k');
  assert.deepEqual(await visible(), []);
  await page.locator('#empty-reset').click();
  assert.equal((await visible()).length, 3);
  assert.equal(await page.locator('#q').evaluate(e=>e===document.activeElement), true);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
''')
