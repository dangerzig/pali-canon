#!/usr/bin/env python3
"""
Fast canonical DN builder - SC base with PTS refs.
Variant comparison done separately.
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

# PTS page ranges for each sutta (approximate from standard references)
PTS_REFS = {
    1: ("D i", "1-46"), 2: ("D i", "47-86"), 3: ("D i", "87-110"),
    4: ("D i", "111-126"), 5: ("D i", "127-149"), 6: ("D i", "150-158"),
    7: ("D i", "159-177"), 8: ("D i", "178-203"), 9: ("D i", "204-210"),
    10: ("D i", "211-223"), 11: ("D i", "224-234"), 12: ("D i", "235-252"),
    13: ("D i", "253-260"),
    14: ("D ii", "1-54"), 15: ("D ii", "55-71"), 16: ("D ii", "72-168"),
    17: ("D ii", "169-199"), 18: ("D ii", "200-219"), 19: ("D ii", "220-262"),
    20: ("D ii", "263-274"), 21: ("D ii", "275-289"), 22: ("D ii", "290-315"),
    23: ("D ii", "316-357"),
    24: ("D iii", "1-35"), 25: ("D iii", "36-79"), 26: ("D iii", "80-98"),
    27: ("D iii", "99-116"), 28: ("D iii", "117-141"), 29: ("D iii", "142-179"),
    30: ("D iii", "180-193"), 31: ("D iii", "194-206"), 32: ("D iii", "207-224"),
    33: ("D iii", "225-271"), 34: ("D iii", "272-294")
}

SUTTA_TITLES = {
    1: "Brahmajālasutta", 2: "Sāmaññaphalasutta", 3: "Ambaṭṭhasutta",
    4: "Soṇadaṇḍasutta", 5: "Kūṭadantasutta", 6: "Mahālisutta",
    7: "Jāliyasutta", 8: "Mahāsīhanādasutta", 9: "Poṭṭhapādasutta",
    10: "Subhasutta", 11: "Kevaṭṭasutta", 12: "Lohiccasutta",
    13: "Tevijjasutta", 14: "Mahāpadānasutta", 15: "Mahānidānasutta",
    16: "Mahāparinibbānasutta", 17: "Mahāsudassanasutta", 18: "Janavasabhasutta",
    19: "Mahāgovindasutta", 20: "Mahāsamayasutta", 21: "Sakkapañhasutta",
    22: "Mahāsatipaṭṭhānasutta", 23: "Pāyāsisutta", 24: "Pāṭikasutta",
    25: "Udumbarikasutta", 26: "Cakkavattisīhanādasutta", 27: "Aggaññasutta",
    28: "Sampasādanīyasutta", 29: "Pāsādikasutta", 30: "Lakkhaṇasutta",
    31: "Siṅgālasutta", 32: "Āṭānāṭiyasutta", 33: "Saṅgītisutta",
    34: "Dasuttarasutta"
}

def normalize(text):
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_sutta(sutta_num):
    filepath = SC_DN_DIR / f"dn{sutta_num}_root-pli-ms.json"
    if not filepath.exists():
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sc_data = json.load(f)
    
    pts_vol, pts_pages = PTS_REFS.get(sutta_num, ("D ?", "?"))
    
    canonical = {
        "meta": {
            "id": f"dn{sutta_num}",
            "title": SUTTA_TITLES.get(sutta_num, f"DN {sutta_num}"),
            "pts_ref": f"{pts_vol} {pts_pages}",
            "segment_count": len(sc_data)
        },
        "segments": []
    }
    
    for seg_id, text in sc_data.items():
        canonical["segments"].append({
            "id": seg_id,
            "pali": normalize(text)
        })
    
    return canonical

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_stats = []
    for n in range(1, 35):
        sutta = build_sutta(n)
        if sutta:
            with open(OUTPUT_DIR / f"dn{n}.json", 'w', encoding='utf-8') as f:
                json.dump(sutta, f, indent=2, ensure_ascii=False)
            all_stats.append({
                "id": sutta["meta"]["id"],
                "title": sutta["meta"]["title"],
                "pts": sutta["meta"]["pts_ref"],
                "segments": sutta["meta"]["segment_count"]
            })
            print(f"✓ DN {n}: {sutta['meta']['title']} ({sutta['meta']['segment_count']} segments)")
    
    # Summary
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump({"suttas": all_stats, "total_segments": sum(s["segments"] for s in all_stats)}, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal: {len(all_stats)} suttas, {sum(s['segments'] for s in all_stats)} segments")

if __name__ == "__main__":
    main()
