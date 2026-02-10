#!/usr/bin/env python3
"""
Build critical edition from collated variants.

Output format:
- Corrected PTS text (errors fixed using SC/VRI witnesses)
- Apparatus with all variants
- Cross-references to SC segment IDs
"""

import re
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-parsed/dn"
VRI_DIR = DATA_DIR / "vri-parsed/dn"
SC_DIR = DATA_DIR / "canonical/dn"
COLLATION_DIR = DATA_DIR / "collation/dn"
OUTPUT_DIR = DATA_DIR / "critical/dn"


def load_collation(sutta_num: int) -> Optional[dict]:
    """Load collation data for a sutta."""
    collation_file = COLLATION_DIR / f"dn{sutta_num}_collation.json"
    if collation_file.exists():
        return json.loads(collation_file.read_text())
    return None


def load_gretil_text(sutta_num: int) -> Optional[str]:
    """Load GRETIL text for a sutta."""
    gretil_file = GRETIL_DIR / f"dn{sutta_num}.json"
    if gretil_file.exists():
        data = json.loads(gretil_file.read_text())
        return data.get('text', '')
    return None


def load_sc_segments(sutta_num: int) -> list:
    """Load SC segments for cross-referencing."""
    sc_file = SC_DIR / f"dn{sutta_num}.json"
    if sc_file.exists():
        data = json.loads(sc_file.read_text())
        return data.get('segments', [])
    return []


def tokenize_with_positions(text: str) -> list:
    """Tokenize text with character positions."""
    tokens = []
    for match in re.finditer(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+', text):
        tokens.append({
            'word': match.group(0),
            'start': match.start(),
            'end': match.end()
        })
    return tokens


def apply_corrections(text: str, errors: list) -> tuple:
    """Apply corrections to text and return corrected text + log."""
    # Build correction map from errors
    # Only include corrections where words are clearly related (same base word)
    corrections = []

    for err in errors:
        g = err.get('gretil')
        preferred = err.get('preferred')

        if not g or not preferred or g == preferred:
            continue

        # Filter out corrections that are likely alignment artifacts
        # 1. Words must be similar in length (within 3 chars)
        if abs(len(g) - len(preferred)) > 3:
            continue

        # 2. One must be a prefix/suffix of the other OR share significant content
        g_lower = g.lower()
        p_lower = preferred.lower()

        # Check if it's a simple suffix/prefix addition (sandhi)
        # But only if the addition is small (1-2 chars) - otherwise it's a different word
        is_sandhi = False
        if g_lower in p_lower:
            extra = len(p_lower) - len(g_lower)
            is_sandhi = extra <= 2  # e.g., "aham" → "ahampi" (2 chars added)
        elif p_lower in g_lower:
            extra = len(g_lower) - len(p_lower)
            is_sandhi = extra <= 2

        # Check if the difference is just orthographic (ṃ vs m, ṇ vs n, etc.)
        is_ortho = False
        g_norm = g_lower.replace('ṃ', 'm').replace('ṇ', 'n').replace('ṅ', 'n')
        p_norm = p_lower.replace('ṃ', 'm').replace('ṇ', 'n').replace('ṅ', 'n')
        if g_norm == p_norm:
            is_ortho = True

        # Check Levenshtein distance for similar words
        # Be more strict for short words (< 6 chars require 80% similarity)
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, g_lower, p_lower).ratio()
        min_threshold = 0.8 if len(g_lower) < 6 else 0.7
        is_similar = similarity >= min_threshold

        if is_sandhi or is_ortho or is_similar:
            corrections.append({
                'original': g,
                'corrected': preferred,
                'notes': err.get('notes', ''),
                'type': 'orthographic' if is_ortho else ('sandhi' if is_sandhi else 'variant')
            })

    # Apply corrections
    corrected_text = text
    applied = []

    for corr in corrections:
        orig = corr['original']
        new = corr['corrected']

        # Count occurrences
        count = corrected_text.lower().count(orig.lower())
        if count > 0:
            # Replace preserving case where possible
            if orig[0].isupper() and new[0].islower():
                new = new[0].upper() + new[1:]

            # Word boundary replacement
            old_text = corrected_text
            corrected_text = re.sub(
                rf'\b{re.escape(orig)}\b',
                new,
                corrected_text,
                flags=re.IGNORECASE
            )

            if corrected_text != old_text:
                applied.append({
                    'original': orig,
                    'corrected': new,
                    'notes': corr['notes']
                })

    return corrected_text, applied


