"""Content-addressed fetched text. Only deterministic tools populate this cache."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


class Cache:
    def __init__(self, directory: Path):
        self.directory = directory

    def store(self, url: str, text: str) -> str:
        blob = json.dumps({"url": url, "text": text}, ensure_ascii=False, sort_keys=True).encode()
        key = hashlib.sha256(blob).hexdigest()
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / (key + ".json")
        if path.exists():
            if path.read_bytes() != blob:
                raise ValueError("cache integrity failure")
        else:
            with path.open("xb") as stream:
                stream.write(blob)
        return key

    def read(self, key: str, url: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", key):
            raise ValueError("invalid cache key")
        path = self.directory / (key + ".json")
        if not path.resolve().is_relative_to(self.directory.resolve()):
            raise ValueError("cache path escape")
        blob = path.read_bytes()
        if hashlib.sha256(blob).hexdigest() != key:
            raise ValueError("cache integrity failure")
        data = json.loads(blob)
        if data["url"] != url:
            raise ValueError("cached URL mismatch")
        return data["text"]
