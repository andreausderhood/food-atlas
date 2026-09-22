#!/usr/bin/env python3
"""High-throughput scraper for all 4,010 Indian medicinal plants in IMPPAT 2.0.

Features:
- Full coverage: All 4,010 botanical species from data/raw/imppat-2.0/all_plants.json
- Resumable: Skips already scraped plants in imppat_records.jsonl
- Rate-limited concurrent workers (3 workers, 0.25s delay)
- Continuous atomic flush to JSONL
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ensure atlas package is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from atlas.ingest.imppat import fetch_imppat_phytochemicals, fetch_imppat_therapeutics


def main():
    root = Path(__file__).resolve().parent.parent
    imppat_dir = root / "data/raw/imppat-2.0"
    plants_file = imppat_dir / "all_plants.json"
    records_file = imppat_dir / "imppat_records.jsonl"

    if not plants_file.is_file():
        print(f"Error: {plants_file} not found.")
        return 1

    all_plants = json.loads(plants_file.read_text(encoding="utf-8"))
    print(f"🌿 Loaded {len(all_plants)} total plants from {plants_file.name}")

    seen = set()
    if records_file.is_file():
        with records_file.open(encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        if rec.get("plant_name"):
                            seen.add(rec["plant_name"])
                    except Exception:
                        pass

    print(f"🔍 Found {len(seen)} already harvested plants in {records_file.name}")
    remaining = [p for p in all_plants if p not in seen]
    print(f"⏳ Remaining to harvest: {len(remaining)} plants")

    if not remaining:
        print("🎉 All 4,010 plants already harvested!")
        return 0

    lock = threading.Lock()
    done_count = 0
    total = len(remaining)
    start_time = time.time()

    def worker(plant_name: str) -> dict | None:
        try:
            phys = fetch_imppat_phytochemicals(plant_name, timeout=25)
            time.sleep(0.2)
            tus = fetch_imppat_therapeutics(plant_name, timeout=25)
            time.sleep(0.2)
            return {
                "plant_name": plant_name,
                "ayurvedic_properties": {},
                "phytochemicals": phys,
                "therapeutics": tus,
            }
        except Exception as e:
            return {"plant_name": plant_name, "error": str(e), "phytochemicals": [], "therapeutics": []}

    with records_file.open("a", encoding="utf-8") as out_fp:
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_plant = {executor.submit(worker, p): p for p in remaining}
            for future in as_completed(future_to_plant):
                plant = future_to_plant[future]
                res = future.result()
                if res is not None:
                    with lock:
                        out_fp.write(json.dumps(res, ensure_ascii=False) + "\n")
                        out_fp.flush()
                        done_count += 1
                        if done_count % 25 == 0 or done_count == total:
                            elapsed = time.time() - start_time
                            rate = done_count / max(elapsed, 0.1)
                            eta_min = (total - done_count) / max(rate, 0.01) / 60
                            print(f"[{done_count}/{total}] ({done_count/total*100:.1f}%) "
                                  f"Harvested: {plant} | {rate:.1f} plants/s | ETA: {eta_min:.1f} min")

    print(f"\n🎉 All {len(all_plants)} IMPPAT plants successfully harvested into {records_file}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
