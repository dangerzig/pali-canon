#!/usr/bin/env python3
"""
Build canonical SN (Saṃyutta Nikāya) with all metadata.
- Normalized Pāli text (SC base, ṃ for niggahīta)
- PTS page references
- Segment IDs for translation alignment
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
SC_SN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/sn"
OUTPUT_DIR = DATA_DIR / "canonical/sn"

# SN is organized into 5 main vaggas (books) containing 56 saṃyuttas
VAGGA_ASSIGNMENTS = {
    # Sagāthāvagga (SN 1-11) - "The Book with Verses"
    **{i: "Sagāthāvagga" for i in range(1, 12)},
    # Nidānavagga (SN 12-21) - "The Book of Causation"
    **{i: "Nidānavagga" for i in range(12, 22)},
    # Khandhavagga (SN 22-34) - "The Book of Aggregates"
    **{i: "Khandhavagga" for i in range(22, 35)},
    # Saḷāyatanavagga (SN 35-44) - "The Book of the Six Sense Bases"
    **{i: "Saḷāyatanavagga" for i in range(35, 45)},
    # Mahāvagga (SN 45-56) - "The Great Book"
    **{i: "Mahāvagga" for i in range(45, 57)},
}

# Saṃyutta names (Pāli and English)
SAMYUTTA_NAMES = {
    1: ("Devatāsaṃyutta", "Deities"),
    2: ("Devaputtasaṃyutta", "Sons of the Devas"),
    3: ("Kosalasaṃyutta", "King Pasenadi of Kosala"),
    4: ("Mārasaṃyutta", "Māra"),
    5: ("Bhikkhunīsaṃyutta", "Nuns"),
    6: ("Brahmasaṃyutta", "Brahmās"),
    7: ("Brāhmaṇasaṃyutta", "Brahmins"),
    8: ("Vaṅgīsasaṃyutta", "Vaṅgīsa"),
    9: ("Vanasaṃyutta", "The Forest"),
    10: ("Yakkhasaṃyutta", "Yakkhas"),
    11: ("Sakkasaṃyutta", "Sakka"),
    12: ("Nidānasaṃyutta", "Causation"),
    13: ("Abhisamayasaṃyutta", "Realization"),
    14: ("Dhātusaṃyutta", "Elements"),
    15: ("Anamataggasaṃyutta", "Without Discoverable Beginning"),
    16: ("Kassapasaṃyutta", "Kassapa"),
    17: ("Lābhasakkārasaṃyutta", "Gains and Honor"),
    18: ("Rāhulasaṃyutta", "Rāhula"),
    19: ("Lakkhaṇasaṃyutta", "Lakkhaṇa"),
    20: ("Opammasaṃyutta", "Similes"),
    21: ("Bhikkhusaṃyutta", "Monks"),
    22: ("Khandhasaṃyutta", "Aggregates"),
    23: ("Rādhasaṃyutta", "Rādha"),
    24: ("Diṭṭhisaṃyutta", "Views"),
    25: ("Okkantisaṃyutta", "Entering"),
    26: ("Uppādasaṃyutta", "Arising"),
    27: ("Kilesasaṃyutta", "Defilements"),
    28: ("Sāriputtasaṃyutta", "Sāriputta"),
    29: ("Nāgasaṃyutta", "Nāgas"),
    30: ("Supaṇṇasaṃyutta", "Supaṇṇas"),
    31: ("Gandhabbasaṃyutta", "Gandhabbas"),
    32: ("Valāhakasaṃyutta", "Cloud Devas"),
    33: ("Vacchagottasaṃyutta", "Vacchagotta"),
    34: ("Jhānasaṃyutta", "Jhāna"),
    35: ("Saḷāyatanasaṃyutta", "The Six Sense Bases"),
    36: ("Vedanāsaṃyutta", "Feeling"),
    37: ("Mātugāmasaṃyutta", "Women"),
    38: ("Jambukhādakasaṃyutta", "Jambukhādaka"),
    39: ("Sāmaṇḍakasaṃyutta", "Sāmaṇḍaka"),
    40: ("Moggallānasaṃyutta", "Moggallāna"),
    41: ("Cittasaṃyutta", "Citta"),
    42: ("Gāmaṇisaṃyutta", "Village Headmen"),
    43: ("Asaṅkhatasaṃyutta", "The Unconditioned"),
    44: ("Abyākatasaṃyutta", "The Undeclared"),
    45: ("Maggasaṃyutta", "The Path"),
    46: ("Bojjhaṅgasaṃyutta", "The Factors of Awakening"),
    47: ("Satipaṭṭhānasaṃyutta", "Mindfulness Meditation"),
    48: ("Indriyasaṃyutta", "The Faculties"),
    49: ("Sammappadhānasaṃyutta", "Right Striving"),
    50: ("Balasaṃyutta", "The Powers"),
    51: ("Iddhipādasaṃyutta", "Bases of Psychic Power"),
    52: ("Anuruddhasaṃyutta", "Anuruddha"),
    53: ("Jhānasaṃyutta", "Jhāna"),
    54: ("Ānāpānasaṃyutta", "Breathing"),
    55: ("Sotāpattisaṃyutta", "Stream-Entry"),
    56: ("Saccasaṃyutta", "The Truths"),
}

# PTS Volume references by saṃyutta (approximate)
PTS_REFS = {
    1: "S i 1–44", 2: "S i 45–53", 3: "S i 68–102", 4: "S i 103–127",
    5: "S i 128–135", 6: "S i 136–145", 7: "S i 160–184", 8: "S i 185–196",
    9: "S i 197–205", 10: "S i 206–215", 11: "S i 216–240",
    12: "S ii 1–133", 13: "S ii 133–138", 14: "S ii 140–177", 15: "S ii 178–193",
    16: "S ii 194–224", 17: "S ii 225–243", 18: "S ii 244–253", 19: "S ii 254–262",
    20: "S ii 262–270", 21: "S ii 273–284",
    22: "S iii 1–188", 23: "S iii 188–201", 24: "S iii 202–224", 25: "S iii 225–228",
    26: "S iii 228–231", 27: "S iii 232–234", 28: "S iii 235–238", 29: "S iii 240–242",
    30: "S iii 246–248", 31: "S iii 249–251", 32: "S iii 254–257", 33: "S iii 258–263",
    34: "S iii 263–278",
    35: "S iv 1–204", 36: "S iv 204–237", 37: "S iv 238–248", 38: "S iv 251–261",
    39: "S iv 261–262", 40: "S iv 262–280", 41: "S iv 281–304", 42: "S iv 305–330",
    43: "S iv 359–373", 44: "S iv 374–403",
    45: "S v 1–62", 46: "S v 62–140", 47: "S v 141–192", 48: "S v 193–252",
    49: "S v 244–245", 50: "S v 249–250", 51: "S v 254–293", 52: "S v 294–306",
    53: "S v 307–312", 54: "S v 311–341", 55: "S v 342–409", 56: "S v 414–478",
}

def get_sutta_number(filename):
    """Extract sutta number from filename.
    Handles both: sn1.23_root-pli-ms.json -> (1, 23, None)
    And ranges: sn49.1-12_root-pli-ms.json -> (49, 1, 12)
    """
    # Try range pattern first (e.g., sn49.1-12)
    match = re.match(r'sn(\d+)\.(\d+)-(\d+)_root-pli-ms\.json', filename)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # Try single sutta pattern (e.g., sn1.23)
    match = re.match(r'sn(\d+)\.(\d+)_root-pli-ms\.json', filename)
    if match:
        return int(match.group(1)), int(match.group(2)), None
    return None, None, None

def build_samyutta(samyutta_num):
    """Build all suttas for a saṃyutta."""
    samyutta_dir = SC_SN_DIR / f"sn{samyutta_num}"
    if not samyutta_dir.exists():
        return None

    pali_name, eng_name = SAMYUTTA_NAMES.get(samyutta_num, (f"Saṃyutta {samyutta_num}", ""))

    samyutta = {
        "id": f"sn{samyutta_num}",
        "name_pali": pali_name,
        "name_eng": eng_name,
        "vagga": VAGGA_ASSIGNMENTS[samyutta_num],
        "pts": PTS_REFS.get(samyutta_num, ""),
        "suttas": []
    }

    # Get all sutta files and sort by sutta number
    sutta_files = list(samyutta_dir.glob("sn*.json"))
    sutta_files_sorted = []
    for f in sutta_files:
        sam_num, sutta_start, sutta_end = get_sutta_number(f.name)
        if sutta_start is not None:
            sutta_files_sorted.append((sutta_start, sutta_end, f))
    sutta_files_sorted.sort(key=lambda x: x[0])

    for sutta_start, sutta_end, filepath in sutta_files_sorted:
        with open(filepath, 'r', encoding='utf-8') as f:
            sc_data = json.load(f)

        # Handle range files (e.g., sn49.1-12) vs single suttas (e.g., sn1.1)
        if sutta_end is not None:
            sutta_id = f"sn{samyutta_num}.{sutta_start}-{sutta_end}"
        else:
            sutta_id = f"sn{samyutta_num}.{sutta_start}"

        sutta = {
            "id": sutta_id,
            "segments": []
        }

        for seg_id, text in sc_data.items():
            sutta["segments"].append({
                "id": seg_id,
                "pali": normalize_pali(text)
            })

        samyutta["suttas"].append(sutta)

    return samyutta

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "collection": "Saṃyutta Nikāya",
        "description": "The Connected Discourses of the Buddha",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "vaggas": [
            {"name": "Sagāthāvagga", "range": "SN 1-11", "description": "The Book with Verses"},
            {"name": "Nidānavagga", "range": "SN 12-21", "description": "The Book of Causation"},
            {"name": "Khandhavagga", "range": "SN 22-34", "description": "The Book of Aggregates"},
            {"name": "Saḷāyatanavagga", "range": "SN 35-44", "description": "The Book of the Six Sense Bases"},
            {"name": "Mahāvagga", "range": "SN 45-56", "description": "The Great Book"},
        ],
        "samyuttas": []
    }

    total_suttas = 0
    total_segs = 0

    for samyutta_num in range(1, 57):
        samyutta = build_samyutta(samyutta_num)
        if samyutta is None:
            continue

        # Save individual saṃyutta file
        with open(OUTPUT_DIR / f"sn{samyutta_num}.json", 'w', encoding='utf-8') as f:
            json.dump(samyutta, f, indent=2, ensure_ascii=False)

        sutta_count = len(samyutta["suttas"])
        seg_count = sum(len(s["segments"]) for s in samyutta["suttas"])
        total_suttas += sutta_count
        total_segs += seg_count

        index["samyuttas"].append({
            "id": samyutta["id"],
            "name_pali": samyutta["name_pali"],
            "name_eng": samyutta["name_eng"],
            "vagga": samyutta["vagga"],
            "pts": samyutta["pts"],
            "suttas": sutta_count,
            "segments": seg_count
        })

        print(f"SN {samyutta_num:2d}: {samyutta['name_pali']:30s} ({sutta_count:3d} suttas, {seg_count:5d} segments)")

    index["total_suttas"] = total_suttas
    index["total_segments"] = total_segs

    # Save index
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Total: 56 saṃyuttas, {total_suttas:,} suttas, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
