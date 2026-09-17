"""Independent QA fixtures; runnable without pytest or atlas dependencies."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/audit_build.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_build", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload_fixture():
    claim = {"subject": "food:apple", "group": "nutrition", "field": "vitamin_c",
             "v": 4.6, "unit": "mg", "basis": "fresh_weight", "food_part": "whole",
             "src": "SRC-A", "tier": 1, "derivation": "analytical", "ref": "row:1",
             "v_min": None, "v_max": None, "n": None, "flags": [], "curated": False}
    return {"foods": [{"id": "food:apple", "foodatlas_ids": ["e1"], "bls_codes": [],
                       "claims": [claim], "gaps": []}],
            "organisms": [{"id": "org:apple", "claims": []}],
            "sources": [{"id": "SRC-A", "license": "CC0", "license_read": True,
                         "license_class": "ship", "claims": 1, "supports": ["nutrition"],
                         "url": "https://example.org", "attribution": "Test fixture"}],
            "gaps": [], "excluded_foodatlas": {"e1671": "Other species"},
            "stats": {"accepted": 1, "gaps": 0, "sources_used": ["SRC-A"],
                      "missing_raw": [], "partial": False}}


class AuditBuildTests(unittest.TestCase):
    def test_payload_counts_and_expected_partial_sources(self):
        payload = payload_fixture()
        payload["stats"].update(partial=True, missing_raw=["bls"])
        payload["sources"].append({"id": "SRC-BLS-4.0", "license": "CC BY 4.0",
                                   "license_class": "ship", "license_read": True, "claims": 0})
        payload["gaps"].append({"subject": "dataset:bls", "field": "raw_source", "rule": 5,
                                 "src": "SRC-BLS-4.0", "carried_value": None})
        payload["stats"]["gaps"] = 1
        report = load_tool().audit_payload(payload)
        self.assertEqual(report["counts"], {"foods": 1, "organisms": 1, "claims": 1,
                                            "gaps": 1, "sources": 2})
        self.assertEqual(report["implementation_errors"], [])
        self.assertEqual(report["expected_missing_sources"][0]["dataset"], "bls")
        self.assertEqual(report["source_licenses"][0]["license"], "CC0")
        self.assertEqual(report["numeric_checks"]["checked"], 1)
        self.assertEqual(report["excluded_mappings"]["violations"], [])

    def test_integrity_findings_are_not_expected_missing_sources(self):
        payload = payload_fixture()
        claim = payload["foods"][0]["claims"][0]
        claim.update(v=float("nan"), basis="wet", food_part=None, unit=None)
        payload["foods"][0]["claims"].append(dict(claim))
        payload["foods"][0]["foodatlas_ids"].append("e1671")
        payload["sources"][0].update(license_class="adapter", license_read=False)
        payload["organisms"][0]["claims"].append(dict(claim, subject="org:apple", src="SRC-TYPO"))
        payload["gaps"].append({"subject": "food:apple", "src": "SRC-GAP-TYPO", "rule": 2})
        report = load_tool().audit_payload(payload)
        codes = {e["code"] for e in report["implementation_errors"]}
        self.assertTrue({"invalid_amount", "non_finite", "source_license", "excluded_mapping",
                         "unresolved_claim_source", "stats_mismatch", "duplicate_claim"} <= codes)
        self.assertEqual(report["expected_missing_sources"], [])
        self.assertEqual(report["unresolved_source_refs"]["gaps"][0]["src"], "SRC-GAP-TYPO")
        self.assertEqual(report["numeric_checks"]["checked"], 3)
        json.dumps(report, allow_nan=False)

    def test_pmc_presence_not_counted_as_amount(self):
        payload = payload_fixture()
        claim = payload["foods"][0]["claims"][0]
        claim.update(group="molecules", field="contains:CHEBI:1", v="present", unit=None,
                     basis=None, src="SRC-FOODATLAS-V4.11", derivation="extracted",
                     tier=3, ref="PMC123, PMC456", flags=["llm_extracted"])
        payload["sources"][0].update(id=claim["src"], supports=["molecules"])
        payload["stats"]["sources_used"] = [claim["src"]]
        report = load_tool().audit_payload(payload)
        self.assertEqual(report["pmc"]["ids"], ["PMC123", "PMC456"])
        self.assertEqual(report["pmc"]["presence_claims"], 1)
        self.assertEqual(report["numeric_checks"]["checked"], 0)
        self.assertEqual(report["implementation_errors"], [])
        claim["ref"] = ""
        broken = load_tool().audit_payload(payload)
        self.assertIn("missing_pmc", {e["code"] for e in broken["implementation_errors"]})

    def test_internal_links_fragments_queries_and_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "data/build/site"
            site.mkdir(parents=True)
            (site / "index.html").write_text('<a href="other.html?q=1#yes">ok</a>'
                '<a href="other.html#missing">bad</a><img src="lost.png">'
                '<a href="https://example.org">external</a><a href="../../../../secret">escape</a>')
            (site / "other.html").write_text('<p id="yes">Target</p>')
            report = {"implementation_errors": [], "limitations": []}
            load_tool().audit_site(site, root, report)
            self.assertEqual(report["internal_links"]["checked"], 4)
            self.assertEqual(len(report["internal_links"]["broken"]), 3)
            self.assertEqual(report["internal_links"]["external_skipped"], 1)

    def test_unused_restricted_sources_and_independent_refs_are_not_errors(self):
        payload = payload_fixture()
        payload["sources"].append({"id": "SRC-NOT-IMPORTED", "license_class": "adapter", "claims": 0})
        claim = dict(payload["foods"][0]["claims"][0], ref="row:2")
        payload["foods"][0]["claims"].append(claim)
        payload["stats"]["accepted"] = 2
        payload["sources"][0]["claims"] = 2
        self.assertEqual(load_tool().audit_payload(payload)["implementation_errors"], [])

    def test_cite_without_ref_and_finite_bounds_are_rejected(self):
        payload = payload_fixture()
        payload["sources"][0]["license_class"] = "cite"
        payload["foods"][0]["claims"][0].update(v_max=float("inf"), curated=True, ref="")
        report = load_tool().audit_payload(payload)
        self.assertTrue({"source_license", "non_finite"} <= {e["code"] for e in report["implementation_errors"]})
        json.dumps(report, allow_nan=False)

    def test_absent_build_is_not_misreported_as_success_or_bad_source(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(TOOL), "--root", directory],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "not_built")
        self.assertEqual(report["implementation_errors"], [])
        self.assertEqual(report["expected_missing_sources"], [])
        self.assertIsNone(report["counts"]["claims"])
        self.assertTrue(report["limitations"])


if __name__ == "__main__":
    unittest.main()
