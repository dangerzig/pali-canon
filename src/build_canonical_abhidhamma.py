#!/usr/bin/env python3
"""
Build canonical-format Abhidhamma files from SuttaCentral bilara-data.

Reads segmented JSON files from bilara-data and creates canonical-format
JSON files in data/canonical/abhidhamma/, preserving segment IDs for the
lemmatization pipeline.

Output format matches DN canonical files (flat segments):
{
  "id": "dhammasangani",
  "title_pali": "Dhammasaṅgaṇī",
  "collection": "abhidhamma",
  "segments": [
    {"id": "ds1.1:0.1", "pali": "Dhammasaṅgaṇī"},
    ...
  ]
}

SC Abhidhamma structure -> output files:
  ds/       -> dhammasangani
  vb/       -> vibhanga
  dt/       -> dhatukatha
  pp/       -> puggalapannatti
  kv/       -> kathavatthu
  ya/ ya1-5 -> yamaka1
  ya/ ya6-10 -> yamaka2
  patthana/ -> patthana
"""

import json
import re
from pathlib import Path

try:
    from pali.text import normalize_pali
except ImportError:
    def normalize_pali(text):
        text = text.replace('ṁ', 'ṃ')
        return re.sub(r'\s+', ' ', text).strip()

DATA_DIR = Path(__file__).parent.parent / "data"
BILARA_DIR = DATA_DIR / "bilara-data" / "root" / "pli" / "ms" / "abhidhamma"
OUTPUT_DIR = DATA_DIR / "canonical" / "abhidhamma"


def load_bilara_segments(filepath: Path) -> list:
    """Load a bilara JSON file and return list of {id, pali} segments."""
    data = json.loads(filepath.read_text(encoding='utf-8'))
    segments = []
    for seg_id, text in data.items():
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text).strip()
        if clean and clean != '{}':
            segments.append({
                "id": seg_id,
                "pali": normalize_pali(clean)
            })
    return segments


def load_bilara_tree_segments(dirpath: Path) -> list:
    """Recursively load all bilara files under a directory tree."""
    segments = []
    # First load files directly in this directory
    for f in sorted(dirpath.glob('*_root-pli-ms.json')):
        segments.extend(load_bilara_segments(f))
    # Then recurse into subdirectories
    for subdir in sorted(d for d in dirpath.iterdir() if d.is_dir()):
        segments.extend(load_bilara_tree_segments(subdir))
    return segments


def build_simple_text(sc_dir_name, output_id, title_pali):
    """Build a single canonical file from a bilara directory."""
    dirpath = BILARA_DIR / sc_dir_name
    segments = load_bilara_tree_segments(dirpath)
    return {
        "id": output_id,
        "title_pali": title_pali,
        "collection": "abhidhamma",
        "segments": segments
    }


def build_yamaka1():
    """Build Yamaka I (ya1-ya5)."""
    ya_dir = BILARA_DIR / "ya"
    segments = []
    for subdir in sorted(ya_dir.iterdir()):
        if not subdir.is_dir():
            continue
        m = re.search(r'ya(\d+)', subdir.name)
        if m and int(m.group(1)) <= 5:
            segments.extend(load_bilara_tree_segments(subdir))

    return {
        "id": "yamaka1",
        "title_pali": "Yamaka I",
        "collection": "abhidhamma",
        "segments": segments
    }


def build_yamaka2():
    """Build Yamaka II (ya6-ya10)."""
    ya_dir = BILARA_DIR / "ya"
    segments = []
    for subdir in sorted(ya_dir.iterdir()):
        if not subdir.is_dir():
            continue
        m = re.search(r'ya(\d+)', subdir.name)
        if m and int(m.group(1)) > 5:
            segments.extend(load_bilara_tree_segments(subdir))

    return {
        "id": "yamaka2",
        "title_pali": "Yamaka II",
        "collection": "abhidhamma",
        "segments": segments
    }


def build_patthana():
    """Build Patthana (all 24 paccayas)."""
    pat_dir = BILARA_DIR / "patthana"
    segments = load_bilara_tree_segments(pat_dir)
    return {
        "id": "patthana",
        "title_pali": "Paṭṭhāna",
        "collection": "abhidhamma",
        "segments": segments
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Simple one-to-one mappings
    simple_texts = [
        ('ds', 'dhammasangani', 'Dhammasaṅgaṇī'),
        ('vb', 'vibhanga', 'Vibhaṅga'),
        ('dt', 'dhatukatha', 'Dhātukathā'),
        ('pp', 'puggalapannatti', 'Puggalapaññatti'),
        ('kv', 'kathavatthu', 'Kathāvatthu'),
    ]

    index = {
        "collection": "Abhidhamma Piṭaka",
        "description": "The Basket of Higher Doctrine",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "texts": []
    }

    total_segs = 0
    all_texts = []

    # Build simple texts
    for sc_dir, output_id, title in simple_texts:
        text_data = build_simple_text(sc_dir, output_id, title)
        all_texts.append(text_data)

    # Build yamaka (split)
    all_texts.append(build_yamaka1())
    all_texts.append(build_yamaka2())

    # Build patthana
    all_texts.append(build_patthana())

    # Save all
    for text_data in all_texts:
        seg_count = len(text_data["segments"])
        total_segs += seg_count

        outfile = OUTPUT_DIR / f"{text_data['id']}.json"
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(text_data, f, indent=2, ensure_ascii=False)

        index["texts"].append({
            "id": text_data["id"],
            "title_pali": text_data["title_pali"],
            "segments": seg_count
        })

        print(f"  {text_data['title_pali']:40s} ({seg_count:6,} segments)")

    index["total_segments"] = total_segs

    # Save index
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Total: {len(all_texts)} texts, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
