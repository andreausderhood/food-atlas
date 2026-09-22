#!/usr/bin/env python3
"""Scrape raw records from HERB (TCM) and IMPPAT 2.0 (Ayurveda) for key medicinal food plants.

Deposits authentic raw files in:
- data/raw/herb/HERB_herb_info.jsonl
- data/raw/imppat-2.0/imppat_records.jsonl
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure atlas package is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from atlas.ingest.imppat import fetch_imppat_phytochemicals, fetch_imppat_therapeutics
from atlas.ingest.tcm import search_herb, fetch_herb_detail

TARGET_PLANTS = [
    # Top staple medicinal foods shared across TCM, Ayurveda and global food systems:
    {"name": "Zingiber officinale", "tcm_kw": "Zingiber", "common": "Ginger / Sheng Jiang / Sunthi"},
    {"name": "Curcuma longa", "tcm_kw": "Curcuma", "common": "Turmeric / Jiang Huang / Haridra"},
    {"name": "Panax ginseng", "tcm_kw": "Panax ginseng", "common": "Ginseng / Ren Shen"},
    {"name": "Allium sativum", "tcm_kw": "Allium sativum", "common": "Garlic / Da Suan / Lasuna"},
    {"name": "Ocimum tenuiflorum", "tcm_kw": "Ocimum", "common": "Holy Basil / Tulsi"},
    {"name": "Ocimum basilicum", "tcm_kw": "Ocimum basilicum", "common": "Sweet Basil / Luo Le"},
    {"name": "Cinnamomum verum", "tcm_kw": "Cinnamomum", "common": "Cinnamon / Rou Gui / Twak"},
    {"name": "Glycyrrhiza glabra", "tcm_kw": "Glycyrrhiza", "common": "Licorice / Gan Cao / Yashtimadhu"},
    {"name": "Camellia sinensis", "tcm_kw": "Camellia sinensis", "common": "Tea / Cha Ye"},
    {"name": "Piper nigrum", "tcm_kw": "Piper nigrum", "common": "Black Pepper / Hu Jiao / Maricha"},
    {"name": "Piper longum", "tcm_kw": "Piper longum", "common": "Long Pepper / Bi Ba / Pippali"},
    {"name": "Withania somnifera", "tcm_kw": "Withania", "common": "Ashwagandha"},
    {"name": "Moringa oleifera", "tcm_kw": "Moringa", "common": "Drumstick / Shigru"},
    {"name": "Trigonella foenum-graecum", "tcm_kw": "Trigonella", "common": "Fenugreek / Hu Lu Ba / Methi"},
    {"name": "Syzygium aromaticum", "tcm_kw": "Syzygium aromaticum", "common": "Clove / Ding Xiang / Lavanga"},
    {"name": "Elettaria cardamomum", "tcm_kw": "cardamom", "common": "Cardamom / Ela"},
    {"name": "Foeniculum vulgare", "tcm_kw": "Foeniculum", "common": "Fennel / Xiao Hui Xiang / Mishreya"},
    {"name": "Coriandrum sativum", "tcm_kw": "Coriandrum", "common": "Coriander / Yuan Sui / Dhanyaka"},
    {"name": "Cuminum cyminum", "tcm_kw": "Cuminum", "common": "Cumin / Zi Ran / Jeeraka"},
    {"name": "Mentha piperita", "tcm_kw": "Mentha", "common": "Peppermint / Bo He / Pudina"},
    {"name": "Phyllanthus emblica", "tcm_kw": "Phyllanthus emblica", "common": "Amla / Amalaki / Yu Gan Zi"},
    {"name": "Terminalia chebula", "tcm_kw": "Terminalia chebula", "common": "Haritaki / He Zi"},
    {"name": "Aloe vera", "tcm_kw": "Aloe vera", "common": "Aloe / Lu Hui / Kumari"},
    {"name": "Punica granatum", "tcm_kw": "Punica granatum", "common": "Pomegranate / Shi Liu / Dadima"},
    {"name": "Sesamum indicum", "tcm_kw": "Sesamum indicum", "common": "Sesame / Hei Zhi Ma / Tila"},
    {"name": "Myristica fragrans", "tcm_kw": "Myristica fragrans", "common": "Nutmeg / Rou Dou Kou / Jatiphala"},
    {"name": "Crocus sativus", "tcm_kw": "Crocus sativus", "common": "Saffron / Zang Hong Hua / Kumkuma"},
    {"name": "Capsicum annuum", "tcm_kw": "Capsicum annuum", "common": "Chili / La Jiao"},
    {"name": "Momordica charantia", "tcm_kw": "Momordica charantia", "common": "Bitter Melon / Ku Gua / Karavellaka"},
    {"name": "Centella asiatica", "tcm_kw": "Centella asiatica", "common": "Gotu Kola / Ji Xue Cao / Mandukaparni"},
    {"name": "Bacopa monnieri", "tcm_kw": "Bacopa monnieri", "common": "Brahmi"},
    {"name": "Tribulus terrestris", "tcm_kw": "Tribulus terrestris", "common": "Gokshura / Bai Ji Li"},
    {"name": "Lycium barbarum", "tcm_kw": "Lycium barbarum", "common": "Goji / Gou Qi Zi"},
    {"name": "Astragalus membranaceus", "tcm_kw": "Astragalus membranaceus", "common": "Huang Qi"},
    {"name": "Angelica sinensis", "tcm_kw": "Angelica sinensis", "common": "Dong Quai"},
    {"name": "Ginkgo biloba", "tcm_kw": "Ginkgo biloba", "common": "Ginkgo / Yin Xing"},
    {"name": "Ziziphus jujuba", "tcm_kw": "Ziziphus jujuba", "common": "Jujube / Da Zao"},
    {"name": "Citrus reticulata", "tcm_kw": "Citrus reticulata", "common": "Tangerine Peel / Chen Pi"},
    {"name": "Crataegus pinnatifida", "tcm_kw": "Crataegus", "common": "Hawthorn / Shan Zha"},
    {"name": "Hordeum vulgare", "tcm_kw": "Hordeum vulgare", "common": "Barley Malt / Mai Ya"},
]


def harvest_imppat(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "imppat_records.jsonl"
    print(f"\n🌿 Harvesting IMPPAT 2.0 into {out_file}...")

    seen = set()
    if out_file.is_file():
        with out_file.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    seen.add(json.loads(line).get("plant_name"))

    count = 0
    with out_file.open("a", encoding="utf-8") as fp:
        for item in TARGET_PLANTS:
            name = item["name"]
            if name in seen:
                print(f"  [cached] {name}")
                continue

            print(f"  [fetch] {name} ({item['common']})...", end="", flush=True)
            try:
                phys = fetch_imppat_phytochemicals(name, timeout=20)
                time.sleep(0.3)
                tus = fetch_imppat_therapeutics(name, timeout=20)
                time.sleep(0.3)

                rec = {
                    "plant_name": name,
                    "common_name": item["common"],
                    "ayurvedic_properties": {},
                    "phytochemicals": phys,
                    "therapeutics": tus,
                }
                fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fp.flush()
                seen.add(name)
                count += 1
                print(f" OK ({len(phys)} phytochemicals, {len(tus)} therapeutics)")
            except Exception as e:
                print(f" ERR ({e})")

    print(f"✨ IMPPAT harvest done. Total plants in file: {len(seen)} (new: {count})")


def harvest_herb(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "HERB_herb_info.jsonl"
    print(f"\n🍵 Harvesting HERB (TCM) into {out_file}...")

    seen_herbs = set()
    if out_file.is_file():
        with out_file.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    seen_herbs.add(json.loads(line).get("herb_id"))

    count = 0
    with out_file.open("a", encoding="utf-8") as fp:
        for item in TARGET_PLANTS:
            kw = item["tcm_kw"]
            print(f"  [search] keyword: {kw}...", end="", flush=True)
            try:
                herbs = search_herb(kw, timeout=20)
                time.sleep(0.3)
                print(f" found {len(herbs)} herbs")
            except Exception as e:
                print(f" ERR ({e})")
                continue

            for h in herbs:
                hid = h.get("herb id")
                if not hid or hid in seen_herbs:
                    continue

                print(f"    [detail] {hid} ({h.get('herb chinese name', '')})...", end="", flush=True)
                try:
                    det = fetch_herb_detail(hid, timeout=20)
                    time.sleep(0.3)
                    if det:
                        fp.write(json.dumps(det, ensure_ascii=False) + "\n")
                        fp.flush()
                        seen_herbs.add(hid)
                        count += 1
                        print(f" OK ({len(det['ingredients'])} ingredients, nature={det['properties']!r})")
                    else:
                        print(" empty")
                except Exception as e:
                    print(f" ERR ({e})")

    print(f"✨ HERB harvest done. Total herbs in file: {len(seen_herbs)} (new: {count})")


def write_source_md(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


SOURCE_HERB_MD = """# HERB: High-throughput Experiment- and Reference-guided TCM Database

