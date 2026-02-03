#!/usr/bin/env python3
"""
Find variants between SC and VRI editions.
Uses efficient text chunking and comparison.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("/Users/danzigmond/pali/data")
SC_DN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/dn"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "canonical/dn"

VRI_FILES = ["s0101m.mul.txt", "s0102m.mul.txt", "s0103m.mul.txt"]

def normalize(text):
    """Normalize for comparison."""
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'[''""\"\'«»]', '', text)
    text = re.sub(r'[\s\u00a0]+', ' ', text).strip()
    return text.lower()

def get_words(text):
    """Extract words from text."""
    return re.findall(r'[a-zāīūṃṅñṭḍṇḷ]+', normalize(text))

def load_vri_words():
    """Load all VRI words into a set for quick lookup."""
    all_words = set()
    for filename in VRI_FILES:
        filepath = VRI_DIR / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        words = get_words(text)
        all_words.update(words)
    print(f"VRI vocabulary: {len(all_words)} unique words")
    return all_words

def find_unknown_words(sc_data, vri_words):
    """Find SC words not in VRI."""
    unknown = []
    for seg_id, text in sc_data.items():
        sc_words = get_words(text)
        for word in sc_words:
            if word not in vri_words and len(word) > 2:
                unknown.append((seg_id, word))
    return unknown

def compare_dn():
    """Compare all DN suttas."""
    vri_words = load_vri_words()
    
    variants = defaultdict(list)
    
    for n in range(1, 35):
        filepath = SC_DN_DIR / f"dn{n}_root-pli-ms.json"
        with open(filepath, 'r', encoding='utf-8') as f:
            sc_data = json.load(f)
        
        unknown = find_unknown_words(sc_data, vri_words)
        if unknown:
            variants[f"dn{n}"] = unknown
            print(f"DN {n}: {len(unknown)} potential variants")
        else:
            print(f"DN {n}: ✓ all words match")
    
    # Save variants report
    report = {
        "summary": {
            "suttas_with_variants": len(variants),
            "total_potential_variants": sum(len(v) for v in variants.values())
        },
        "details": {k: [{"segment": s, "word": w} for s, w in v] for k, v in variants.items()}
    }
    
    with open(OUTPUT_DIR / "_variants.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved variants report: {report['summary']}")

if __name__ == "__main__":
    compare_dn()
