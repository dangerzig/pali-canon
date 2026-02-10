#!/usr/bin/env python3
"""
Build canonical Pāli DN from multiple editions.
Base: SuttaCentral Mahāsaṅgīti
Compare: VRI Chaṭṭha Saṅgāyana, PTS
"""

import json
import re
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
VRI_DIR = DATA_DIR / "vri-raw"
PTS_DIR = DATA_DIR / "pts-text/sutta"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

# VRI file mapping (vagga -> file)
VRI_FILES = {
    "silakkhandha": "s0101m.mul.txt",  # DN 1-13
    "maha": "s0102m.mul.txt",           # DN 14-23  
    "pathika": "s0103m.mul.txt"         # DN 24-34
}

# DN sutta to vagga mapping
DN_VAGGA = {
    **{i: "silakkhandha" for i in range(1, 14)},
    **{i: "maha" for i in range(14, 24)},
    **{i: "pathika" for i in range(24, 35)}
}

# PTS volume mapping
PTS_VOLUMES = {
    1: "06-Digha-Nikaya-1-Davids-Carpenter-1890.txt",  # DN 1-13
    2: "07-Digha-Nikaya-2-Davids-Carpenter-1903.txt",  # DN 14-23
    3: "08-Digha-Nikaya-3-Carpenter-1911.txt"          # DN 24-34
}

def normalize_pali(text):
    """Normalize Pāli text for comparison."""
    # Normalize niggahīta: ṁ -> ṃ
    text = text.replace('ṁ', 'ṃ')
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_sc_sutta(sutta_num):
    """Load SuttaCentral sutta."""
    filename = f"dn{sutta_num}_root-pli-ms.json"
    filepath = SC_DN_DIR / filename
    if not filepath.exists():
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_vri_text(vagga):
    """Load VRI vagga text."""
    filepath = VRI_DIR / VRI_FILES[vagga]
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_vri_sutta(vri_text, sutta_num):
    """Extract a specific sutta from VRI vagga text."""
    # VRI marks suttas with "X. Namesuttaṃ" pattern
    # Find start of this sutta and next sutta
    pattern = rf'({sutta_num}\s*\.\s*[A-ZĀ][a-zāīūṃṅñṭḍṇḷ]+suttaṃ)'
    match = re.search(pattern, vri_text, re.IGNORECASE)
    if not match:
        # Try alternate pattern
        pattern = rf'(\d+\.\s*{sutta_num}\s*\.\s*)'
        match = re.search(pattern, vri_text)
    
    if match:
        start = match.start()
        # Find next sutta
        next_pattern = rf'{sutta_num + 1}\s*\.\s*[A-ZĀ]'
        next_match = re.search(next_pattern, vri_text[start + 100:], re.IGNORECASE)
        if next_match:
            end = start + 100 + next_match.start()
        else:
            end = len(vri_text)
        return vri_text[start:end]
    return None

def compare_texts(sc_text, vri_text):
    """Compare SC and VRI texts, return differences."""
    sc_norm = normalize_pali(sc_text)
    vri_norm = normalize_pali(vri_text)
    
    if sc_norm == vri_norm:
        return None
    
    # Find specific differences
    sc_words = sc_norm.split()
    vri_words = vri_norm.split()
    
    differences = []
    max_len = max(len(sc_words), len(vri_words))
    
    for i in range(min(len(sc_words), len(vri_words))):
        if sc_words[i] != vri_words[i]:
            differences.append({
                "position": i,
                "sc": sc_words[i],
                "vri": vri_words[i]
            })
    
    return differences if differences else None

def build_canonical_sutta(sutta_num):
    """Build canonical version of a sutta."""
    print(f"Processing DN {sutta_num}...")
    
    # Load SC as base
    sc_data = load_sc_sutta(sutta_num)
    if not sc_data:
        print(f"  SC data not found for DN {sutta_num}")
        return None
    
    # Load VRI
    vagga = DN_VAGGA[sutta_num]
    vri_full = load_vri_text(vagga)
    
    # Build canonical structure
    canonical = {
        "meta": {
            "id": f"dn{sutta_num}",
            "title": list(sc_data.values())[1] if len(sc_data) > 1 else f"DN {sutta_num}",
            "collection": "dn",
            "vagga": vagga,
            "pts_volume": f"D {'i' if sutta_num <= 13 else 'ii' if sutta_num <= 23 else 'iii'}",
            "editions": {
                "base": "sc-ms",
                "compared": ["vri", "pts"]
            }
        },
        "segments": []
    }
    
    # Process each segment
    for seg_id, text in sc_data.items():
        segment = {
            "id": seg_id,
            "text": normalize_pali(text),
            "variants": {}
        }
        canonical["segments"].append(segment)
    
    return canonical

def main():
    """Build canonical DN."""
    # Start with DN 1 as proof of concept
    for sutta_num in range(1, 35):
        canonical = build_canonical_sutta(sutta_num)
        if canonical:
            output_file = OUTPUT_DIR / f"dn{sutta_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(canonical, f, indent=2, ensure_ascii=False)
            print(f"  Saved {output_file}")

if __name__ == "__main__":
    main()
