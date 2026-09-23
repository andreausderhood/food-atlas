import json
import pytest
from pathlib import Path
from atlas.ingest.base import get_adapter
from atlas.contract import check as contract_check

RAW_PATH = Path("data/raw/bzfe-saison/saisonkalender.json")

def test_adapter_registered():
    """SRC-BZFE-SAISONKALENDER adapter must be registered."""
    a = get_adapter("SRC-BZFE-SAISONKALENDER")
    assert a is not None

def test_claims_emitted():
    """Adapter must emit claims from saisonkalender.json."""
    a = get_adapter("SRC-BZFE-SAISONKALENDER")
    claims = list(a.iter_claims(RAW_PATH))
    assert len(claims) > 0

def test_harvest_claim_structure():
    """Each harvest claim must have correct group, field, and ref."""
    a = get_adapter("SRC-BZFE-SAISONKALENDER")
    claims = [c for c in a.iter_claims(RAW_PATH)
              if getattr(c, 'field', None) == 'season:harvest:months']
    assert len(claims) > 0
    c = claims[0]
    # cite class requires ref
    assert c.ref is not None and len(c.ref) > 0
    # value should be a JSON list of integers
    import json
    months = json.loads(c.v)
    assert isinstance(months, list)
    assert all(isinstance(m, int) and 1 <= m <= 12 for m in months)

def test_claims_pass_contract():
    """All emitted claims must pass contract.check."""
    from atlas.registry import load_sources
    sources = load_sources()
    a = get_adapter("SRC-BZFE-SAISONKALENDER")
    claims = list(a.iter_claims(RAW_PATH))
    for c in claims:
        result = contract_check(c, sources)
        assert result.ok, f"Contract failed for {c}: {result.reason}"
