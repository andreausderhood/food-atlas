"""Rule 4: check every source URL and record the result (machine-owned file)."""
from __future__ import annotations

import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import yaml

from atlas.registry import Source

UNCHECKABLE = (401, 403, 405, 429)  # servers that refuse automated checks; not proof of a dead link


def check_links(sources: dict[str, Source], out_path: Path, opener=urllib.request.urlopen) -> dict[str, str]:
    results: dict[str, str] = {}
    for s in sources.values():
        request = urllib.request.Request(s.url, method="HEAD", headers={"User-Agent": "food-atlas-linkcheck"})
        try:
            with opener(request, timeout=20) as response:
                same = response.geturl().rstrip("/") == s.url.rstrip("/")
                results[s.id] = "ok" if same else "redirected"
        except urllib.error.HTTPError as e:
            results[s.id] = "unchecked" if e.code in UNCHECKABLE else "broken"
        except (urllib.error.URLError, TimeoutError):
            results[s.id] = "broken"
    today = date.today().isoformat()
    out_path.write_text(
        "# MACHINE-OWNED — written by `atlas check-links`. Do not hand-edit.\n"
        + yaml.safe_dump({k: {"status": v, "checked": today} for k, v in sorted(results.items())}),
        encoding="utf-8",
    )
    return results
