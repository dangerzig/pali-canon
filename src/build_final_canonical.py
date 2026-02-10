#!/usr/bin/env python3
"""
Build final canonical DN with all metadata.
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
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

PTS_REFS = {
    1: "D i 1–46", 2: "D i 47–86", 3: "D i 87–110",
    4: "D i 111–126", 5: "D i 127–149", 6: "D i 150–158",
    7: "D i 159–177", 8: "D i 178–203", 9: "D i 204–210",
    10: "D i 211–223", 11: "D i 224–234", 12: "D i 235–252",
    13: "D i 253–260", 14: "D ii 1–54", 15: "D ii 55–71", 
    16: "D ii 72–168", 17: "D ii 169–199", 18: "D ii 200–219",
    19: "D ii 220–262", 20: "D ii 263–274", 21: "D ii 275–289",
    22: "D ii 290–315", 23: "D ii 316–357", 24: "D iii 1–35",
    25: "D iii 36–79", 26: "D iii 80–98", 27: "D iii 99–116",
    28: "D iii 117–141", 29: "D iii 142–179", 30: "D iii 180–193",
    31: "D iii 194–206", 32: "D iii 207–224", 33: "D iii 225–271",
    34: "D iii 272–294"
}

TITLES = {
    1: ("Brahmajālasutta", "The Discourse on the All-embracing Net of Views"),
    2: ("Sāmaññaphalasutta", "The Fruits of the Contemplative Life"),
    3: ("Ambaṭṭhasutta", "The Discourse to Ambaṭṭha"),
    4: ("Soṇadaṇḍasutta", "The Discourse to Soṇadaṇḍa"),
    5: ("Kūṭadantasutta", "The Discourse to Kūṭadanta"),
    6: ("Mahālisutta", "The Discourse to Mahāli"),
    7: ("Jāliyasutta", "The Discourse to Jāliya"),
    8: ("Mahāsīhanādasutta", "The Great Discourse on the Lion's Roar"),
    9: ("Poṭṭhapādasutta", "The Discourse to Poṭṭhapāda"),
    10: ("Subhasutta", "The Discourse to Subha"),
    11: ("Kevaṭṭasutta", "The Discourse to Kevaṭṭa"),
    12: ("Lohiccasutta", "The Discourse to Lohicca"),
    13: ("Tevijjasutta", "The Discourse on the Three Knowledges"),
    14: ("Mahāpadānasutta", "The Great Discourse on the Lineage"),
    15: ("Mahānidānasutta", "The Great Discourse on Causation"),
    16: ("Mahāparinibbānasutta", "The Great Discourse on the Final Nibbāna"),
    17: ("Mahāsudassanasutta", "The Great Discourse on King Sudassana"),
    18: ("Janavasabhasutta", "The Discourse on Janavasabha"),
    19: ("Mahāgovindasutta", "The Great Discourse on Govinda"),
    20: ("Mahāsamayasutta", "The Great Discourse on the Assembly"),
    21: ("Sakkapañhasutta", "The Discourse on Sakka's Questions"),
    22: ("Mahāsatipaṭṭhānasutta", "The Great Discourse on Foundations of Mindfulness"),
    23: ("Pāyāsisutta", "The Discourse to Pāyāsi"),
    24: ("Pāṭikasutta", "The Discourse on Pāṭika"),
    25: ("Udumbarikasutta", "The Discourse at Udumbarikā's Park"),
    26: ("Cakkavattisīhanādasutta", "The Lion's Roar on the Wheel-Turning Monarch"),
    27: ("Aggaññasutta", "The Discourse on Origin"),
    28: ("Sampasādanīyasutta", "The Discourse on Serene Faith"),
    29: ("Pāsādikasutta", "The Delightful Discourse"),
    30: ("Lakkhaṇasutta", "The Discourse on Marks"),
    31: ("Siṅgālasutta", "The Discourse to Siṅgāla"),
    32: ("Āṭānāṭiyasutta", "The Discourse on Āṭānāṭiya"),
    33: ("Saṅgītisutta", "The Discourse on Reciting Together"),
    34: ("Dasuttarasutta", "The Discourse on Expanding Decades")
}

VAGGAS = {
    1: "Sīlakkhandhavagga", 2: "Sīlakkhandhavagga", 3: "Sīlakkhandhavagga",
    4: "Sīlakkhandhavagga", 5: "Sīlakkhandhavagga", 6: "Sīlakkhandhavagga",
    7: "Sīlakkhandhavagga", 8: "Sīlakkhandhavagga", 9: "Sīlakkhandhavagga",
    10: "Sīlakkhandhavagga", 11: "Sīlakkhandhavagga", 12: "Sīlakkhandhavagga",
    13: "Sīlakkhandhavagga",
    14: "Mahāvagga", 15: "Mahāvagga", 16: "Mahāvagga", 17: "Mahāvagga",
    18: "Mahāvagga", 19: "Mahāvagga", 20: "Mahāvagga", 21: "Mahāvagga",
    22: "Mahāvagga", 23: "Mahāvagga",
    24: "Pāthikavagga", 25: "Pāthikavagga", 26: "Pāthikavagga", 27: "Pāthikavagga",
    28: "Pāthikavagga", 29: "Pāthikavagga", 30: "Pāthikavagga", 31: "Pāthikavagga",
    32: "Pāthikavagga", 33: "Pāthikavagga", 34: "Pāthikavagga"
}

def build_sutta(n):
    """Build canonical sutta file."""
    filepath = SC_DN_DIR / f"dn{n}_root-pli-ms.json"
    with open(filepath, 'r', encoding='utf-8') as f:
        sc_data = json.load(f)
    
    pali_title, eng_title = TITLES.get(n, (f"DN {n}", ""))
    
    sutta = {
        "id": f"dn{n}",
        "title_pali": pali_title,
        "title_eng": eng_title,
        "collection": "dn",
        "vagga": VAGGAS[n],
        "pts": PTS_REFS[n],
        "segments": []
    }
    
    for seg_id, text in sc_data.items():
        sutta["segments"].append({
            "id": seg_id,
            "pali": normalize_pali(text)
        })
    
    return sutta

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    index = {
        "collection": "Dīgha Nikāya",
        "description": "The Long Discourses of the Buddha",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "suttas": []
    }
    
    total_segs = 0
    for n in range(1, 35):
        sutta = build_sutta(n)
        
        # Save individual sutta
        with open(OUTPUT_DIR / f"dn{n}.json", 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)
        
        seg_count = len(sutta["segments"])
        total_segs += seg_count
        
        index["suttas"].append({
            "id": sutta["id"],
            "title_pali": sutta["title_pali"],
            "title_eng": sutta["title_eng"],
            "vagga": sutta["vagga"],
            "pts": sutta["pts"],
            "segments": seg_count
        })
        
        print(f"✓ DN {n:2d}: {sutta['title_pali']:30s} ({seg_count:4d} segments) - {sutta['pts']}")
    
    index["total_segments"] = total_segs
    
    # Save index
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Total: 34 suttas, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
