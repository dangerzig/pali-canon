#!/usr/bin/env python3
"""
Build canonical Pāli DN with actual variant comparison.
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
VRI_DIR = DATA_DIR / "vri-raw"
PTS_DIR = DATA_DIR / "pts-text/sutta"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

VRI_FILES = {
    "silakkhandha": "s0101m.mul.txt",
    "maha": "s0102m.mul.txt",
    "pathika": "s0103m.mul.txt"
}

DN_VAGGA = {
    **{i: "silakkhandha" for i in range(1, 14)},
    **{i: "maha" for i in range(14, 24)},
    **{i: "pathika" for i in range(24, 35)}
}

def normalize(text):
    """Normalize for comparison."""
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'[\s\u00a0]+', ' ', text).strip()
    return text

def load_sc_sutta(sutta_num):
    """Load SC sutta."""
    filepath = SC_DN_DIR / f"dn{sutta_num}_root-pli-ms.json"
    if not filepath.exists():
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_vri_vagga(vagga):
    """Load VRI vagga."""
    filepath = VRI_DIR / VRI_FILES[vagga]
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def find_vri_match(sc_text, vri_text, context_size=200):
    """Find the best match for SC text in VRI."""
    sc_norm = normalize(sc_text)
    
    # Try to find exact match first
    if sc_norm in normalize(vri_text):
        return {"match": "exact", "vri_text": sc_text}
    
    # Try finding with first few words
    words = sc_norm.split()[:5]
    search_text = ' '.join(words)
    
    vri_norm = normalize(vri_text)
    pos = vri_norm.find(search_text)
    
    if pos != -1:
        # Extract corresponding VRI segment
        end_pos = pos + len(sc_norm) + 50
        vri_segment = vri_norm[pos:end_pos]
        
        # Check similarity
        ratio = SequenceMatcher(None, sc_norm, vri_segment[:len(sc_norm)]).ratio()
        
        if ratio > 0.95:
            return {"match": "high", "ratio": ratio}
        elif ratio > 0.8:
            return {"match": "medium", "ratio": ratio, "vri_snippet": vri_segment[:100]}
        else:
            return {"match": "low", "ratio": ratio, "vri_snippet": vri_segment[:100]}
    
    return {"match": "none"}

def build_canonical_sutta(sutta_num, vri_cache):
    """Build canonical sutta with variant tracking."""
    sc_data = load_sc_sutta(sutta_num)
    if not sc_data:
        return None
    
    vagga = DN_VAGGA[sutta_num]
    if vagga not in vri_cache:
        vri_cache[vagga] = load_vri_vagga(vagga)
    vri_text = vri_cache[vagga]
    
    # Get title from second segment typically
    title = "Unknown"
    for seg_id, text in list(sc_data.items())[:5]:
        if "sutta" in text.lower():
            title = text
            break
    
    canonical = {
        "meta": {
            "id": f"dn{sutta_num}",
            "title": title,
            "collection": "dn",
            "vagga": vagga,
            "pts_ref": f"D {'i' if sutta_num <= 13 else 'ii' if sutta_num <= 23 else 'iii'}",
            "stats": {
                "segments": len(sc_data),
                "exact_matches": 0,
                "high_matches": 0,
                "variants": 0
            }
        },
        "segments": []
    }
    
    for seg_id, text in sc_data.items():
        normalized_text = normalize(text)
        
        # Compare with VRI
        match_result = find_vri_match(text, vri_text)
        
        segment = {
            "id": seg_id,
            "text": normalized_text
        }
        
        if match_result["match"] == "exact" or match_result.get("ratio", 0) > 0.99:
            canonical["meta"]["stats"]["exact_matches"] += 1
        elif match_result["match"] == "high":
            canonical["meta"]["stats"]["high_matches"] += 1
        elif match_result["match"] in ["medium", "low"]:
            canonical["meta"]["stats"]["variants"] += 1
            segment["vri_match"] = match_result
        
        canonical["segments"].append(segment)
    
    return canonical

def main():
    vri_cache = {}
    stats_summary = []
    
    for sutta_num in range(1, 35):
        print(f"Processing DN {sutta_num}...", end=" ")
        canonical = build_canonical_sutta(sutta_num, vri_cache)
        
        if canonical:
            output_file = OUTPUT_DIR / f"dn{sutta_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(canonical, f, indent=2, ensure_ascii=False)
            
            stats = canonical["meta"]["stats"]
            print(f"✓ {stats['segments']} segs, {stats['exact_matches']} exact, {stats['variants']} variants")
            stats_summary.append({
                "sutta": f"dn{sutta_num}",
                **stats
            })
    
    # Save summary
    with open(OUTPUT_DIR / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print("\nSaved summary to _summary.json")

if __name__ == "__main__":
    main()