def build_apparatus(variants: list, uncertain: list) -> list:
    """Build critical apparatus from variants."""
    apparatus = []

    for var in variants:
        g = var.get('gretil')
        s = var.get('sc')
        v = var.get('vri')

        if not g:
            continue

        entry = {
            'lemma': g,
            'readings': {
                'PTS': g,
                'SC': s,
                'VRI': v
            },
            'type': var.get('type', 'variant'),
            'notes': var.get('notes', '')
        }
        apparatus.append(entry)

    # Add uncertain readings
    for unc in uncertain:
        g = unc.get('gretil')
        s = unc.get('sc')
        v = unc.get('vri')

        entry = {
            'lemma': g if g else (s or v),
            'readings': {
                'PTS': g,
                'SC': s,
                'VRI': v
            },
            'type': unc.get('type', 'uncertain'),
            'notes': unc.get('notes', '')
        }
        apparatus.append(entry)

    return apparatus


def build_critical_edition(sutta_num: int) -> dict:
    """Build critical edition for a single sutta."""
    # Load data
    collation = load_collation(sutta_num)
    if not collation:
        return {'error': f'No collation data for DN {sutta_num}'}

    gretil_text = load_gretil_text(sutta_num)
    if not gretil_text:
        return {'error': f'No GRETIL text for DN {sutta_num}'}

    sc_segments = load_sc_segments(sutta_num)

    # Apply corrections
    corrected_text, corrections_applied = apply_corrections(
        gretil_text,
        collation.get('errors', [])
    )

    # Build apparatus
    apparatus = build_apparatus(
        collation.get('variants', []),
        collation.get('uncertain', [])
    )

    # Build SC cross-reference (segment ID map)
    # This is a simplified version - full implementation would align text blocks
    sc_refs = []
    for seg in sc_segments:
        seg_id = seg.get('id', '')
        pali = seg.get('pali', '')
        if pali and ':0.' not in seg_id:  # Skip headers
            sc_refs.append({
                'id': seg_id,
                'text_sample': pali[:50] + '...' if len(pali) > 50 else pali
            })

    return {
        'id': f'dn{sutta_num}',
        'title': f'DN {sutta_num}',
        'base_edition': 'PTS (GRETIL transcription)',
        'witnesses': ['PTS', 'SC', 'VRI'],
        'pts_range': collation.get('pts_range'),
        'text': corrected_text,
        'word_count': len(tokenize_with_positions(corrected_text)),
        'corrections': {
            'total': len(corrections_applied),
            'list': corrections_applied[:50]  # Limit for readability
        },
        'apparatus': {
            'total': len(apparatus),
            'entries': apparatus[:100]  # Limit for readability
        },
        'sc_cross_ref': {
            'total_segments': len(sc_refs),
            'sample': sc_refs[:10]
        },
        'stats': collation.get('stats', {})
    }


def main():
    print("=" * 70)
    print("Building Critical Edition")
    print("=" * 70)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # Process all 34 DN suttas
    for sutta_num in range(1, 35):
        print(f"Building critical edition for DN {sutta_num}...")

        edition = build_critical_edition(sutta_num)

        if 'error' in edition:
            print(f"  Error: {edition['error']}")
            continue

        print(f"  Word count: {edition['word_count']:,}")
        print(f"  Corrections applied: {edition['corrections']['total']}")
        print(f"  Apparatus entries: {edition['apparatus']['total']}")

        if edition['corrections']['list']:
            print(f"  Sample corrections:")
            for corr in edition['corrections']['list'][:3]:
                print(f"    {corr['original']} → {corr['corrected']}")

        # Save critical edition
        output_file = OUTPUT_DIR / f"dn{sutta_num}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

        # Also save just the corrected text
        text_file = OUTPUT_DIR / f"dn{sutta_num}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(edition['text'])

        results.append({
            'sutta': sutta_num,
            'word_count': edition['word_count'],
            'corrections': edition['corrections']['total'],
            'apparatus_entries': edition['apparatus']['total']
        })

        print()

    # Summary
    print("-" * 70)
    print("Summary:")

    total_words = sum(r['word_count'] for r in results)
    total_corrections = sum(r['corrections'] for r in results)
    total_apparatus = sum(r['apparatus_entries'] for r in results)

    print(f"  Total words: {total_words:,}")
    print(f"  Total corrections: {total_corrections}")
    print(f"  Total apparatus entries: {total_apparatus}")

    # Save summary
    summary_file = OUTPUT_DIR / "_critical_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'description': 'Critical edition of Dīgha Nikāya pilot (DN 1-5)',
            'base_edition': 'PTS (GRETIL transcription)',
            'witnesses': ['PTS', 'SC', 'VRI'],
            'methodology': {
                'errors': 'Corrected where SC=VRI≠PTS and PTS not in DPD',
                'variants': 'Recorded where all readings are valid',
                'uncertain': 'Flagged for review where classification unclear'
            },
            'suttas': results,
            'totals': {
                'words': total_words,
                'corrections': total_corrections,
                'apparatus_entries': total_apparatus
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
