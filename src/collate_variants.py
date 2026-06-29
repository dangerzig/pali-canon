#!/usr/bin/env python3
"""
Collate variants across editions and classify differences.

Classification rules:
- Orthographic only (ṁ/ṃ, ṅ/ṃ): Normalize silently
- SC=VRI≠PTS + PTS not in DPD: Error - correct and note
- SC=VRI≠PTS + all valid words: Variant - record in apparatus
- All three differ: Uncertain - flag for review
"""

import re
import json
from pathlib import Path
from collections import Counter
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-parsed/dn"
VRI_DIR = DATA_DIR / "vri-parsed/dn"
SC_DIR = DATA_DIR / "canonical/dn"
DPD_DIR = DATA_DIR / "dpd"
OUTPUT_DIR = DATA_DIR / "collation/dn"

# DPD word validation delegates to collate_nikaya, which FAILS CLOSED (raises)
# when no DPD source is available rather than treating every word as valid.
# (This legacy module previously failed open; see CODE_REVIEW finding 2.)


def load_dpd_words() -> set:
    """Load the set of DPD-known word forms (fail-closed; see collate_nikaya)."""
    from collate_nikaya import load_dpd_words as _load
    return _load()


def is_valid_word(word: str) -> bool:
    """Check if a word exists in DPD (fail-closed; see collate_nikaya)."""
    from collate_nikaya import is_valid_word as _is_valid
    return _is_valid(word)


def normalize_for_comparison(word: str) -> str:
    """Normalize word for orthographic comparison."""
    if not word:
        return ''
    word = word.lower()
    # Normalize niggahita
    word = word.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    # Normalize ṅ/ṃ before consonants (both valid representations)
    word = word.replace('saṅgh', 'saṃgh')
    word = word.replace('saṅk', 'saṃk')
    return word


def is_orthographic_only(word1: str, word2: str) -> bool:
    """Check if difference is purely orthographic."""
    if not word1 or not word2:
        return False
    return normalize_for_comparison(word1) == normalize_for_comparison(word2)


def words_are_related(word1: str, word2: str) -> bool:
    """Check if two words are plausibly related (not alignment artifacts)."""
    if not word1 or not word2:
        return False

    w1 = word1.lower()
    w2 = word2.lower()

    # Short words (1-2 chars) are often fragments
    if len(w1) <= 2 or len(w2) <= 2:
        return w1 == w2

    # If length differs by more than 3x, likely unrelated
    len_ratio = max(len(w1), len(w2)) / min(len(w1), len(w2))
    if len_ratio > 3:
        return False

    # Check prefix similarity (sandhi variants often share prefix)
    common_prefix = 0
    for i in range(min(len(w1), len(w2))):
        if w1[i] == w2[i]:
            common_prefix += 1
        else:
            break
    prefix_ratio = common_prefix / min(len(w1), len(w2))

    # Strong prefix match indicates related words
    if prefix_ratio >= 0.5:
        return True

    # Check if one is a substring of the other (e.g., sandhi)
    if w1 in w2 or w2 in w1:
        return True

    # Levenshtein-ish check: require at least 60% of chars in sequence
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, w1, w2).ratio()

    return similarity >= 0.5


