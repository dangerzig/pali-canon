#!/usr/bin/env python3
"""
Build canonical KN (Khuddaka Nikāya) with all metadata.
- Normalized Pāli text (SC base, ṃ for niggahīta)
- Segment IDs for translation alignment
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SC_KN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/kn"
OUTPUT_DIR = DATA_DIR / "canonical/kn"

# KN text metadata (abbreviation, Pāli name, English name)
KN_TEXTS = {
    "kp": ("Khuddakapāṭha", "The Short Passages"),
    "dhp": ("Dhammapada", "Verses on the Dhamma"),
    "ud": ("Udāna", "Inspired Utterances"),
    "iti": ("Itivuttaka", "As It Was Said"),
    "snp": ("Suttanipāta", "The Group of Discourses"),
    "vv": ("Vimānavatthu", "Stories of Celestial Mansions"),
    "pv": ("Petavatthu", "Stories of Ghosts"),
    "thag": ("Theragāthā", "Verses of the Elder Monks"),
    "thig": ("Therīgāthā", "Verses of the Elder Nuns"),
    "ja": ("Jātaka", "Birth Stories"),
    "mnd": ("Mahāniddesa", "The Great Exposition"),
    "cnd": ("Cūḷaniddesa", "The Minor Exposition"),
    "ps": ("Paṭisambhidāmagga", "The Path of Discrimination"),
    "tha-ap": ("Therāpadāna", "Legends of the Elder Monks"),
    "thi-ap": ("Therīapadāna", "Legends of the Elder Nuns"),
    "bv": ("Buddhavaṃsa", "The Chronicle of Buddhas"),
    "cp": ("Cariyāpiṭaka", "The Basket of Conduct"),
    "ne": ("Nettippakaraṇa", "The Guide"),
    "pe": ("Peṭakopadesa", "Instruction on the Piṭaka"),
    "mil": ("Milindapañha", "The Questions of King Milinda"),
}

def normalize_pali(text):
    """Normalize Pāli text."""
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_sort_key(filename, prefix):
    """Extract sort key from filename for proper ordering."""
    # Remove prefix and suffix
    name = filename.replace(f'{prefix}', '').replace('_root-pli-ms.json', '')

    # Handle range patterns like "1-20" or "100-115"
    range_match = re.match(r'(\d+)-(\d+)', name)
    if range_match:
        return (int(range_match.group(1)), int(range_match.group(2)))

    # Handle dotted patterns like "1.1" or "10.23"
    dot_match = re.match(r'(\d+)\.(\d+)', name)
    if dot_match:
        return (int(dot_match.group(1)), int(dot_match.group(2)))

    # Handle simple numbers
    num_match = re.match(r'(\d+)', name)
    if num_match:
        return (int(num_match.group(1)), 0)

    return (0, 0)

def build_text(text_abbrev):
    """Build canonical file for a KN text."""
    text_dir = SC_KN_DIR / text_abbrev
    if not text_dir.exists():
        return None

    pali_name, eng_name = KN_TEXTS.get(text_abbrev, (text_abbrev.upper(), ""))

    text_data = {
        "id": text_abbrev,
        "name_pali": pali_name,
        "name_eng": eng_name,
        "collection": "kn",
        "items": []
    }

    # Collect all JSON files (handling nested directories like snp/vagga1/)
    all_files = []
    for json_file in text_dir.rglob(f"{text_abbrev}*.json"):
        all_files.append(json_file)

    # Sort files by extracted numbers
    all_files.sort(key=lambda f: get_sort_key(f.name, text_abbrev))

    for filepath in all_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            sc_data = json.load(f)

        # Extract ID from filename
        item_id = filepath.stem.replace('_root-pli-ms', '')

        item = {
            "id": item_id,
            "segments": []
        }

        for seg_id, text in sc_data.items():
            item["segments"].append({
                "id": seg_id,
                "pali": normalize_pali(text)
            })

        text_data["items"].append(item)

    return text_data

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "collection": "Khuddaka Nikāya",
        "description": "The Minor Collection",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "texts": []
    }

    total_items = 0
    total_segs = 0

    # Process texts in traditional order
    text_order = ["kp", "dhp", "ud", "iti", "snp", "vv", "pv", "thag", "thig",
                  "ja", "mnd", "cnd", "ps", "tha-ap", "thi-ap", "bv", "cp", "ne", "pe", "mil"]

    for text_abbrev in text_order:
        text_data = build_text(text_abbrev)
        if text_data is None:
            continue

        # Save individual text file
        with open(OUTPUT_DIR / f"{text_abbrev}.json", 'w', encoding='utf-8') as f:
            json.dump(text_data, f, indent=2, ensure_ascii=False)

        item_count = len(text_data["items"])
        seg_count = sum(len(item["segments"]) for item in text_data["items"])
        total_items += item_count
        total_segs += seg_count

        index["texts"].append({
            "id": text_data["id"],
            "name_pali": text_data["name_pali"],
            "name_eng": text_data["name_eng"],
            "items": item_count,
            "segments": seg_count
        })

        print(f"{text_abbrev:8s}: {text_data['name_pali']:25s} ({item_count:4d} items, {seg_count:6d} segments)")

    index["total_items"] = total_items
    index["total_segments"] = total_segs

    # Save index
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Total: {len(text_order)} texts, {total_items:,} items, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
