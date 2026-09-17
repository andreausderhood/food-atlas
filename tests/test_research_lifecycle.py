"""Public proposal lifecycle. All evidence below is explicitly synthetic test data."""
import json

from atlas.cli import main
from atlas.research.evidence import Cache
from atlas.research.queue import Task
from atlas.research.state import State


def setup(tmp_path):
    task = Task.create("license_read", "licenses", "S", "license", "S")
    child = Task.create("basis_gap", "coverage", "food:apple", "vitamin", "S", (task.id,))
    with State(tmp_path / "data/research/state.db") as state:
        state.enqueue([task, child])
    key = Cache(tmp_path / "data/research/cache").store(
        "https://example.org/license", "Synthetic test license evidence: CC0")
    return task, {"kind": "license_read", "subject": "S", "field": "license",
                  "source": "S", "findings": {"license": "CC0"},
                  "evidence": [{"ref": "https://example.org/license", "quote": "CC0", "cache_key": key}]}


def test_claim_submit_and_review_does_not_unlock_dependencies(tmp_path, capsys):
    task, proposal = setup(tmp_path)
    args = ["--root", str(tmp_path), "research"]
    assert main(args + ["next", "--lease-by", "agent-a"]) == 0
    lease = json.loads(capsys.readouterr().out)
    assert lease["item"]["id"] == task.id
    assert lease["lease"]["claimed_by"] == "agent-a"
    proposal.update(item_id=task.id, lease_token=lease["lease"]["token"])
    payload = tmp_path / "proposal.json"
    payload.write_text(json.dumps(proposal))
    assert main(args + ["submit", str(payload)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "pending_review"
    saved = json.loads((tmp_path / result["path"]).read_text())
    assert "lease_token" not in saved
    assert main(args + ["next", "--lease-by", "agent-b"]) == 0
    assert json.loads(capsys.readouterr().out)["item"] is None
    assert main(args + ["review", result["proposal_id"]]) == 0
    reviewed = json.loads(capsys.readouterr().out)
    assert reviewed["status"] == "pending_review"
    assert reviewed["proposal"]["evidence"] == proposal["evidence"]
    with State(tmp_path / "data/research/state.db") as state:
        assert state.counts() == {"pending_review": 1, "queued": 1}
    # Replaying a submitted lease cannot create another proposal.
    assert main(args + ["submit", str(payload)]) == 1
    assert "lease" in capsys.readouterr().err


def test_submit_rejects_wrong_lease_and_fabricated_evidence(tmp_path, capsys):
    task, proposal = setup(tmp_path)
    args = ["--root", str(tmp_path), "research"]
    assert main(args + ["next", "--lease-by", "agent-a"]) == 0
    lease = json.loads(capsys.readouterr().out)["lease"]
    proposal.update(item_id=task.id, lease_token="wrong")
    payload = tmp_path / "proposal.json"
    payload.write_text(json.dumps(proposal))
    assert main(args + ["submit", str(payload)]) == 1
    assert "lease" in capsys.readouterr().err
    proposal["lease_token"] = lease["token"]
    proposal["evidence"][0]["quote"] = "fabricated quotation"
    payload.write_text(json.dumps(proposal))
    assert main(args + ["submit", str(payload)]) == 1
    assert "quotation" in capsys.readouterr().err
    with State(tmp_path / "data/research/state.db") as state:
        assert state.counts() == {"queued": 2}
        assert state.db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0
    assert not list((tmp_path / "data/proposals").rglob("*.json"))


def test_missing_state_next_does_not_create_state(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "research", "next", "--lease-by", "a"]) == 1
    assert "research init" in capsys.readouterr().err
    assert not (tmp_path / "data/research/state.db").exists()