def classify_variant(gretil: str, sc: str, vri: str) -> dict:
    """Classify a variant reading.

    Returns classification with:
    - type: 'orthographic', 'error', 'variant', 'uncertain', 'insertion', 'deletion'
    - confidence: float 0-1
    - preferred: the recommended reading
    - notes: explanation
    """
    g = gretil.lower() if gretil else None
    s = sc.lower() if sc else None
    v = vri.lower() if vri else None

    # Skip if words are completely unrelated (alignment artifact)
    if g and s and v:
        if not words_are_related(g, s) and not words_are_related(g, v):
            return {
                'type': 'alignment_artifact',
                'confidence': 0.1,
                'preferred': None,
                'notes': 'Words appear unrelated - likely alignment issue'
            }

    # Skip very short fragments (likely OCR/parsing artifacts)
    if g and len(g) <= 2 and g not in {'ti', 'ca', 'vā', 'no', 'na', 'so', 'te', 'me', 'ye', 'pi'}:
        return {
            'type': 'fragment',
            'confidence': 0.1,
            'preferred': None,
            'notes': f'Short fragment: {g}'
        }

    # Handle insertions/deletions
    if not g and s and v:
        return {
            'type': 'pts_omission',
            'confidence': 0.8 if s == v else 0.5,
            'preferred': s if s == v else None,
            'notes': 'Present in SC/VRI but missing in PTS'
        }

    if g and not s and not v:
        return {
            'type': 'pts_addition',
            'confidence': 0.7,
            'preferred': g,
            'notes': 'Present in PTS but missing in SC/VRI'
        }

    if not g:
        return {'type': 'missing', 'confidence': 0, 'preferred': None, 'notes': 'Missing from PTS'}

    # Check if all three agree (after normalization)
    g_norm = normalize_for_comparison(g)
    s_norm = normalize_for_comparison(s) if s else None
    v_norm = normalize_for_comparison(v) if v else None

    if g_norm == s_norm == v_norm:
        return {
            'type': 'orthographic',
            'confidence': 1.0,
            'preferred': g,
            'notes': 'All editions agree (orthographic normalization)'
        }

    # SC and VRI agree against PTS
    if s_norm and v_norm and s_norm == v_norm and g_norm != s_norm:
        # Check if PTS reading is valid
        pts_valid = is_valid_word(g)
        sc_valid = is_valid_word(s)

        if not pts_valid and sc_valid:
            return {
                'type': 'error',
                'confidence': 0.9,
                'preferred': s,
                'notes': f'PTS "{g}" not in DPD, SC/VRI "{s}" is valid'
            }
        elif pts_valid and sc_valid:
            return {
                'type': 'variant',
                'confidence': 0.7,
                'preferred': g,  # Keep PTS as primary
                'notes': f'Textual variant: PTS "{g}" vs SC/VRI "{s}"'
            }
        else:
            return {
                'type': 'uncertain',
                'confidence': 0.4,
                'preferred': s,  # Prefer majority
                'notes': f'Neither reading validated: PTS "{g}" vs SC/VRI "{s}"'
            }

    # All three differ
    if g_norm != s_norm and g_norm != v_norm and s_norm != v_norm:
        # Check which is valid
        g_valid = is_valid_word(g)
        s_valid = is_valid_word(s) if s else False
        v_valid = is_valid_word(v) if v else False

        valid_count = sum([g_valid, s_valid, v_valid])

        if valid_count == 1:
            if g_valid:
                preferred = g
            elif s_valid:
                preferred = s
            else:
                preferred = v
            return {
                'type': 'uncertain',
                'confidence': 0.5,
                'preferred': preferred,
                'notes': 'Multi-way disagreement, one valid reading'
            }
        else:
            return {
                'type': 'uncertain',
                'confidence': 0.3,
                'preferred': g,  # Default to PTS
                'notes': f'Multi-way disagreement: PTS "{g}", SC "{s}", VRI "{v}"'
            }

    # PTS agrees with one but not other
    if g_norm == s_norm and g_norm != v_norm:
        return {
            'type': 'vri_variant',
            'confidence': 0.6,
            'preferred': g,
            'notes': f'VRI differs: "{v}" vs PTS/SC "{g}"'
        }

    if g_norm == v_norm and g_norm != s_norm:
        return {
            'type': 'sc_variant',
            'confidence': 0.6,
            'preferred': g,
            'notes': f'SC differs: "{s}" vs PTS/VRI "{g}"'
        }

    # Default
    return {
        'type': 'unknown',
        'confidence': 0.2,
        'preferred': g,
        'notes': 'Unable to classify'
    }


