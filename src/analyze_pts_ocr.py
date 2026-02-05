#!/usr/bin/env python3
"""
Analyze OCR quality of PTS Dīgha Nikāya texts.

This script examines the parsed PTS text to identify:
1. OCR-specific errors (missing diacritics, ligature issues)
2. Word fragments from broken text
3. Quality metrics per sutta
"""

import re
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"
PTS_DIR = DATA_DIR / "pts-parsed/dn"
SC_DIR = DATA_DIR / "canonical/dn"


def analyze_diacritic_issues(text: str) -> dict:
    """Find words that likely have missing diacritics."""
    # Pattern for Pāli words without diacritics
    words_no_diacritics = re.findall(r'\b[a-z]{4,}\b', text.lower())

    # Pattern for Pāli words with diacritics
    words_with_diacritics = re.findall(r'\b[a-zāīūṭḍṇṅñṃḷ]*[āīūṭḍṇṅñṃḷ][a-zāīūṭḍṇṅñṃḷ]*\b', text.lower())

    # Ratio indicates quality - high ratio of non-diacritic words = poor OCR
    total_words = len(words_no_diacritics) + len(words_with_diacritics)
    if total_words == 0:
        return {'ratio': 0, 'no_diacritics': 0, 'with_diacritics': 0}

    return {
        'no_diacritics': len(words_no_diacritics),
        'with_diacritics': len(words_with_diacritics),
        'ratio': len(words_no_diacritics) / total_words
    }


def find_ligature_errors(text: str) -> list:
    """Find fi/fl ligature OCR errors."""
    # Common ligature errors: ñ → fi, ā → ā, etc.
    errors = []

    # fi/fl ligature issues
    fi_matches = re.findall(r'\b\w*fi\w*\b', text.lower())
    fl_matches = re.findall(r'\b\w*fl\w*\b', text.lower())

    # These are likely OCR errors in Pāli text
    for word in fi_matches:
        if 'fi' in word and not word.startswith('fi'):  # fi inside word is suspicious
            errors.append(('fi-ligature', word))

    return errors


def find_word_fragments(text: str) -> list:
    """Find short word fragments that are likely OCR errors."""
    words = re.findall(r'\b[a-zāīūṭḍṇṅñṃḷ]+\b', text.lower())

    # Very short "words" are often fragments
    fragments = [w for w in words if len(w) <= 2 and w not in ('a', 'ca', 'na', 'va', 'sa', 'pi', 'ti', 'te', 'ye', 'me', 'no', 'so', 'ko', 'tu', 'ya', 'ta', 'ma', 'pa')]

    return Counter(fragments).most_common(20)


def find_garbage_text(text: str) -> list:
    """Find lines with obvious OCR garbage."""
    garbage = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Lines with mostly non-alphabetic characters
        if len(line) > 5:
            alpha_ratio = sum(c.isalpha() for c in line) / len(line)
            if alpha_ratio < 0.5:
                garbage.append((i, line[:80]))

        # Lines with repeated characters
        if re.search(r'(.)\1{4,}', line):
            garbage.append((i, line[:80]))

    return garbage[:20]


