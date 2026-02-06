#!/usr/bin/env python3
"""
Collate variants across editions for any nikaya.

Usage:
    python collate_nikaya.py mn    # Collate MN (Majjhima Nikāya)
    python collate_nikaya.py dn    # Collate DN (Dīgha Nikāya)

Classification rules:
- Orthographic only (ṁ/ṃ, ṅ/ṃ): Normalize silently
- SC=VRI≠PTS + PTS not in DPD: Error - correct and note
- SC=VRI≠PTS + all valid words: Variant - record in apparatus
- All three differ: Uncertain - flag for review
"""

import re
import sys
import json
from pathlib import Path
from collections import Counter
from typing import Optional
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
DPD_DIR = DATA_DIR / "dpd"

# Nikaya configurations: (nikaya_code, num_suttas_or_structure)
# For DN/MN: num_suttas is an integer
# For SN/AN: structure is a dict mapping saṃyutta/nipāta to sutta counts
NIKAYAS = {
    'dn': ('dn', 34),
    'mn': ('mn', 152),
    'sn': ('sn', 'samyutta'),  # Special handling for saṃyutta structure
    'an': ('an', 'nipata'),    # Special handling for nipāta structure
}

# Pre-compiled patterns
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Load DPD headwords for validation
_dpd_words = None


def load_dpd_words() -> set:
    """Load DPD headwords for word validation."""
    global _dpd_words
    if _dpd_words is not None:
        return _dpd_words

    dpd_file = DPD_DIR / "dpd_headwords.json"
    if dpd_file.exists():
        data = json.loads(dpd_file.read_text())
        _dpd_words = set(data.get('headwords', []))
    else:
        # Fallback: try to load from generated lemma lookup
        lookup_file = DATA_DIR / "lemma_lookup.json"
        if lookup_file.exists():
            data = json.loads(lookup_file.read_text())
            _dpd_words = set(data.keys())
        else:
            _dpd_words = set()

    return _dpd_words


def is_valid_word(word: str) -> bool:
    """Check if a word exists in DPD."""
    dpd = load_dpd_words()
    if not dpd:
        return True  # Can't validate without DPD
    word = word.lower().replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    return word in dpd


def normalize_for_comparison(word: str) -> str:
    """Normalize word for orthographic comparison."""
    if not word:
        return ''
    word = word.lower()
    word = word.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    word = word.replace('saṅgh', 'saṃgh')
    word = word.replace('saṅk', 'saṃk')
    return word


def normalize_text(text: str) -> str:
    """Normalize Pāli text for comparison."""
    text = text.lower()
    text = text.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    text = text.replace('saṅgh', 'saṃgh')
    text = text.replace('-', '')
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('*', '')
    return text


def tokenize(text: str) -> list:
    """Tokenize Pāli text into words."""
    normalized = normalize_text(text)
    return PALI_WORD_PATTERN.findall(normalized)


def clean_gretil_text(text: str) -> str:
    """Remove GRETIL-specific markers."""
    text = re.sub(r'\d+\.\d+\.', '', text)
    text = re.sub(r'^\s*\d+\.\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[[DM]\.\s*[ivx]+\.\s*\d+\.\s*\d+', '', text)
    text = re.sub(r'\[page\s+\d+\]', '', text)
    text = text.replace('*', '')
    text = re.sub(r'([a-zāīūṭḍṇṅñṃḷ])-([a-zāīūṭḍṇṅñṃḷ])', r'\1\2', text, flags=re.IGNORECASE)
    return text