def tokenize(text: str) -> list:
    """Tokenize Pāli text into words with positions."""
    tokens = []
    for match in re.finditer(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+', text):
        tokens.append({
            'word': match.group(0),
            'start': match.start(),
            'end': match.end()
        })
    return tokens


def load_sutta_data(sutta_num: int) -> dict:
    """Load sutta data from all three sources."""
    data = {}

    # GRETIL
    gretil_file = GRETIL_DIR / f"dn{sutta_num}.json"
    if gretil_file.exists():
        gretil = json.loads(gretil_file.read_text())
        data['gretil'] = gretil

    # VRI
    vri_file = VRI_DIR / f"dn{sutta_num}.json"
    if vri_file.exists():
        vri = json.loads(vri_file.read_text())
        data['vri'] = vri

    # SC
    sc_file = SC_DIR / f"dn{sutta_num}.json"
    if sc_file.exists():
        sc = json.loads(sc_file.read_text())
        data['sc'] = sc

    return data


def collate_sutta(sutta_num: int, max_variants: int = 1000) -> dict:
    """Collate a single sutta and classify all variants."""
    from align_editions import align_sutta, tokenize as align_tokenize

    # Get alignment
    alignment_data = align_sutta(sutta_num)
    if 'error' in alignment_data:
        return {'error': alignment_data['error']}

    alignment = alignment_data.get('alignment', [])

    # Classify each position
    collation = {
        'sutta': sutta_num,
        'pts_range': alignment_data.get('pts_range'),
        'word_counts': alignment_data.get('word_counts'),
        'stats': {
            'total_positions': len(alignment),
            'orthographic': 0,
            'errors': 0,
            'variants': 0,
            'uncertain': 0,
            'match': 0,
            'other': 0
        },
        'errors': [],
        'variants': [],
        'uncertain': []
    }

    for i, pos in enumerate(alignment):
        g = pos.get('gretil')
        s = pos.get('sc')
        v = pos.get('vri')

        # Skip if all match
        if pos.get('sc_match') == 'match' and pos.get('vri_match') == 'match':
            collation['stats']['match'] += 1
            continue

        # Classify the difference
        classification = classify_variant(g, s, v)
        var_type = classification['type']

        # Update stats
        if var_type == 'orthographic':
            collation['stats']['orthographic'] += 1
        elif var_type == 'error':
            collation['stats']['errors'] += 1
            if len(collation['errors']) < max_variants:
                collation['errors'].append({
                    'position': i,
                    'gretil': g,
                    'sc': s,
                    'vri': v,
                    **classification
                })
        elif var_type == 'variant':
            collation['stats']['variants'] += 1
            if len(collation['variants']) < max_variants:
                collation['variants'].append({
                    'position': i,
                    'gretil': g,
                    'sc': s,
                    'vri': v,
                    **classification
                })
        elif var_type in ('uncertain', 'pts_omission', 'pts_addition'):
            collation['stats']['uncertain'] += 1
            if len(collation['uncertain']) < max_variants:
                collation['uncertain'].append({
                    'position': i,
                    'gretil': g,
                    'sc': s,
                    'vri': v,
                    **classification
                })
        elif var_type in ('alignment_artifact', 'fragment'):
            # Skip these - don't count as meaningful differences
            collation['stats']['other'] += 1
        else:
            collation['stats']['other'] += 1

    return collation


def main():
    print("=" * 70)
    print("Collating Variants Across Editions")
    print("=" * 70)
    print()

    # Check DPD availability
    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # Process all 34 DN suttas
    for sutta_num in range(1, 35):
        print(f"Collating DN {sutta_num}...")

        collation = collate_sutta(sutta_num)

        if 'error' in collation:
            print(f"  Error: {collation['error']}")
            continue

        stats = collation['stats']
        print(f"  Positions: {stats['total_positions']:,}")
        print(f"  Matches: {stats['match']:,} ({stats['match']/stats['total_positions']*100:.1f}%)")
        print(f"  Orthographic: {stats['orthographic']:,}")
        print(f"  Errors: {stats['errors']:,}")
        print(f"  Variants: {stats['variants']:,}")
        print(f"  Uncertain: {stats['uncertain']:,}")

        # Show sample errors
        if collation['errors']:
            print(f"  Sample errors:")
            for err in collation['errors'][:3]:
                print(f"    PTS '{err['gretil']}' → '{err['preferred']}': {err['notes']}")

        # Save collation
        output_file = OUTPUT_DIR / f"dn{sutta_num}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_num,
            'stats': stats
        })

        print()

    # Summary
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = OUTPUT_DIR / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)']
            },
            'dpd_words': len(dpd),
            'suttas': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
