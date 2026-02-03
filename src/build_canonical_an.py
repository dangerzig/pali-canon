#!/usr/bin/env python3
"""
Build canonical AN (Aṅguttara Nikāya) with all metadata.
- Normalized Pāli text (SC base, ṃ for niggahīta)
- PTS page references
- Segment IDs for translation alignment
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SC_AN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/an"
OUTPUT_DIR = DATA_DIR / "canonical/an"

# Nipāta names (Pāli and English)
NIPATA_NAMES = {
    1: ("Ekakanipāta", "The Book of Ones"),
    2: ("Dukanipāta", "The Book of Twos"),
    3: ("Tikanipāta", "The Book of Threes"),
    4: ("Catukkanipāta", "The Book of Fours"),
    5: ("Pañcakanipāta", "The Book of Fives"),
    6: ("Chakkanipāta", "The Book of Sixes"),
    7: ("Sattakanipāta", "The Book of Sevens"),
    8: ("Aṭṭhakanipāta", "The Book of Eights"),
    9: ("Navakanipāta", "The Book of Nines"),
    10: ("Dasakanipāta", "The Book of Tens"),
    11: ("Ekādasakanipāta", "The Book of Elevens"),
}

# PTS Volume references by nipāta (approximate)
PTS_REFS = {
    1: "A i 1–46",
    2: "A i 47–100",
    3: "A i 101–299",
    4: "A ii 1–241",
    5: "A iii 1–278",
    6: "A iii 279–452",
    7: "A iv 1–149",
    8: "A iv 150–350",
    9: "A iv 351–465",
    10: "A v 1–310",
    11: "A v 311–362",
}

def normalize_pali(text):
    """Normalize Pāli text."""
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_sutta_info(filename):
    """Extract sutta info from filename.
    Handles both: an10.23_root-pli-ms.json -> (10, 23, None)
    And ranges: an1.1-10_root-pli-ms.json -> (1, 1, 10)
    """
    # Try range pattern first (e.g., an1.1-10)
    match = re.match(r'an(\d+)\.(\d+)-(\d+)_root-pli-ms\.json', filename)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # Try single sutta pattern (e.g., an10.23)
    match = re.match(r'an(\d+)\.(\d+)_root-pli-ms\.json', filename)
    if match:
        return int(match.group(1)), int(match.group(2)), None
    return None, None, None

def build_nipata(nipata_num):
    """Build all suttas for a nipāta."""
    nipata_dir = SC_AN_DIR / f"an{nipata_num}"
    if not nipata_dir.exists():
        return None

    pali_name, eng_name = NIPATA_NAMES.get(nipata_num, (f"Nipāta {nipata_num}", ""))

    nipata = {
        "id": f"an{nipata_num}",
        "name_pali": pali_name,
        "name_eng": eng_name,
        "pts": PTS_REFS.get(nipata_num, ""),
        "suttas": []
    }

    # Get all sutta files and sort by sutta number
    sutta_files = list(nipata_dir.glob("an*.json"))
    sutta_files_sorted = []
    for f in sutta_files:
        nip_num, sutta_start, sutta_end = get_sutta_info(f.name)
        if sutta_start is not None:
            sutta_files_sorted.append((sutta_start, sutta_end, f))
    sutta_files_sorted.sort(key=lambda x: x[0])

    for sutta_start, sutta_end, filepath in sutta_files_sorted:
        with open(filepath, 'r', encoding='utf-8') as f:
            sc_data = json.load(f)

        # Handle range files (e.g., an1.1-10) vs single suttas (e.g., an10.23)
        if sutta_end is not None:
            sutta_id = f"an{nipata_num}.{sutta_start}-{sutta_end}"
        else:
            sutta_id = f"an{nipata_num}.{sutta_start}"

        sutta = {
            "id": sutta_id,
            "segments": []
        }

        for seg_id, text in sc_data.items():
            sutta["segments"].append({
                "id": seg_id,
                "pali": normalize_pali(text)
            })

        nipata["suttas"].append(sutta)

    return nipata

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "collection": "Aṅguttara Nikāya",
        "description": "The Numerical Discourses of the Buddha",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "nipatas": []
    }

    total_suttas = 0
    total_segs = 0

    for nipata_num in range(1, 12):
        nipata = build_nipata(nipata_num)
        if nipata is None:
            continue

        # Save individual nipāta file
        with open(OUTPUT_DIR / f"an{nipata_num}.json", 'w', encoding='utf-8') as f:
            json.dump(nipata, f, indent=2, ensure_ascii=False)

        sutta_count = len(nipata["suttas"])
        seg_count = sum(len(s["segments"]) for s in nipata["suttas"])
        total_suttas += sutta_count
        total_segs += seg_count

        index["nipatas"].append({
            "id": nipata["id"],
            "name_pali": nipata["name_pali"],
            "name_eng": nipata["name_eng"],
            "pts": nipata["pts"],
            "suttas": sutta_count,
            "segments": seg_count
        })

        print(f"AN {nipata_num:2d}: {nipata['name_pali']:20s} ({sutta_count:3d} suttas, {seg_count:5d} segments)")

    index["total_suttas"] = total_suttas
    index["total_segments"] = total_segs

    # Save index
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Total: 11 nipātas, {total_suttas:,} suttas, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
