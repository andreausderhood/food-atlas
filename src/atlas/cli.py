"""`atlas` command line: fetch, check-links, build, site, curate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.build import build
from atlas.curate import search_bls, search_fdc, search_foodatlas
from atlas.fetch import fetch, load_downloads
from atlas.links import check_links
from atlas.registry import load_sources
from atlas.site.build import render_site

SEARCH = {"fdc": search_fdc, "bls": search_bls, "foodatlas": search_foodatlas}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download a raw source listed in data/registry/downloads.yaml")
    f.add_argument("id")
    f.add_argument("--from-file", type=Path)
    sub.add_parser("check-links", help="check every source URL (rule 4)")
    b = sub.add_parser("build", help="validate all claims and write data/build")
    b.add_argument("--no-raw", action="store_true", help="skip raw sources that are not downloaded")
    sub.add_parser("site", help="render data/build/site from data/build/atlas.json")
    c = sub.add_parser("curate", help="search raw sources while editing foods.yaml")
    c.add_argument("kind", choices=sorted(SEARCH))
    c.add_argument("query")
    from atlas.research.cli import register, dispatch
    register(sub)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.cmd == "research":
        return dispatch(args, root)
    registry = root / "data/registry"

    if args.cmd == "fetch":
        print(fetch(load_downloads(registry / "downloads.yaml")[args.id], root, args.from_file))
        return 0
    if args.cmd == "check-links":
        results = check_links(load_sources(registry / "sources.yaml"), registry / "link_status.yaml")
        for sid, status in sorted(results.items()):
            print(f"{status:10} {sid}")
        return 1 if "broken" in results.values() else 0
    if args.cmd == "build":
        result = build(root, require_raw=not args.no_raw)
        print(f"accepted {len(result.validation.accepted)} · gaps {len(result.validation.gaps)}")
        return 0
    if args.cmd == "site":
        payload = json.loads((root / "data/build/atlas.json").read_text(encoding="utf-8"))
        for path in render_site(payload, root / "data/build/site"):
            print(path)
        return 0
    if args.cmd == "curate":
        print("\n".join(SEARCH[args.kind](root, args.query)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