def clean_vri_text(text: str) -> str:
    """Remove VRI-specific markers."""
    text = re.sub(r'^\d+\s+\.', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*suttaṃ\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def clean_sc_segments(segments: list) -> str:
    """Extract and clean SC text from segments."""
    text_parts = []
    for seg in segments:
        seg_id = seg.get('id', '')
        if ':0.' in seg_id:
            continue
        pali = seg.get('pali', '')
        if pali:
            text_parts.append(pali)
    return ' '.join(text_parts)


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


def align_three_way(gretil_words: list, sc_words: list, vri_words: list) -> list:
    """Perform three-way alignment."""
    gretil_sc = align_word_sequences(gretil_words, sc_words)
    gretil_vri = align_word_sequences(gretil_words, vri_words)

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

    return [combined[i] for i in sorted(combined.keys())]


def words_are_related(word1: str, word2: str) -> bool:
    """Check if two words are plausibly related."""
    if not word1 or not word2:
        return False

    w1 = word1.lower()
    w2 = word2.lower()

    if len(w1) <= 2 or len(w2) <= 2:
        return w1 == w2

    len_ratio = max(len(w1), len(w2)) / min(len(w1), len(w2))
    if len_ratio > 3:
        return False

    common_prefix = 0
    for i in range(min(len(w1), len(w2))):
        if w1[i] == w2[i]:
            common_prefix += 1
        else:
            break
    prefix_ratio = common_prefix / min(len(w1), len(w2))

    if prefix_ratio >= 0.5:
        return True

    if w1 in w2 or w2 in w1:
        return True

    similarity = SequenceMatcher(None, w1, w2).ratio()
    return similarity >= 0.5


def classify_variant(gretil: str, sc: str, vri: str) -> dict:
    """Classify a variant reading."""
    g = gretil.lower() if gretil else None
    s = sc.lower() if sc else None
    v = vri.lower() if vri else None

    if g and s and v:
        if not words_are_related(g, s) and not words_are_related(g, v):
            return {
                'type': 'alignment_artifact',
                'confidence': 0.1,
                'preferred': None,
                'notes': 'Words appear unrelated - likely alignment issue'
            }

    if g and len(g) <= 2 and g not in {'ti', 'ca', 'vā', 'no', 'na', 'so', 'te', 'me', 'ye', 'pi'}:
        return {
            'type': 'fragment',
            'confidence': 0.1,
            'preferred': None,
            'notes': f'Short fragment: {g}'
        }

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

    if s_norm and v_norm and s_norm == v_norm and g_norm != s_norm:
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
                'preferred': g,
                'notes': f'Textual variant: PTS "{g}" vs SC/VRI "{s}"'
            }
        else:
            return {
                'type': 'uncertain',
                'confidence': 0.4,
                'preferred': s,
                'notes': f'Neither reading validated: PTS "{g}" vs SC/VRI "{s}"'
            }

    if g_norm != s_norm and g_norm != v_norm and s_norm != v_norm:
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
                'notes': 'Three-way disagreement, one valid reading'
            }
        else:
            return {
                'type': 'uncertain',
                'confidence': 0.3,
                'preferred': g,
                'notes': f'Three-way disagreement: PTS "{g}", SC "{s}", VRI "{v}"'
            }

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

    return {
        'type': 'unknown',
        'confidence': 0.2,
        'preferred': g,
        'notes': 'Unable to classify'
    }


def get_sn_sutta_ids() -> list:
    """Get all SN sutta IDs from the VRI parsed data."""
    vri_dir = DATA_DIR / "vri-parsed/sn"
    summary_file = vri_dir / "_summary.json"

    if not summary_file.exists():
        return []

    summary = json.loads(summary_file.read_text())
    samyutta_counts = summary.get('samyutta_counts', {})

    sutta_ids = []
    for samyutta, count in sorted(samyutta_counts.items(), key=lambda x: int(x[0])):
        for sutta in range(1, count + 1):
            sutta_ids.append(f"sn{samyutta}.{sutta}")

    return sutta_ids


