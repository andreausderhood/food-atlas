import io
import urllib.error
import zipfile

import pytest
import yaml

from atlas.fetch import Download, fetch, sha256_of
from atlas.links import check_links
from atlas.registry import Source


def make_zip(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("inner/food.csv", "fdc_id,description\n1,Apples, raw\n")
    return path


def dl(tmp_path, url, **kw):
    base = dict(id="x", source="SRC-X", url=url, filename="x.zip", dest="data/raw/x",
                sha256=None, unzip=True, manual=None)
    base.update(kw)
    return Download(**base)


def test_fetch_downloads_unzips_and_records(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root)
    assert (dest / "inner/food.csv").exists()
    record = (dest / "SOURCE.md").read_text(encoding="utf-8")
    assert sha256_of(dest / "x.zip") in record and "SRC-X" in record


def test_fetch_rejects_wrong_checksum(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    with pytest.raises(RuntimeError, match="sha256"):
        fetch(dl(tmp_path, z.as_uri(), sha256="0" * 64), tmp_path / "proj")


def test_manual_download_needs_from_file(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    d = dl(tmp_path, "https://example.org/session", manual="Download it in a browser.")
    with pytest.raises(RuntimeError, match="manually"):
        fetch(d, tmp_path / "proj")
    assert (fetch(d, tmp_path / "proj", from_file=z) / "inner/food.csv").exists()


def test_existing_source_record_is_kept(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    dest = tmp_path / "proj/data/raw/x"
    dest.mkdir(parents=True)
    (dest / "SOURCE.md").write_text("hand-written", encoding="utf-8")
    fetch(dl(tmp_path, z.as_uri()), tmp_path / "proj")
    assert (dest / "SOURCE.md").read_text(encoding="utf-8") == "hand-written"


class FakeResponse(io.BytesIO):
    def __init__(self, url):
        super().__init__(b"")
        self._url = url

    def geturl(self):
        return self._url


def test_nested_archive_stays_in_destination(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    assert (dest / "inner/food.csv").resolve().is_relative_to(dest.resolve())
    assert (dest / "inner/food.csv").read_text() == "fdc_id,description\n1,Apples, raw\n"


def test_identical_from_file_is_idempotent(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    paths = [dest / "x.zip", dest / "inner/food.csv", dest / "SOURCE.md"]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == before
    fetch(dl(tmp_path, z.as_uri()), root, from_file=dest / "x.zip")
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == before


def test_existing_archive_cannot_be_replaced(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    before = {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    other = tmp_path / "other.zip"
    with zipfile.ZipFile(other, "w") as archive:
        archive.writestr("inner/food.csv", "fdc_id,description\n2,Pears, raw\n")
    with pytest.raises(RuntimeError, match="immutable"):
        fetch(dl(tmp_path, other.as_uri()), root, from_file=other)
    assert {p.relative_to(dest): p.read_bytes() for p in dest.rglob("*") if p.is_file()} == before


def test_checksum_failure_leaves_cache_empty(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    with pytest.raises(RuntimeError, match="sha256"):
        fetch(dl(tmp_path, z.as_uri(), sha256="0" * 64), root, from_file=z)
    assert list((root / "data/raw/x").iterdir()) == []


def test_interrupted_copy_leaves_cache_empty(tmp_path, monkeypatch):
    import atlas.fetch as module

    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"

    def interrupted(source, out, *args, **kwargs):
        out.write(source.read(10))
        raise OSError("interrupted copy")

    monkeypatch.setattr(module.shutil, "copyfileobj", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    assert list((root / "data/raw/x").iterdir()) == []


def test_extraction_failure_does_not_publish_archive(tmp_path, monkeypatch):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"

    def interrupted(*args, **kwargs):
        raise OSError("interrupted extraction")

    monkeypatch.setattr(zipfile.ZipFile, "open", interrupted)
    with pytest.raises(OSError, match="interrupted extraction"):
        fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    assert list((root / "data/raw/x").iterdir()) == []


def test_changed_extracted_file_is_not_overwritten(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    extracted = dest / "inner/food.csv"
    extracted.write_text("local correction\n")
    with pytest.raises(RuntimeError, match="immutable"):
        fetch(dl(tmp_path, z.as_uri()), root)
    assert extracted.read_text() == "local correction\n"


def test_cached_checksum_is_rechecked_without_network(tmp_path, monkeypatch):
    import atlas.fetch as module

    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    d = dl(tmp_path, z.as_uri(), sha256=sha256_of(z))
    dest = fetch(d, root, from_file=z)
    (dest / "x.zip").write_bytes(b"incomplete copy")

    def no_network(*args, **kwargs):
        pytest.fail("cached archive must not trigger a request")

    monkeypatch.setattr(module.urllib.request, "urlopen", no_network)
    with pytest.raises(RuntimeError, match="sha256"):
        fetch(d, root)


def test_record_checksum_detects_changed_unpinned_cache(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    d = dl(tmp_path, z.as_uri())
    dest = fetch(d, root, from_file=z)
    (dest / "x.zip").write_bytes(b"incomplete copy")
    with pytest.raises(RuntimeError, match="sha256"):
        fetch(d, root)


def test_publish_failure_rolls_back_new_files(tmp_path, monkeypatch):
    import atlas.fetch as module

    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    real_link = module.os.link
    calls = []

    def interrupted(source, target):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("disk full")
        assert source.read_bytes()
        real_link(source, target)

    monkeypatch.setattr(module.os, "link", interrupted)
    with pytest.raises(OSError, match="disk full"):
        fetch(dl(tmp_path, z.as_uri()), root, from_file=z)
    assert len(calls) == 2
    assert list((root / "data/raw/x").iterdir()) == []


def test_missing_extracted_file_is_restored_without_rewriting_cache(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    d = dl(tmp_path, z.as_uri())
    dest = fetch(d, root, from_file=z)
    before = (dest / "x.zip").stat().st_mtime_ns
    (dest / "inner/food.csv").unlink()
    fetch(d, root)
    assert (dest / "inner/food.csv").is_file()
    assert (dest / "x.zip").stat().st_mtime_ns == before


def test_plain_file_is_cached_without_extraction(tmp_path):
    source = tmp_path / "food.csv"
    source.write_text("id,name\n1,Apple\n")
    d = dl(tmp_path, source.as_uri(), filename="food.csv", unzip=False,
           sha256=sha256_of(source).upper())
    dest = fetch(d, tmp_path / "proj", from_file=source)
    assert (dest / "food.csv").read_bytes() == source.read_bytes()
    assert sorted(p.name for p in dest.iterdir()) == ["SOURCE.md", "food.csv"]


def test_check_links_classifies(tmp_path):
    def src(sid, url):
        return Source(id=sid, title="t", publisher="p", url=url, license="l", license_class="ship",
                      license_read=True, kind="registry", independence="independent",
                      supports=("identity",), attribution="a")

    def opener(req, timeout):
        url = req.full_url
        if "gone" in url:
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        if "blocked" in url:
            raise urllib.error.HTTPError(url, 403, "forbidden", {}, None)
        if "moved" in url:
            return FakeResponse("https://example.org/new")
        return FakeResponse(url)

    sources = {s.id: s for s in (
        src("A", "https://example.org/a"), src("B", "https://example.org/gone"),
        src("C", "https://example.org/blocked"), src("D", "https://example.org/moved"),
    )}
    out = tmp_path / "link_status.yaml"
    assert check_links(sources, out, opener) == {"A": "ok", "B": "broken", "C": "unchecked", "D": "redirected"}
    assert yaml.safe_load(out.read_text(encoding="utf-8"))["B"]["status"] == "broken"
