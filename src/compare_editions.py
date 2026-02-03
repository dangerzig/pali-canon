#!/usr/bin/env python3
"""Compare Pāli text across editions."""
import json
import re
import sys

def normalize(text):
    """Normalize text for comparison."""
    # Remove punctuation and extra whitespace
    text = re.sub(r'[.,;:!?\-–—\'\"()\[\]{}]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    # Normalize niggahīta: ṁ and ṃ -> ṃ
    text = text.replace('ṁ', 'ṃ')
    return text

def tokenize(text):
    """Split into words."""
    return normalize(text).split()

def compare_texts(sc_text, vri_text, pts_text):
    """Compare three texts and find differences."""
    sc_words = tokenize(sc_text)
    vri_words = tokenize(vri_text)
    pts_words = tokenize(pts_text)
    
    differences = []
    
    # Simple word-by-word comparison (first N words)
    max_len = min(len(sc_words), len(vri_words), len(pts_words), 50)
    
    for i in range(max_len):
        sc_w = sc_words[i] if i < len(sc_words) else ""
        vri_w = vri_words[i] if i < len(vri_words) else ""
        pts_w = pts_words[i] if i < len(pts_words) else ""
        
        # Check if all three match
        if not (sc_w == vri_w == pts_w):
            differences.append({
                'position': i,
                'sc': sc_w,
                'vri': vri_w,
                'pts': pts_w
            })
    
    return differences

# Test with sample texts
sc_text = """Evaṁ me sutaṁ—
ekaṁ samayaṁ bhagavā antarā ca rājagahaṁ antarā ca nāḷandaṁ addhānamaggappaṭipanno hoti mahatā bhikkhusaṅghena saddhiṁ pañcamattehi bhikkhusatehi."""

vri_text = """Evaṃ me sutaṃ – ekaṃ samayaṃ bhagavā antarā ca rājagahaṃ antarā ca nāḷandaṃ addhānamaggappaṭipanno hoti mahatā bhikkhusaṅghena saddhiṃ pañcamattehi bhikkhusatehi."""

pts_text = """Evam me sutam. Ekam samayam Bhagava antara ca Rajagaham antara ca Nalandam addhana-magga-patipanno hoti mahata bhikkhu-samghena saddhim panca-mattehi bhikkhu-satehi."""

diffs = compare_texts(sc_text, vri_text, pts_text)

print("Differences found (first 50 words):")
print("-" * 60)
for d in diffs:
    print(f"Word {d['position']:2d}: SC={d['sc']:25s} VRI={d['vri']:25s} PTS={d['pts']}")
