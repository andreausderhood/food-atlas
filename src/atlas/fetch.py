"""Download raw sources with checksums and write a SOURCE.md provenance record."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml


@dataclass(frozen=True)
class Download:
    id: str
    source: str
    url: str
    filename: str
    dest: str
    sha256: str | None
    unzip: bool
    manual: str | None


def load_downloads(path: Path) -> dict[str, Download]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        k: Download(id=k, source=d["source"], url=d["url"], filename=d["filename"], dest=d["dest"],
                    sha256=d.get("sha256"), unzip=bool(d.get("unzip", False)), manual=d.get("manual"))
        for k, d in raw.items()
    }


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _contained(base: Path, relative: str) -> Path:
    """Require a relative path with no symlink components or parent traversal."""
    posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
    if (not relative or posix.is_absolute() or windows.drive or windows.root
            or ".." in posix.parts or "\\" in relative):
        raise ValueError(f"path escapes destination: {relative!r}")
    target = base / relative
    if not target.resolve().is_relative_to(base.resolve()):
        raise ValueError(f"path escapes destination: {relative!r}")
    current = base
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink in destination: {relative!r}")
    return target


def _check_digest(dl: Download, digest: str, record: Path) -> None:
    expected = dl.sha256
    if expected and digest != expected.lower():
        raise RuntimeError(f"{dl.id}: sha256 {digest} does not match the manifest ({expected})")
    if record.exists():
        text = record.read_text(encoding="utf-8")
        # Respect hand-written records; only interpret this fetcher's checksum field.
        if f"| File | `{dl.filename}`" in text:
            match = re.search(r"^\| SHA-256 \| `([a-fA-F0-9]{64})` \|$", text, re.MULTILINE)
            if match and digest != match[1].lower():
                raise RuntimeError(f"{dl.id}: sha256 {digest} does not match SOURCE.md")


def _stage_zip(archive: Path, stage: Path, dest: Path, filename: str) -> None:
    with zipfile.ZipFile(archive) as z:
        seen: set[Path] = set()
        for info in z.infolist():
            output = _contained(stage, info.filename)
            _contained(dest, info.filename)
            relative = output.relative_to(stage)
            if (not relative.parts or relative.parts[0] in (filename, "SOURCE.md")
                    or relative in seen):
                raise ValueError(f"archive contains duplicate or reserved path: {info.filename!r}")
            seen.add(relative)
            mode = stat.S_IFMT(info.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError(f"archive contains non-regular entry: {info.filename!r}")
            if info.is_dir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as source, output.open("xb") as out:
                    shutil.copyfileobj(source, out)


def _publish(stage: Path, dest: Path) -> None:
    """Preflight the entire staged tree, then atomically add files without clobbering."""
    entries = sorted(stage.rglob("*"), key=lambda p: (len(p.parts), str(p)))
    for source in entries:
        target = _contained(dest, source.relative_to(stage).as_posix())
        if target.exists():
            same = (target.is_dir() if source.is_dir() else
                    target.is_file() and sha256_of(source) == sha256_of(target))
            if not same:
                raise RuntimeError(f"immutable raw file already exists: {target}")
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for source in entries:
            target = _contained(dest, source.relative_to(stage).as_posix())
            if source.is_dir():
                if not target.exists():
                    target.mkdir()
                    created_dirs.append(target)
            elif target.exists():
                if not target.is_file() or sha256_of(source) != sha256_of(target):
                    raise RuntimeError(f"immutable raw file already exists: {target}")
            else:
                # Same-filesystem hard linking publishes complete bytes atomically and
                # refuses a concurrent writer instead of replacing its raw file.
                os.link(source, target)
                created_files.append(target)
    except Exception:
        for path in reversed(created_files):
            path.unlink()
        for path in reversed(created_dirs):
            path.rmdir()
        raise


def fetch(dl: Download, root: Path, from_file: Path | None = None) -> Path:
    dest = _contained(root, dl.dest)
    if len(PurePosixPath(dl.filename).parts) != 1 or dl.filename == "SOURCE.md":
        raise ValueError(f"invalid archive filename: {dl.filename!r}")
    target = _contained(dest, dl.filename)
    record = _contained(dest, "SOURCE.md")
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".fetch-", dir=dest) as temporary:
        work = Path(temporary)
        stage = work / "publish"
        stage.mkdir()
        if target.exists():
            digest = sha256_of(target)
            _check_digest(dl, digest, record)
            if from_file is not None and sha256_of(from_file) != digest:
                raise RuntimeError(f"{dl.id}: immutable raw file already exists: {target}")
            archive = target
        else:
            archive = stage / dl.filename
            if from_file is not None:
                with from_file.open("rb") as source, archive.open("xb") as out:
                    shutil.copyfileobj(source, out)
            else:
                if dl.manual:
                    raise RuntimeError(f"{dl.id}: download manually, then pass --from-file. {dl.manual}")
                request = urllib.request.Request(dl.url, headers={"User-Agent": "food-atlas-fetch"})
                with urllib.request.urlopen(request, timeout=300) as source, archive.open("xb") as out:
                    shutil.copyfileobj(source, out)
            digest = sha256_of(archive)
            _check_digest(dl, digest, record)
        if dl.unzip:
            _stage_zip(archive, stage, dest, dl.filename)
        if not record.exists():
            (stage / "SOURCE.md").write_text(
                f"# Source record — {dl.id}\n\n"
                "| Field | Value |\n| :--- | :--- |\n"
                f"| Source ID | `{dl.source}` |\n"
                f"| File | `{dl.filename}` ({archive.stat().st_size:,} bytes) |\n"
                f"| URL | {dl.url} |\n"
                f"| SHA-256 | `{digest}` |\n"
                f"| Fetched | {date.today().isoformat()} |\n\n"
                "Raw files are never edited. License and attribution: `data/registry/sources.yaml`.\n",
                encoding="utf-8",
            )
        _publish(stage, dest)
    return dest
