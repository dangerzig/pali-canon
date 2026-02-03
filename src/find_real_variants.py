#!/usr/bin/env python3
"""
Find REAL textual variants between SC and VRI.
Ignores: punctuation, spacing, niggahīta forms, header formatting.
"""

import json
import re
from pathlib import Path

DATA_DIR = Path("/Users/danzigmond/pali/data")
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

def deep_normalize(text):
    """Aggressive normalization for comparison."""
    text = text.lower()
    # Normalize niggahīta and final nasals
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'n\b', 'ṃ', text)  # final -n to -ṃ
    # Remove punctuation and numbers
    text = re.sub(r'[.,;:!?\'\"—–\-\d()]', ' ', text)
    # Normalize spacing
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_vri_dn():
    """Load and concatenate all VRI DN text."""
    texts = []
    for filename in ["s0101m.mul.txt", "s0102m.mul.txt", "s0103m.mul.txt"]:
        with open(VRI_DIR / filename, 'r', encoding='utf-8') as f:
            texts.append(f.read())
    return deep_normalize(' '.join(texts))

def find_segment_in_vri(segment_text, vri_text, min_words=4):
    """Try to find a segment in VRI text."""
    seg_norm = deep_normalize(segment_text)
    words = seg_norm.split()
    
    if len(words) < min_words:
        return None  # Skip short segments (headers, etc.)
    
    # Try finding with first N words
    for n in [6, 5, 4, 3]:
        if len(words) >= n:
            search = ' '.join(words[:n])
            if search in vri_text:
                return "found"
    
    return "not_found"

def compare_suttas():
    """Compare SC segments against VRI."""
    print("Loading VRI DN text...")
    vri_text = load_vri_dn()
    print(f"VRI text: {len(vri_text)} characters")
    
    results = {}
    
    for n in range(1, 35):
        with open(SC_DN_DIR / f"dn{n}_root-pli-ms.json") as f:
            sc_data = json.load(f)
        
        found = 0
        not_found = []
        skipped = 0
        
        for seg_id, text in sc_data.items():
            result = find_segment_in_vri(text, vri_text)
            if result == "found":
                found += 1
            elif result == "not_found":
                not_found.append({"id": seg_id, "text": text[:80]})
            else:
                skipped += 1
        
        total = len(sc_data)
        match_pct = found / (total - skipped) * 100 if (total - skipped) > 0 else 0
        
        results[f"dn{n}"] = {
            "total": total,
            "found": found,
            "not_found": len(not_found),
            "skipped": skipped,
            "match_pct": round(match_pct, 1),
            "missing_samples": not_found[:5]  # First 5 samples
        }
        
        status = "✓" if match_pct > 95 else "⚠" if match_pct > 80 else "✗"
        print(f"DN {n:2d}: {status} {match_pct:5.1f}% match ({found}/{total-skipped} segments)")
    
    # Save detailed report
    with open(OUTPUT_DIR / "_comparison.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nSaved comparison report to _comparison.json")

if __name__ == "__main__":
    compare_suttas()
