#!/usr/bin/env python3
"""Independent, read-only QA audit of Food Atlas build artifacts. Pure stdlib.

Deliberately imports nothing from `atlas` so it can never inherit the build's
own bugs; it re-derives every count from the artifact on disk.

Audited artifact: data/build/atlas.json (payload written by atlas.build).
Cross-checked siblings when present: claims.csv, gaps.csv, NOT...[truncated]