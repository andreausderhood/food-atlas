"""Exercise the public CLI using real registry/build file formats, offline."""
import json

from atlas.cli import main


def test_cli_initializes_real_artifacts_idempotently_and_reports_status(tmp_path, capsys):
    registry = tmp_path / "data/registry"
    registry.mkdir(parents=True)
    (registry / "sources.yaml").write_text("""S:
  title: Test source
  publisher: Test publisher
  url: https://example.org
  license: Unknown
  license_class: cite
  license_read: false
  kind: registry
  independence: independent
  supports: [origin]
  attribution: Test
""")
    (registry / "images.yaml").write_text("{}\n")
    (registry / "foods.yaml").write_text("excluded_foodatlas: {}\nfood:apple:\n  name: Apple\n")
    build = tmp_path / "data/build"
    build.mkdir()
    (build / "gaps.csv").write_text("subject,field,rule,src\nfood:apple,origin,5,S\n")
    (build / "claims.csv").write_text("subject,group\n")
    args = ["--root", str(tmp_path), "research"]
    assert main(args + ["init"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["counts"]["queued"] > 1
    assert first["by_kind"]["image"] == 1
    assert first["ready"][0]["kind"] == "license_read"
    assert main(args + ["init"]) == 0
    assert json.loads(capsys.readouterr().out) == first
    assert main(args + ["status"]) == 0
    assert json.loads(capsys.readouterr().out) == first


def test_cli_missing_build_fails_without_creating_database(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "research", "init"]) == 1
    assert "atlas build" in capsys.readouterr().err
    assert not (tmp_path / "data/research/state.db").exists()


def test_status_does_not_create_empty_state(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "research", "status"]) == 0
    assert json.loads(capsys.readouterr().out)["initialized"] is False
    assert not (tmp_path / "data/research/state.db").exists()
