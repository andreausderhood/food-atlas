import yaml

from atlas.cli import main


def test_atlas_coverage_is_wired(tmp_path, monkeypatch, capsys):
    from atlas.site import catalog
    monkeypatch.setattr(catalog, "_fdc_rows", lambda: [])
    monkeypatch.setattr(catalog, "_bls_rows", lambda: [])
    monkeypatch.setattr(catalog, "_ciqual_rows", lambda: [])
    monkeypatch.setattr(catalog, "_swiss_rows", lambda: [])
    scope = tmp_path / "data/research/scope"
    scope.mkdir(parents=True)
    (scope / "species-pool.yaml").write_text(
        yaml.safe_dump({"pool": {"malus domestica": {"common_names": ["apple"], "epd": {"path": "p"}}}}),
        encoding="utf-8")
    assert main(["--root", str(tmp_path), "coverage"]) == 0
    assert "Common names" in capsys.readouterr().out