def analyze_sutta(sutta_num: int) -> dict:
    """Analyze OCR quality for a single sutta."""
    pts_file = PTS_DIR / f"dn{sutta_num}.json"
    sc_file = SC_DIR / f"dn{sutta_num}.json"

    if not pts_file.exists():
        return None

    pts_data = json.loads(pts_file.read_text())
    pts_text = pts_data.get('text', '')

    # Get SC word count for comparison
    sc_words = 0
    if sc_file.exists():
        sc_data = json.loads(sc_file.read_text())
        sc_text = ' '.join(seg.get('pali', '') for seg in sc_data.get('segments', []))
        sc_words = len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', sc_text.lower()))

    # PTS word count
    pts_words = len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', pts_text.lower()))

    # Analyze quality issues
    diacritic_analysis = analyze_diacritic_issues(pts_text)
    ligature_errors = find_ligature_errors(pts_text)
    fragments = find_word_fragments(pts_text)
    garbage = find_garbage_text(pts_text)

    # Quality score (0-100, higher is better)
    # Penalize: high no-diacritic ratio, ligature errors, fragments, garbage
    quality_score = 100
    quality_score -= diacritic_analysis['ratio'] * 30  # Up to -30 for no diacritics
    quality_score -= min(len(ligature_errors) * 2, 20)  # Up to -20 for ligatures
    quality_score -= min(len(fragments) * 0.5, 15)  # Up to -15 for fragments
    quality_score -= min(len(garbage) * 1, 15)  # Up to -15 for garbage

    # Penalize word count mismatch
    if sc_words > 0:
        ratio = pts_words / sc_words
        if ratio > 1.5:
            quality_score -= min((ratio - 1.5) * 20, 20)
        elif ratio < 0.7:
            quality_score -= min((0.7 - ratio) * 40, 20)

    return {
        'sutta': sutta_num,
        'pts_words': pts_words,
        'sc_words': sc_words,
        'word_ratio': round(pts_words / sc_words, 2) if sc_words > 0 else 0,
        'diacritic_ratio': round(diacritic_analysis['ratio'], 3),
        'ligature_errors': len(ligature_errors),
        'fragment_count': sum(c for _, c in fragments),
        'garbage_lines': len(garbage),
        'quality_score': round(max(0, quality_score), 1),
        'sample_ligature_errors': [e[1] for e in ligature_errors[:5]],
        'sample_fragments': [f[0] for f in fragments[:5]],
    }


def main():
    print("=" * 70)
    print("PTS Dīgha Nikāya OCR Quality Analysis")
    print("=" * 70)
    print()

    results = []

    for sutta_num in range(1, 35):
        result = analyze_sutta(sutta_num)
        if result:
            results.append(result)

            # Quality indicator
            quality = result['quality_score']
            if quality >= 70:
                indicator = "✓"
            elif quality >= 50:
                indicator = "~"
            else:
                indicator = "✗"

            print(f"DN {sutta_num:2d}: Quality={quality:5.1f} {indicator}  "
                  f"Ratio={result['word_ratio']:.2f}  "
                  f"Diacr={result['diacritic_ratio']:.2f}  "
                  f"Lig={result['ligature_errors']:2d}  "
                  f"Frag={result['fragment_count']:3d}")

    # Summary statistics
    print()
    print("-" * 70)
    print("Summary:")
    print()

    good = [r for r in results if r['quality_score'] >= 70]
    moderate = [r for r in results if 50 <= r['quality_score'] < 70]
    poor = [r for r in results if r['quality_score'] < 50]

    print(f"  Good quality (≥70):     {len(good):2d} suttas")
    print(f"  Moderate quality (50-70): {len(moderate):2d} suttas")
    print(f"  Poor quality (<50):     {len(poor):2d} suttas")

    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    avg_ratio = sum(r['word_ratio'] for r in results) / len(results)

    print()
    print(f"  Average quality score: {avg_quality:.1f}")
    print(f"  Average word ratio (PTS/SC): {avg_ratio:.2f}")

    # Most problematic suttas
    print()
    print("Most problematic suttas:")
    for r in sorted(results, key=lambda x: x['quality_score'])[:5]:
        print(f"  DN {r['sutta']:2d}: score={r['quality_score']:.1f}, "
              f"ratio={r['word_ratio']:.2f}, "
              f"ligatures={r['ligature_errors']}")

    # Common ligature errors
    all_ligature_words = []
    for r in results:
        all_ligature_words.extend(r['sample_ligature_errors'])

    if all_ligature_words:
        print()
        print("Sample ligature errors across corpus:")
        for word in list(set(all_ligature_words))[:10]:
            print(f"  {word}")

    # Save results
    output_file = PTS_DIR / "_ocr_quality.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'good_quality': len(good),
                'moderate_quality': len(moderate),
                'poor_quality': len(poor),
                'average_quality': round(avg_quality, 1),
                'average_word_ratio': round(avg_ratio, 2)
            },
            'suttas': results
        }, f, indent=2, ensure_ascii=False)

    print()
    print(f"Full analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
