#!/usr/bin/env python3
"""
Compare PTS and SC texts to identify variants.

This script compares the extracted PTS text with SC canonical text
to find textual differences (not just formatting differences).
"""

import re
import json
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
SC_DIR = DATA_DIR / "canonical/dn"
PTS_DIR = DATA_DIR / "pts-parsed/dn"


def tokenize(text: str) -> list:
    """Tokenize Pāli text into words."""
    # Normalize
    text = text.lower()
    text = text.replace('ṁ', 'ṃ')
    text = text.replace('ŋ', 'ṃ')

    # Extract words (Pāli characters only)
    pattern = r'[a-zāīūṭḍṇṅñṃḷ]+'
    return re.findall(pattern, text)


def get_word_freq(text: str) -> Counter:
    """Get word frequency from text."""
    words = tokenize(text)
    return Counter(words)


def compare_sutta(sutta_num: int) -> dict:
    """Compare PTS and SC versions of a sutta."""
    sc_file = SC_DIR / f"dn{sutta_num}.json"
    pts_file = PTS_DIR / f"dn{sutta_num}.json"

    if not sc_file.exists() or not pts_file.exists():
        return None

    # Load texts
    sc_data = json.loads(sc_file.read_text())
    pts_data = json.loads(pts_file.read_text())

    # Get SC text
    sc_text = ' '.join(seg.get('pali', '') for seg in sc_data.get('segments', []))

    # Get PTS text
    pts_text = pts_data.get('text', '')

    # Tokenize
    sc_words = tokenize(sc_text)
    pts_words = tokenize(pts_text)

    # Word frequencies
    sc_freq = Counter(sc_words)
    pts_freq = Counter(pts_words)

    # Find words unique to each
    sc_only = set(sc_freq.keys()) - set(pts_freq.keys())
    pts_only = set(pts_freq.keys()) - set(sc_freq.keys())

    # Find words with different frequencies
    common_words = set(sc_freq.keys()) & set(pts_freq.keys())
    freq_diff = {}
    for word in common_words:
        sc_count = sc_freq[word]
        pts_count = pts_freq[word]
        if abs(sc_count - pts_count) > max(1, min(sc_count, pts_count) * 0.2):
            freq_diff[word] = (sc_count, pts_count)

    return {
        'sutta': sutta_num,
        'sc_words': len(sc_words),
        'pts_words': len(pts_words),
        'sc_unique_forms': len(sc_freq),
        'pts_unique_forms': len(pts_freq),
        'sc_only_words': sorted(sc_only)[:20],  # Top 20
        'pts_only_words': sorted(pts_only)[:20],
        'freq_differences': dict(sorted(freq_diff.items(),
                                       key=lambda x: abs(x[1][0] - x[1][1]),
                                       reverse=True)[:20])
    }


def main():
    print("=" * 70)
    print("Comparing PTS and SC Dīgha Nikāya texts")
    print("=" * 70)

    all_results = []

    for sutta_num in range(1, 35):
        result = compare_sutta(sutta_num)
        if result:
            all_results.append(result)

            sc_words = result['sc_words']
            pts_words = result['pts_words']
            ratio = pts_words / sc_words if sc_words > 0 else 0

            flag = ""
            if ratio > 1.5 or ratio < 0.7:
                flag = " *"

            print(f"DN {sutta_num:2d}: SC={sc_words:>7,} PTS={pts_words:>7,} "
                  f"ratio={ratio:.2f} unique: SC={len(result['sc_only_words'])}, "
                  f"PTS={len(result['pts_only_words'])}{flag}")

    # Summary
    print()
    print("-" * 70)
    print("Words unique to SC (sample from DN 1):")
    if all_results:
        dn1 = all_results[0]
        for word in dn1['sc_only_words'][:10]:
            print(f"  {word}")

    print()
    print("Words unique to PTS (sample from DN 1):")
    if all_results:
        for word in dn1['pts_only_words'][:10]:
            print(f"  {word}")

    # Save results
    output_file = DATA_DIR / "pts-parsed/dn/_comparison.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print()
    print(f"Full comparison saved to: {output_file}")


if __name__ == "__main__":
    main()
