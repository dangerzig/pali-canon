#!/usr/bin/env python3
"""
Build canonical-format Vinaya files from SuttaCentral bilara-data.

Reads segmented JSON files from bilara-data and creates canonical-format
JSON files in data/canonical/vinaya/, preserving segment IDs for the
lemmatization pipeline.

Output format matches DN canonical files (flat segments):
{
  "id": "mahavagga",
  "title_pali": "Mahāvagga",
  "collection": "vinaya",
  "segments": [
    {"id": "pli-tv-kd1:0.1", "pali": "Theravāda Vinayapiṭaka"},
    ...
  ]
}

SC Vinaya structure -> output files:
  pli-tv-bu-pm + pli-tv-bu-vb pj/ss/ay/np + pli-tv-bi-vb pj/ss
    -> suttavibhanga1
  pli-tv-bi-pm + pli-tv-bu-vb pc/pd/sk/as + pli-tv-bi-vb np/pc/pd/sk/as
    -> suttavibhanga2
  pli-tv-kd1-10  -> mahavagga
  pli-tv-kd11-22 -> cullavagga
  pli-tv-pvr     -> parivara
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
BILARA_DIR = DATA_DIR / "bilara-data" / "root" / "pli" / "ms" / "vinaya"
OUTPUT_DIR = DATA_DIR / "canonical" / "vinaya"


def load_bilara_segments(filepath: Path) -> list:
    """Load a bilara JSON file and return list of {id, pali} segments."""
    data = json.loads(filepath.read_text(encoding='utf-8'))
    segments = []
    for seg_id, text in data.items():
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text).strip()
        if clean and clean != '{}':
            # Strip English structural labels (e.g., "Chapter 1. Kaṭhina" -> "Kaṭhina")
            clean = re.sub(r'^Chapter\s+\d+\.\s*', '', clean)
            pali = normalize_pali(clean)
            if pali:
                segments.append({
                    "id": seg_id,
                    "pali": pali
                })
    return segments


def load_bilara_dir_segments(dirpath: Path) -> list:
    """Load all bilara files in a directory (sorted) and return segments."""
    files = sorted(dirpath.glob('*_root-pli-ms.json'))
    segments = []
    for f in files:
        segments.extend(load_bilara_segments(f))
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


def build_suttavibhanga1():
    """Build Suttavibhanga I (Parajika section)."""
    bu_vb = BILARA_DIR / "pli-tv-bu-vb"
    bi_vb = BILARA_DIR / "pli-tv-bi-vb"

    segments = []

    # Bhikkhu Patimokkha
    bu_pm = BILARA_DIR / "pli-tv-bu-pm_root-pli-ms.json"
    if bu_pm.exists():
        segments.extend(load_bilara_segments(bu_pm))

    # Bhikkhu vibhanga: pj, ss, ay, np
    for subdir_name in ['pli-tv-bu-vb-pj', 'pli-tv-bu-vb-ss',
                        'pli-tv-bu-vb-ay', 'pli-tv-bu-vb-np']:
        subdir = bu_vb / subdir_name
        if subdir.is_dir():
            segments.extend(load_bilara_tree_segments(subdir))
        else:
            f = bu_vb / f"{subdir_name}_root-pli-ms.json"
            if f.exists():
                segments.extend(load_bilara_segments(f))

    # Bhikkhuni vibhanga: pj, ss
    for subdir_name in ['pli-tv-bi-vb-pj', 'pli-tv-bi-vb-ss']:
        subdir = bi_vb / subdir_name
        if subdir.is_dir():
            segments.extend(load_bilara_tree_segments(subdir))

    return {
        "id": "suttavibhanga1",
        "title_pali": "Suttavibhaṅga I (Pārājika)",
        "collection": "vinaya",
        "segments": segments
    }


def build_suttavibhanga2():
    """Build Suttavibhanga II (Pacittiya section)."""
    bu_vb = BILARA_DIR / "pli-tv-bu-vb"
    bi_vb = BILARA_DIR / "pli-tv-bi-vb"

    segments = []

    # Bhikkhuni Patimokkha
    bi_pm = BILARA_DIR / "pli-tv-bi-pm_root-pli-ms.json"
    if bi_pm.exists():
        segments.extend(load_bilara_segments(bi_pm))

    # Bhikkhu vibhanga: pc, pd, sk
    for subdir_name in ['pli-tv-bu-vb-pc', 'pli-tv-bu-vb-pd',
                        'pli-tv-bu-vb-sk']:
        subdir = bu_vb / subdir_name
        if subdir.is_dir():
            segments.extend(load_bilara_tree_segments(subdir))

    # Adhikarana-samatha (top-level file)
    as_file = bu_vb / "pli-tv-bu-vb-as1-7_root-pli-ms.json"
    if as_file.exists():
        segments.extend(load_bilara_segments(as_file))

    # Bhikkhuni sections: np, pc, pd, sk
    for subdir_name in ['pli-tv-bi-vb-np', 'pli-tv-bi-vb-pc',
                        'pli-tv-bi-vb-pd', 'pli-tv-bi-vb-sk']:
        subdir = bi_vb / subdir_name
        if subdir.is_dir():
            segments.extend(load_bilara_tree_segments(subdir))

    # Bhikkhuni Adhikarana-samatha
    bi_as = bi_vb / "pli-tv-bi-vb-as1-7_root-pli-ms.json"
    if bi_as.exists():
        segments.extend(load_bilara_segments(bi_as))

    return {
        "id": "suttavibhanga2",
        "title_pali": "Suttavibhaṅga II (Pācittiya)",
        "collection": "vinaya",
        "segments": segments
    }


def build_mahavagga():
    """Build Mahavagga (kd1-10)."""
    kd_dir = BILARA_DIR / "pli-tv-kd"
    segments = []
    for i in range(1, 11):
        kd_file = kd_dir / f"pli-tv-kd{i}_root-pli-ms.json"
        if kd_file.exists():
            segments.extend(load_bilara_segments(kd_file))

    return {
        "id": "mahavagga",
        "title_pali": "Mahāvagga",
        "collection": "vinaya",
        "segments": segments
    }


def build_cullavagga():
    """Build Cullavagga (kd11-22)."""
    kd_dir = BILARA_DIR / "pli-tv-kd"
    segments = []
    for i in range(11, 23):
        kd_file = kd_dir / f"pli-tv-kd{i}_root-pli-ms.json"
        if kd_file.exists():
            segments.extend(load_bilara_segments(kd_file))

    return {
        "id": "cullavagga",
        "title_pali": "Cūḷavagga",
        "collection": "vinaya",
        "segments": segments
    }


def build_parivara():
    """Build Parivara."""
    pvr_dir = BILARA_DIR / "pli-tv-pvr"
    segments = load_bilara_tree_segments(pvr_dir)

    return {
        "id": "parivara",
        "title_pali": "Parivāra",
        "collection": "vinaya",
        "segments": segments
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    builders = [
        build_suttavibhanga1,
        build_suttavibhanga2,
        build_mahavagga,
        build_cullavagga,
        build_parivara,
    ]

    index = {
        "collection": "Vinaya Piṭaka",
        "description": "The Basket of Discipline",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "texts": []
    }

    total_segs = 0
    for builder in builders:
        text_data = builder()
        seg_count = len(text_data["segments"])
        total_segs += seg_count

        # Save file
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
    print(f"Total: {len(builders)} texts, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
