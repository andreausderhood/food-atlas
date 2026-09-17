# Independent build QA

Run from the repository root (no downloads, rebuilds, or production writes):

```sh
python3 tools/audit_build.py --root .
python3 tests/test_audit_build.py
uv run pytest tests/test_audit_build.py -q
# Same audit with the project's optional DuckDB package available:
uv run python tools/audit_build.py --root .
```

The CLI emits strict JSON on stdout. Exit **0** means audited with no implementation findings, **1** means implementation findings, **2** means `atlas.json` is absent (not a pass), and **3** means the audit could not complete. Do not treat exit 0 as proof that all datasets or scientific coverage are complete. See `limitations`, `expected_missing_sources`, and the individual audit sections.

## Automated checks

- [ ] Food, organism, accepted claim, gap and source counts agree with payload statistics. Organism-owned claims count too.
- [ ] Every accepted claim source resolves. Unresolved gap references are reported separately; a rule-2 gap with no carried value is a rejected input, not accepted broken provenance.
- [ ] Accepted-source licenses are read and permit shipping or curated, specifically referenced citations. Unused adapter/restricted sources are not falsely reported as shipped data.
- [ ] Nutrition/molecule numeric values carry a unit, accepted basis (`fresh_weight`, `dry_weight`, `as_sold`) and food part. Values and numeric bounds are finite; extracted amounts do not ship as accepted measurements.
- [ ] All seven excluded FoodAtlas trap IDs remain excluded. Mapping ownership and duplicate IDs/claims are checked. Different primary references are not collapsed as duplicate claims.
- [ ] FoodAtlas molecule presence claims retain PMC references; presence is not counted as concentration.
- [ ] A declared missing download has a registered source and matching rule-5 dataset gap. Expected missing downloads are separate from broken artifacts, bad statistics or unresolved accepted source references.
- [ ] CSV row counts match payload; required JSON/CSV/DuckDB artifacts and repository NOTICE exist. With DuckDB installed, five database table counts match in a read-only connection.
- [ ] Site HTML `href`/`src` targets and fragment IDs resolve, including query strings and URL encoding. Duplicate HTML IDs and links escaping the site are findings. External URLs are counted but never fetched.

## Manual / separate checks still required

- [ ] If site is absent, render it through the normal build workflow before calling QA complete. An absent site is explicitly reported as untested.
- [ ] Open site pages at desktop/mobile sizes; exercise search, filters, comparison and gap visibility. Static HTML inspection does not run JavaScript or validate CSS URLs/srcset.
- [ ] Check scientific scope and wording against primary sources; this tool does not establish scientific validity or independently verify legal permissions.
- [ ] Verify importer tests exclude CTD and avoid shipping PMC evidence sentences. Aggregate JSON cannot prove raw-row selection or text-license provenance.
- [ ] Review CSV/DB value parity when changing serialization. This tool checks export counts, not complete cell-for-cell equality.
- [ ] Do not infer raw-source absence merely because a source has no accepted claims. `stats.missing_raw` and a matching dataset gap are required for the expected-missing classification.

## Known audit evidence

The tool was exercised against real build outputs, not invented fixture results: 33 foods, 8 organisms, 2,597 accepted claims, 764 gaps and 11 sources. An initial site audit found `molecules.html` links to missing `foods/*.html#molecules` anchors; a later real execution after sibling site changes passed: 38 HTML pages, 2,957 internal links checked, zero broken links, all five database counts matching, CLI exit 0. BLS, FDC Foundation and FDC SR Legacy remained explicitly classified as expected missing downloads. Re-run after regeneration; this snapshot is not a persistent assertion about later builds.