def load_sutta_data_sn(sutta_id: str) -> dict:
    """Load SN sutta data from all three sources.

    Args:
        sutta_id: Full sutta ID like "sn1.1", "sn12.23"
    """
    data = {}

    # Parse sutta ID
    match = re.match(r'sn(\d+)\.(\d+)', sutta_id)
    if not match:
        return data

    samyutta = int(match.group(1))
    sutta_num = int(match.group(2))

    gretil_dir = DATA_DIR / "gretil-parsed/sn"
    vri_dir = DATA_DIR / "vri-parsed/sn"
    sc_dir = DATA_DIR / "canonical/sn"

    # GRETIL - file named like sn1_1.json
    gretil_file = gretil_dir / f"sn{samyutta}_{sutta_num}.json"
    if gretil_file.exists():
        gretil = json.loads(gretil_file.read_text())
        raw_text = gretil.get('text', '')
        data['gretil'] = {
            'text': clean_gretil_text(raw_text),
            'raw_text': raw_text,
        }

    # VRI - file named like sn1_1.json
    vri_file = vri_dir / f"sn{samyutta}_{sutta_num}.json"
    if vri_file.exists():
        vri = json.loads(vri_file.read_text())
        raw_text = vri.get('text', '')
        data['vri'] = {
            'text': clean_vri_text(raw_text),
            'raw_text': raw_text,
        }

    # SC - file named like sn{samyutta}.json, suttas nested within
    sc_file = sc_dir / f"sn{samyutta}.json"
    if sc_file.exists():
        sc_data = json.loads(sc_file.read_text())
        # Find the specific sutta by ID
        for sutta in sc_data.get('suttas', []):
            if sutta.get('id') == sutta_id:
                segments = sutta.get('segments', [])
                data['sc'] = {
                    'segments': segments,
                    'text': clean_sc_segments(segments)
                }
                break

    return data


def load_sutta_data(nikaya: str, sutta_num: int) -> dict:
    """Load sutta data from all three sources."""
    data = {}

    gretil_dir = DATA_DIR / f"gretil-parsed/{nikaya}"
    vri_dir = DATA_DIR / f"vri-parsed/{nikaya}"
    sc_dir = DATA_DIR / f"canonical/{nikaya}"

    # GRETIL
    gretil_file = gretil_dir / f"{nikaya}{sutta_num}.json"
    if gretil_file.exists():
        gretil = json.loads(gretil_file.read_text())
        raw_text = gretil.get('text', '')
        data['gretil'] = {
            'text': clean_gretil_text(raw_text),
            'raw_text': raw_text,
        }

    # VRI
    vri_file = vri_dir / f"{nikaya}{sutta_num}.json"
    if vri_file.exists():
        vri = json.loads(vri_file.read_text())
        raw_text = vri.get('text', '')
        data['vri'] = {
            'text': clean_vri_text(raw_text),
            'raw_text': raw_text,
        }

    # SC
    sc_file = sc_dir / f"{nikaya}{sutta_num}.json"
    if sc_file.exists():
        sc = json.loads(sc_file.read_text())
        segments = sc.get('segments', [])
        data['sc'] = {
            'segments': segments,
            'text': clean_sc_segments(segments)
        }

    return data


def align_sutta(nikaya: str, sutta_num: int) -> dict:
    """Align a single sutta across all three editions."""
    data = load_sutta_data(nikaya, sutta_num)

    missing = [k for k in ['gretil', 'sc', 'vri'] if k not in data]
    if missing:
        return {'error': f'Missing sources: {missing}'}

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    vri_words = tokenize(data['vri']['text'])

    alignment = align_three_way(gretil_words, sc_words, vri_words)

    return {
        'sutta': sutta_num,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(vri_words)
        },
        'alignment': alignment
    }


def align_sutta_sn(sutta_id: str) -> dict:
    """Align a single SN sutta across all three editions.

    Args:
        sutta_id: Full sutta ID like "sn1.1"
    """
    data = load_sutta_data_sn(sutta_id)

    missing = [k for k in ['gretil', 'sc', 'vri'] if k not in data]
    if missing:
        return {'error': f'Missing sources: {missing}'}

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    vri_words = tokenize(data['vri']['text'])

    alignment = align_three_way(gretil_words, sc_words, vri_words)

    return {
        'sutta': sutta_id,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(vri_words)
        },
        'alignment': alignment
    }


