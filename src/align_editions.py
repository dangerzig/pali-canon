#!/usr/bin/env python3
"""
Multi-witness alignment of Pāli text editions.

Aligns:
- GRETIL (PTS primary)
- SC (SuttaCentral)
- VRI (Vipassana Research Institute)
- BJT (Buddha Jayanti Tipitaka)

Strategy:
1. Normalize texts (lowercase, consistent diacritics)
2. Find anchor points (section markers, distinctive phrases)
3. Block-level alignment between anchors
4. Word-level alignment within blocks
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-parsed/dn"
VRI_DIR = DATA_DIR / "vri-parsed/dn"
SC_DIR = DATA_DIR / "canonical/dn"
OUTPUT_DIR = DATA_DIR / "aligned/dn"


def normalize_text(text: str) -> str:
    """Normalize Pāli text for comparison."""
    text = text.lower()
    # Normalize niggahita variants (ṃ, ṁ, ṅ before consonants are often interchanged)
    text = text.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    # Normalize saṅgh/saṃgh - both represent same sound before 'gh'
    text = text.replace('saṅgh', 'saṃgh')
    # Remove hyphens (compound breaks vary between editions)
    text = text.replace('-', '')
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    # Remove asterisks and other markers
    text = text.replace('*', '')
    return text


def clean_gretil_for_alignment(text: str) -> str:
    """Remove GRETIL-specific markers for alignment."""
    # Remove section numbers like "1.1." or "2.3." or standalone " 2."
    text = re.sub(r'\d+\.\d+\.', '', text)
    text = re.sub(r'^\s*\d+\.\s*$', '', text, flags=re.MULTILINE)
    # Remove bracketed PTS refs like "[D. i. 1. 5"
    text = re.sub(r'\[D\.\s*[ivx]+\.\s*\d+\.\s*\d+', '', text)
    # Remove page markers
    text = re.sub(r'\[page\s+\d+\]', '', text)
    # Remove asterisks (used as markers)
    text = text.replace('*', '')
    # Join hyphenated compounds (PTS uses hyphens, others don't)
    text = re.sub(r'([a-zāīūṭḍṇṅñṃḷ])-([a-zāīūṭḍṇṅñṃḷ])', r'\1\2', text, flags=re.IGNORECASE)
    return text


def clean_vri_for_alignment(text: str) -> str:
    """Remove VRI-specific markers for alignment."""
    # Remove section numbers like "1 ."
    text = re.sub(r'^\d+\s+\.', '', text, flags=re.MULTILINE)
    # Remove sutta title line
    text = re.sub(r'^.*suttaṃ\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    # Remove section headers (single line titles)
    text = re.sub(r'^[A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+$', '', text, flags=re.MULTILINE)
    return text


def clean_sc_for_alignment(segments: list) -> str:
    """Extract and clean SC text for alignment."""
    # Skip header segments (usually 0.x IDs)
    text_parts = []
    for seg in segments:
        seg_id = seg.get('id', '')
        # Skip title/header segments
        if ':0.' in seg_id:
            continue
        pali = seg.get('pali', '')
        if pali:
            text_parts.append(pali)
    return ' '.join(text_parts)


def tokenize(text: str) -> list:
    """Tokenize Pāli text into words."""
    normalized = normalize_text(text)
    return re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', normalized)


def extract_section_markers(text: str, style: str = 'gretil') -> list:
    """Extract section markers from text.

    GRETIL style: "1.1." or "1.2."
    VRI style: "1 ." or "2 ."
    """
    markers = []

    if style == 'gretil':
        # Pattern: N.N. at start of section
        for match in re.finditer(r'(\d+)\.(\d+)\.', text):
            markers.append({
                'pos': match.start(),
                'section': f"{match.group(1)}.{match.group(2)}",
                'major': int(match.group(1)),
                'minor': int(match.group(2))
            })
    elif style == 'vri':
        # Pattern: N . at start of line
        for match in re.finditer(r'^(\d+)\s+\.', text, re.MULTILINE):
            markers.append({
                'pos': match.start(),
                'section': match.group(1),
                'num': int(match.group(1))
            })

    return markers


def extract_sc_sections(segments: list) -> list:
    """Extract section structure from SC segments."""
    sections = []
    for i, seg in enumerate(segments):
        seg_id = seg.get('id', '')
        # SC IDs like "dn1:1.1.2" - extract section number
        match = re.match(r'dn\d+:(\d+)\.(\d+)', seg_id)
        if match:
            sections.append({
                'idx': i,
                'id': seg_id,
                'major': int(match.group(1)),
                'minor': int(match.group(2)),
                'text': seg.get('pali', '')
            })
    return sections


def find_anchor_phrases(text: str) -> list:
    """Find distinctive phrases that serve as alignment anchors."""
    anchors = []

    # Common opening formulas
    patterns = [
        (r'evaṃ\s+me\s+sutaṃ', 'evam_me_sutam'),
        (r'ekaṃ\s+samayaṃ', 'ekam_samayam'),
        (r'bhagavā\s+etadavoca', 'bhagava_etadavoca'),
        (r'atha\s+kho\s+bhagavā', 'atha_kho_bhagava'),
        (r'niṭṭhitaṃ', 'nitthitam'),
        (r'suttaṃ\s+niṭṭhitaṃ', 'suttam_nitthitam'),
    ]

    normalized = normalize_text(text)
    for pattern, anchor_id in patterns:
        for match in re.finditer(pattern, normalized):
            anchors.append({
                'pos': match.start(),
                'end': match.end(),
                'anchor_id': anchor_id,
                'text': match.group(0)
            })

    return anchors


def align_word_sequences(words1: list, words2: list) -> list:
    """Align two word sequences using SequenceMatcher."""
    matcher = SequenceMatcher(None, words1, words2)
    alignments = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                alignments.append({
                    'type': 'match',
                    'word1': words1[i1 + k],
                    'word2': words2[j1 + k],
                    'idx1': i1 + k,
                    'idx2': j1 + k
                })
        elif op == 'replace':
            # Words at same position but different
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                w1 = words1[i1 + k] if i1 + k < i2 else None
                w2 = words2[j1 + k] if j1 + k < j2 else None
                alignments.append({
                    'type': 'variant',
                    'word1': w1,
                    'word2': w2,
                    'idx1': i1 + k if w1 else None,
                    'idx2': j1 + k if w2 else None
                })
        elif op == 'insert':
            for k in range(j2 - j1):
                alignments.append({
                    'type': 'insert',
                    'word1': None,
                    'word2': words2[j1 + k],
                    'idx1': None,
                    'idx2': j1 + k
                })
        elif op == 'delete':
            for k in range(i2 - i1):
                alignments.append({
                    'type': 'delete',
                    'word1': words1[i1 + k],
                    'word2': None,
                    'idx1': i1 + k,
                    'idx2': None
                })

    return alignments


def align_witnesses(gretil_words: list, sc_words: list, vri_words: list) -> list:
    """Perform multi-witness alignment."""
    # First align GRETIL (primary) with SC
    gretil_sc = align_word_sequences(gretil_words, sc_words)

    # Then align GRETIL with VRI
    gretil_vri = align_word_sequences(gretil_words, vri_words)

    # Build combined alignment indexed by GRETIL position
    combined = {}

    for align in gretil_sc:
        idx = align.get('idx1')
        if idx is not None:
            if idx not in combined:
                combined[idx] = {
                    'gretil': align['word1'],
                    'gretil_idx': idx,
                    'sc': None,
                    'sc_idx': None,
                    'vri': None,
                    'vri_idx': None,
                    'sc_match': None,
                    'vri_match': None
                }
            combined[idx]['sc'] = align['word2']
            combined[idx]['sc_idx'] = align.get('idx2')
            combined[idx]['sc_match'] = align['type']

    for align in gretil_vri:
        idx = align.get('idx1')
        if idx is not None:
            if idx not in combined:
                combined[idx] = {
                    'gretil': align['word1'],
                    'gretil_idx': idx,
                    'sc': None,
                    'sc_idx': None,
                    'vri': None,
                    'vri_idx': None,
                    'sc_match': None,
                    'vri_match': None
                }
            combined[idx]['vri'] = align['word2']
            combined[idx]['vri_idx'] = align.get('idx2')
            combined[idx]['vri_match'] = align['type']

    # Convert to sorted list
    result = [combined[i] for i in sorted(combined.keys())]
    return result


def compute_alignment_stats(alignment: list) -> dict:
    """Compute statistics on alignment quality."""
    total = len(alignment)
    if total == 0:
        return {'total': 0}

    sc_matches = sum(1 for a in alignment if a['sc_match'] == 'match')
    vri_matches = sum(1 for a in alignment if a['vri_match'] == 'match')

    # Full agreement (all witnesses)
    three_way = sum(1 for a in alignment
                    if a['sc_match'] == 'match' and a['vri_match'] == 'match')

    # GRETIL differs from both SC and VRI (but SC=VRI)
    gretil_outlier = sum(1 for a in alignment
                         if a['sc_match'] != 'match'
                         and a['vri_match'] != 'match'
                         and a.get('sc') == a.get('vri')
                         and a.get('sc') is not None)

    return {
        'total_words': total,
        'gretil_sc_matches': sc_matches,
        'gretil_sc_pct': round(sc_matches / total * 100, 1),
        'gretil_vri_matches': vri_matches,
        'gretil_vri_pct': round(vri_matches / total * 100, 1),
        'three_way_matches': three_way,
        'three_way_pct': round(three_way / total * 100, 1),
        'gretil_outlier': gretil_outlier,
        'gretil_outlier_pct': round(gretil_outlier / total * 100, 2)
    }


def load_sutta_data(sutta_num: int) -> dict:
    """Load sutta data from all three sources."""
    data = {}

    # GRETIL
    gretil_file = GRETIL_DIR / f"dn{sutta_num}.json"
    if gretil_file.exists():
        gretil = json.loads(gretil_file.read_text())
        raw_text = gretil.get('text', '')
        data['gretil'] = {
            'text': clean_gretil_for_alignment(raw_text),
            'raw_text': raw_text,
            'pts_refs': gretil.get('pts_refs', []),
            'pts_range': gretil.get('pts_range')
        }

    # VRI
    vri_file = VRI_DIR / f"dn{sutta_num}.json"
    if vri_file.exists():
        vri = json.loads(vri_file.read_text())
        raw_text = vri.get('text', '')
        data['vri'] = {
            'text': clean_vri_for_alignment(raw_text),
            'raw_text': raw_text,
            'sections': vri.get('sections', [])
        }

    # SC
    sc_file = SC_DIR / f"dn{sutta_num}.json"
    if sc_file.exists():
        sc = json.loads(sc_file.read_text())
        segments = sc.get('segments', [])
        data['sc'] = {
            'segments': segments,
            'text': clean_sc_for_alignment(segments)
        }

    return data


def align_sutta(sutta_num: int) -> dict:
    """Align a single sutta across all three editions."""
    data = load_sutta_data(sutta_num)

    if not all(k in data for k in ['gretil', 'sc', 'vri']):
        missing = [k for k in ['gretil', 'sc', 'vri'] if k not in data]
        return {'error': f'Missing sources: {missing}'}

    # Tokenize all three
    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    vri_words = tokenize(data['vri']['text'])

    # Perform multi-witness alignment
    alignment = align_witnesses(gretil_words, sc_words, vri_words)

    # Compute statistics
    stats = compute_alignment_stats(alignment)

    return {
        'sutta': sutta_num,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(vri_words)
        },
        'stats': stats,
        'alignment': alignment,
        'pts_range': data['gretil'].get('pts_range')
    }


def main():
    print("=" * 70)
    print("Multi-Witness Edition Alignment")
    print("=" * 70)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # Process DN 1-5 as pilot
    for sutta_num in range(1, 6):
        print(f"Aligning DN {sutta_num}...")

        result = align_sutta(sutta_num)

        if 'error' in result:
            print(f"  Error: {result['error']}")
            continue

        stats = result['stats']
        print(f"  Words: GRETIL={result['word_counts']['gretil']:,}, "
              f"SC={result['word_counts']['sc']:,}, VRI={result['word_counts']['vri']:,}")
        print(f"  All-witness match: {stats['three_way_pct']}%")
        print(f"  GRETIL outliers: {stats['gretil_outlier']} ({stats['gretil_outlier_pct']}%)")

        # Save alignment
        output_file = OUTPUT_DIR / f"dn{sutta_num}_aligned.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Don't save full alignment for summary - too large
            summary = {
                'sutta': result['sutta'],
                'word_counts': result['word_counts'],
                'stats': result['stats'],
                'pts_range': result['pts_range'],
                'sample_variants': []
            }

            # Extract sample variants (first 20 where GRETIL differs)
            variants = [a for a in result['alignment']
                       if a['sc_match'] != 'match' or a['vri_match'] != 'match'][:20]
            summary['sample_variants'] = variants

            json.dump(summary, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_num,
            'word_counts': result['word_counts'],
            'stats': result['stats']
        })

    # Save summary
    summary_file = OUTPUT_DIR / "_alignment_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'editions': ['GRETIL (PTS)', 'SC (Mahāsaṅgīti)', 'VRI (CST)'],
            'suttas': results,
            'average_three_way': round(
                sum(r['stats']['three_way_pct'] for r in results) / len(results), 1
            ) if results else 0
        }, f, indent=2, ensure_ascii=False)

    print()
    print("-" * 70)
    print("Summary:")
    if results:
        avg_match = sum(r['stats']['three_way_pct'] for r in results) / len(results)
        print(f"  Average all-witness match: {avg_match:.1f}%")
    print(f"  Output saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