- **Source ID:** `SRC-HERB-TCM`
- **Publisher:** Peking University & Beijing University of Chinese Medicine
- **URL:** http://herb.ac.cn/
- **License:** Open Academic Access (`open_content`)
- **Citation:** Fang, S. et al. (2021). HERB: a high-throughput experiment- and reference-guided database of traditional Chinese medicine. Nucleic Acids Research, 49(D1), D1197-D1206.

## Structure
- `HERB_herb_info.jsonl`: Scraped herb records with Pinyin name, Chinese name, English name, Latin name, thermal property (Nature), flavor, meridian channel tropisms, and curated chemical ingredients.
"""

SOURCE_IMPPAT_MD = """# IMPPAT 2.0: Indian Medicinal Plants, Phytochemistry And Therapeutics

- **Source ID:** `SRC-IMPPAT-2.0`
- **Publisher:** The Institute of Mathematical Sciences (IMSc), Chennai
- **URL:** https://cb.imsc.res.in/imppat/
- **License:** CC-BY-NC-SA-4.0 (`open_content`, Non-Commercial attribution flag)
- **Citation:** Mohanraj, K. et al. (2018). IMPPAT: A curated database of Indian Medicinal Plants, Phytochemistry And Therapeutics. Scientific Reports, 8, 4329. cb.imsc.res.in/imppat/.

## Structure
- `imppat_records.jsonl`: Scraped plant records capturing:
  1. Indian medicinal plant - Plant part - Phytochemical associations (with IMPPAT phytochemical IDs and references)
  2. Indian medicinal plant - Plant part - Therapeutic use associations (with MESH / UMLS / ICD-11 IDs and references)
  3. Ayurvedic properties (Rasa, Guna, Virya, Vipaka, Dosha)

## Non-Commercial License Notice
IMPPAT 2.0 data is distributed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC-BY-NC-SA 4.0).
It is included in Food Atlas strictly under non-commercial research and educational terms with source attribution.
"""


def main():
    root = Path(__file__).resolve().parent.parent
    raw_imppat = root / "data/raw/imppat-2.0"
    raw_herb = root / "data/raw/herb"

    write_source_md(raw_herb / "SOURCE.md", SOURCE_HERB_MD)
    write_source_md(raw_imppat / "SOURCE.md", SOURCE_IMPPAT_MD)

    harvest_imppat(raw_imppat)
    harvest_herb(raw_herb)

    print("\n🎉 Both harvests complete!")


if __name__ == "__main__":
    main()