def collate_sutta(nikaya: str, sutta_num: int, max_variants: int = 1000) -> dict:
    """Collate a single sutta and classify all variants."""
    alignment_data = align_sutta(nikaya, sutta_num)
    if 'error' in alignment_data:
        return {'error': alignment_data['error']}

    alignment = alignment_data.get('alignment', [])

    collation = {
        'sutta': sutta_num,
        'nikaya': nikaya.upper(),
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

    return _process_collation(collation, alignment, max_variants)


def collate_sutta_sn(sutta_id: str, max_variants: int = 1000) -> dict:
    """Collate a single SN sutta and classify all variants."""
    alignment_data = align_sutta_sn(sutta_id)
    if 'error' in alignment_data:
        return {'error': alignment_data['error']}

    alignment = alignment_data.get('alignment', [])

    collation = {
        'sutta': sutta_id,
        'nikaya': 'SN',
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

    return _process_collation(collation, alignment, max_variants)


def _process_collation(collation: dict, alignment: list, max_variants: int) -> dict:
    """Process alignment data and classify variants."""

    for i, pos in enumerate(alignment):
        g = pos.get('gretil')
        s = pos.get('sc')
        v = pos.get('vri')

        if pos.get('sc_match') == 'match' and pos.get('vri_match') == 'match':
            collation['stats']['match'] += 1
            continue

        classification = classify_variant(g, s, v)
        var_type = classification['type']

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
            collation['stats']['other'] += 1
        else:
            collation['stats']['other'] += 1

    return collation


def main_sn(output_dir: Path):
    """Main function for collating SN (Saṃyutta Nikāya)."""
    sutta_ids = get_sn_sutta_ids()
    total_suttas = len(sutta_ids)

    print("=" * 70)
    print(f"Collating Variants: SN ({total_suttas} suttas)")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    processed = 0

    for sutta_id in sutta_ids:
        processed += 1
        if processed % 100 == 0 or processed <= 10:
            print(f"Collating {sutta_id} ({processed}/{total_suttas})...", end=" ")

        collation = collate_sutta_sn(sutta_id)

        if 'error' in collation:
            if processed % 100 == 0 or processed <= 10:
                print(f"SKIPPED: {collation['error']}")
            skipped.append(sutta_id)
            continue

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        if processed % 100 == 0 or processed <= 10:
            print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}")

        # Save collation - convert sn1.1 to sn1_1 for filename
        safe_id = sutta_id.replace('.', '_')
        output_file = output_dir / f"{safe_id}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_id,
            'stats': stats
        })

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Suttas processed: {len(results)}/{total_suttas}")
    if skipped:
        print(f"  Skipped (missing data): {len(skipped)} suttas")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'nikaya': 'SN',
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)']
            },
            'dpd_words': len(dpd),
            'suttas_processed': len(results),
            'suttas_skipped': len(skipped),
            'skipped_ids': skipped[:100],  # First 100 skipped
            'suttas': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_dir}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python collate_nikaya.py <nikaya>")
        print("  nikaya: dn, mn, sn, an")
        sys.exit(1)

    nikaya = sys.argv[1].lower()
    if nikaya not in NIKAYAS:
        print(f"Unknown nikaya: {nikaya}")
        print(f"Available: {', '.join(NIKAYAS.keys())}")
        sys.exit(1)

    nikaya_code, structure = NIKAYAS[nikaya]
    output_dir = DATA_DIR / f"collation/{nikaya}"

    # Handle SN/AN with special structure
    if structure == 'samyutta':
        main_sn(output_dir)
        return
    elif structure == 'nipata':
        print("AN collation not yet implemented")
        return

    num_suttas = structure

    print("=" * 70)
    print(f"Collating Variants: {nikaya.upper()} (1-{num_suttas})")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []

    for sutta_num in range(1, num_suttas + 1):
        print(f"Collating {nikaya.upper()} {sutta_num}...", end=" ")

        collation = collate_sutta(nikaya, sutta_num)

        if 'error' in collation:
            print(f"SKIPPED: {collation['error']}")
            skipped.append(sutta_num)
            continue

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}")

        # Save collation
        output_file = output_dir / f"{nikaya}{sutta_num}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_num,
            'stats': stats
        })

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Suttas processed: {len(results)}/{num_suttas}")
    if skipped:
        print(f"  Skipped (missing data): {skipped}")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'nikaya': nikaya.upper(),
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)']
            },
            'dpd_words': len(dpd),
            'suttas_processed': len(results),
            'suttas_skipped': skipped,
            'suttas': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved to: {output_dir}")


if __name__ == "__main__":
    main()
