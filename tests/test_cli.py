from atlas.cli import main


def test_build_and_site(project, capsys):
    assert main(["--root", str(project), "build"]) == 0
    assert "accepted 8 · gaps " in capsys.readouterr().out
    assert main(["--root", str(project), "site"]) == 0
    assert (project / "data/build/site/index.html").exists()


def test_curate_fdc(project, capsys):
    assert main(["--root", str(project), "curate", "fdc", "honeycrisp"]) == 0
    assert "Apples, honeycrisp, with skin, raw" in capsys.readouterr().out


def test_curate_foodatlas(project, capsys):
    assert main(["--root", str(project), "curate", "foodatlas", "apple"]) == 0
    out = capsys.readouterr().out
    assert "e897\tapple" in out and "e1536\tHoneycrisp apple" in out
