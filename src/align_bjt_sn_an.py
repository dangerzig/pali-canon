#!/usr/bin/env python3
"""
Align BJT per-sutta files with GRETIL sutta IDs for SN and AN.

The BJT edition frequently has more per-sutta files than GRETIL/PTS because
it expands peyyāla (abbreviated repetition series). Additionally, BJT's
internal saṃyutta numbering differs from PTS in some volumes, so BJT file
prefixes (e.g., sn17_*) may correspond to a different absolute saṃyutta
than expected (e.g., SN 18 in GRETIL/PTS).

This script builds mapping files: GRETIL sutta ID → BJT file(s).

Algorithm:
  1. Title-based anchoring: match GRETIL sutta titles against BJT sutta
     titles extracted from text (SN only, since GRETIL AN lacks titles)
  2. Sequential text similarity: fill gaps between anchors using text
     comparison that skips the formulaic nidāna opening
  3. Peyyāla ranges: BJT files between two anchor points are assigned
     to the preceding GRETIL sutta as an expanded peyyāla range

Output:
    data/alignment/sn_bjt_mapping.json
    data/alignment/an_bjt_mapping.json

Usage:
    python align_bjt_sn_an.py          # Align both SN and AN
    python align_bjt_sn_an.py sn       # SN only
    python align_bjt_sn_an.py an       # AN only
"""

import re
import sys
import json
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-parsed"
BJT_DIR = DATA_DIR / "bjt-parsed"
ALIGN_DIR = DATA_DIR / "alignment"

try:
    from pali.text import PALI_WORD_PATTERN, tokenize, normalize_title
except ImportError:
    PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)
    def tokenize(text: str) -> list[str]:
        return PALI_WORD_PATTERN.findall(text.lower())
    def normalize_title(title: str) -> str:
        t = title.lower().strip()
        t = re.sub(r'\s*sutta[ṃm]?\.?\s*$', '', t)
        t = re.sub(r'^(paṭhama|dutiya|tatiya|catuttha|pañcama)\s*', '', t)
        t = re.sub(r'\s+', '', t)
        return t


def text_similarity(text1, text2, skip: int = 0,
                    n_words: int = 50) -> float:
    """Compare texts using SequenceMatcher on tokenized words.

    Args:
        text1: Text string or pre-tokenized word list
        text2: Text string or pre-tokenized word list
        skip: number of initial words to skip (to avoid identical nidāna)
        n_words: number of words to compare after skipping
    """
    words1 = text1 if isinstance(text1, list) else tokenize(text1)
    words2 = text2 if isinstance(text2, list) else tokenize(text2)
    w1 = words1[skip:skip + n_words]
    w2 = words2[skip:skip + n_words]
    if not w1 or not w2:
        return 0.0
    return SequenceMatcher(None, w1, w2).ratio()


def extract_bjt_title(text: str) -> str | None:
    """Extract sutta title from BJT text."""
    chunk = text[:500]
    m = re.search(
        r'[\(\[]?\s*([\wāīūṭḍṇṅñṃḷĀĪŪṬḌṆÑṂḶ]'
        r'[\wāīūṭḍṇṅñṃḷĀĪŪṬḌṆÑṂḶ\s]*?sutta[ṃm])',
        chunk, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()
    return None


# ==================== File Loading ====================

def load_all_gretil(nikaya: str) -> list[dict]:
    """Load all GRETIL files for a nikāya, sorted by (group, sutta_num)."""
    gretil_dir = GRETIL_DIR / nikaya
    files = []
    group_key = 'samyutta' if nikaya == 'sn' else 'nipata'
    for f in gretil_dir.glob("*.json"):
        if f.name.startswith('_') or 'vol' in f.name:
            continue
        data = json.loads(f.read_text())
        file_id = data.get('id', '')
        parts = file_id.replace(nikaya, '').split('.')
        if not parts or not parts[0].isdigit():
            continue
        data['_file'] = f.name
        data['_group'] = int(parts[0])
        data['_sutta_num'] = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        files.append(data)
    files.sort(key=lambda d: (d['_group'], d['_sutta_num']))
    return files


def load_all_bjt(nikaya: str) -> list[dict]:
    """Load all BJT per-sutta files for a nikāya.

    Returns files sorted by (prefix_num, file_num).
    Note: prefix_num may NOT correspond to the correct absolute saṃyutta/nipāta
    due to offset mapping issues in split_bjt.py.
    """
    bjt_dir = BJT_DIR / nikaya
    files = []
    for f in bjt_dir.glob(f"{nikaya}*_*.json"):
        if 'vol' in f.name:
            continue
        data = json.loads(f.read_text())
        data['_file'] = f.name
        stem = f.stem  # e.g., "sn17_1"
        # Parse prefix number and sutta number
        parts = stem.replace(nikaya, '').split('_')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        data['_prefix'] = int(parts[0])
        data['_num'] = int(parts[1])
        data['_title'] = extract_bjt_title(data.get('text', ''))
        files.append(data)
    files.sort(key=lambda d: (d['_prefix'], d['_num']))
    return files


# ==================== SN Alignment ====================

def build_bjt_title_index(bjt_files: list[dict]) -> dict:
    """Build index: normalized_title → list of bjt files."""
    index = defaultdict(list)
    for b in bjt_files:
        if b['_title']:
            norm = normalize_title(b['_title'])
            if norm:
                index[norm].append(b)
    return dict(index)


def title_match(g_title: str, bjt_title_index: dict,
                g_text: str = '') -> dict | None:
    """Find best BJT match for a GRETIL title.

    Returns the best matching BJT file dict, or None.
    """
    g_norm = normalize_title(g_title)
    if not g_norm:
        return None

    candidates = []

    # Exact and containment matching
    for bjt_norm, bjt_files in bjt_title_index.items():
        if g_norm == bjt_norm or g_norm in bjt_norm or bjt_norm in g_norm:
            candidates.extend(bjt_files)

    # Fuzzy matching if no exact match
    if not candidates:
        for bjt_norm, bjt_files in bjt_title_index.items():
            ratio = SequenceMatcher(None, g_norm, bjt_norm).ratio()
            if ratio >= 0.55:
                candidates.extend((b, ratio) for b in bjt_files)
        if candidates:
            # Keep only candidates with best fuzzy ratio
            if isinstance(candidates[0], tuple):
                best_ratio = max(c[1] for c in candidates)
                candidates = [c[0] for c in candidates if c[1] >= best_ratio - 0.05]

    if not candidates:
        return None

    # If we have text, pick the candidate with best text similarity
    if g_text and len(candidates) > 1:
        return max(candidates, key=lambda b: text_similarity(
            g_text, b.get('text', ''), skip=5, n_words=50))
    return candidates[0]


# Known correct saṃyutta mapping overrides where auto-detection fails.
# BJT's internal saṃyutta numbering differs from PTS/GRETIL in vol 2
# (SN 13 is merged with SN 12, shifting everything by 1) and some
# titles are too generic for reliable auto-detection.
SN_SAMYUTTA_OVERRIDES = {
    # Vol 2: SN 13 merged with SN 12, subsequent numbers offset by -1
    13: 12,  # SN 13 (Abhisamaya) merged into BJT sn12 (with SN 12)
    14: 13,  # SN 14 (Dhātu) = BJT sn13
    15: 14,  # SN 15 (Anamatagga) = BJT sn14
    16: 15,  # SN 16 (Kassapa) = BJT sn15
    17: 16,  # SN 17 (Lābhasakkāra) = BJT sn16
    18: 17,  # SN 18 (Rāhula) = BJT sn17
    19: 18,  # SN 19 (Lakkhaṇa) = BJT sn18
    20: 19,  # SN 20 (Opamma) = BJT sn19
    21: 20,  # SN 21 (Bhikkhu) = BJT sn20
    # Vol 4: SN 36 (Vedanā) = BJT sn36 (not sn35 as auto-detected)
    36: 36,
    # Generic titles: force correct same-number mapping
    32: 32,  # SN 32 (Valāhaka, title "Desanā" too generic)
    37: 37,  # SN 37 (Mātugāma)
    49: 49,  # SN 49 (Ogha, range-style title)
    50: 50,  # SN 50 (empty title)
    53: 53,  # SN 53 (Jhāna, only 1 BJT file)
}


def build_samyutta_mapping(gretil_files: list[dict],
                           bjt_title_index: dict) -> dict:
    """Build saṃyutta-level mapping: GRETIL saṃyutta → BJT prefix.

    Uses title matching of first suttas to determine which BJT file prefix
    corresponds to each GRETIL saṃyutta, with manual overrides for known
    structural differences.
    """
    # Group GRETIL by saṃyutta, get first few suttas
    gretil_by_sam = defaultdict(list)
    for g in gretil_files:
        gretil_by_sam[g['_group']].append(g)

    mapping = {}
    for sam in sorted(gretil_by_sam):
        # Check overrides first
        if sam in SN_SAMYUTTA_OVERRIDES:
            mapping[sam] = SN_SAMYUTTA_OVERRIDES[sam]
            continue

        suttas = gretil_by_sam[sam][:5]
        prefix_votes = defaultdict(int)
        for s in suttas:
            title = s.get('title', '')
            if not title or title == 'NO TITLE':
                continue
            match = title_match(title, bjt_title_index, s.get('text', ''))
            if match:
                prefix_votes[match['_prefix']] += 1

        if prefix_votes:
            best_prefix = max(prefix_votes, key=prefix_votes.get)
            mapping[sam] = best_prefix
        else:
            # Default: same number
            mapping[sam] = sam

    return mapping


def align_sn():
    """Align all SN suttas using title-based anchoring + text similarity."""
    print("=" * 60)
    print("Aligning SN (Saṃyutta Nikāya)")
    print("=" * 60)

    # Load everything
    print("  Loading GRETIL files...")
    gretil_all = load_all_gretil('sn')
    print(f"    {len(gretil_all)} files")

    print("  Loading BJT files...")
    bjt_all = load_all_bjt('sn')
    print(f"    {len(bjt_all)} files")

    # Build BJT title index
    bjt_title_index = build_bjt_title_index(bjt_all)
    print(f"  BJT title index: {len(bjt_title_index)} unique titles")

    # Build saṃyutta-level mapping
    sam_map = build_samyutta_mapping(gretil_all, bjt_title_index)
    print(f"\n  Saṃyutta mapping (GRETIL → BJT prefix):")
    for g_sam in sorted(sam_map):
        b_prefix = sam_map[g_sam]
        marker = " ✓" if g_sam == b_prefix else f" ← sn{b_prefix}"
        print(f"    SN {g_sam:2d} → sn{b_prefix}{marker}")

    # Find unmapped saṃyuttas
    all_sams = sorted(set(g['_group'] for g in gretil_all))
    unmapped_sams = [s for s in all_sams if s not in sam_map]
    if unmapped_sams:
        print(f"\n  WARNING: {len(unmapped_sams)} saṃyuttas unmapped: {unmapped_sams}")

    # Group BJT files by prefix for efficient lookup
    bjt_by_prefix = defaultdict(list)
    for b in bjt_all:
        bjt_by_prefix[b['_prefix']].append(b)

    # Group GRETIL files by saṃyutta
    gretil_by_sam = defaultdict(list)
    for g in gretil_all:
        gretil_by_sam[g['_group']].append(g)

    # Per-saṃyutta alignment
    all_mappings = {}
    all_unmatched_g = []
    all_unmatched_b = []
    stats = []

    print(f"\n  Per-saṃyutta alignment:")

    for sam in all_sams:
        gretil_group = gretil_by_sam[sam]

        # Get correct BJT files using saṃyutta mapping
        if sam in sam_map:
            bjt_prefix = sam_map[sam]
            bjt_group = bjt_by_prefix.get(bjt_prefix, [])
        else:
            # Fallback: try same number
            bjt_group = bjt_by_prefix.get(sam, [])

        mapping, unmatched_g, unmatched_b = _align_within_group(
            gretil_group, bjt_group, bjt_title_index,
            use_titles=True
        )
        all_mappings.update(mapping)
        all_unmatched_g.extend(unmatched_g)
        all_unmatched_b.extend(unmatched_b)

        matched = len(mapping)
        total_g = len(gretil_group)
        total_b = len(bjt_group)
        multi = sum(1 for m in mapping.values() if len(m['bjt_files']) > 1)
        avg_conf = (sum(m['confidence'] for m in mapping.values()) / matched
                    if matched else 0)

        bjt_label = f"sn{sam_map[sam]}" if sam in sam_map else f"sn{sam}?"
        status = "OK" if matched == total_g else f"GAPS({total_g - matched})"
        print(f"    SN {sam:2d} ({bjt_label:>5s}): "
              f"G={total_g:4d} B={total_b:4d} → "
              f"matched {matched:4d}, multi {multi:3d}, "
              f"conf {avg_conf:.2f}  [{status}]")

        stats.append({
            'samyutta': sam, 'gretil': total_g, 'bjt': total_b,
            'bjt_prefix': sam_map.get(sam, sam),
            'matched': matched, 'unmatched_g': len(unmatched_g),
            'multi_file': multi,
        })

    return all_mappings, all_unmatched_g, all_unmatched_b, stats


def _align_within_group(gretil_files: list[dict], bjt_files: list[dict],
                        bjt_title_index: dict,
                        use_titles: bool = False) -> tuple[dict, list, list]:
    """Align GRETIL files to BJT files within a saṃyutta/nipāta group.

    Two-pass approach:
    1. Title-based anchoring (high confidence)
    2. Sequential text similarity between anchors (gap-filling)
    """
    if not gretil_files or not bjt_files:
        unmatched_g = [g['id'] for g in gretil_files]
        unmatched_b = [b['sutta'] for b in bjt_files]
        return {}, unmatched_g, unmatched_b

    n_gretil = len(gretil_files)
    n_bjt = len(bjt_files)

    # Build BJT index within this group
    bjt_local_titles = {}
    for idx, b in enumerate(bjt_files):
        if b['_title']:
            norm = normalize_title(b['_title'])
            if norm:
                bjt_local_titles.setdefault(norm, []).append(idx)

    # Pass 1: Title-based anchoring
    anchors = {}  # g_idx → bjt_idx (high confidence)
    used_bjt_indices = set()

    if use_titles:
        for g_idx, g in enumerate(gretil_files):
            g_title = g.get('title', '')
            if not g_title or g_title == 'NO TITLE':
                continue
            g_norm = normalize_title(g_title)
            if not g_norm:
                continue

            # Search in local group titles
            best_idx = None
            best_score = 0.0

            for bjt_norm, indices in bjt_local_titles.items():
                # Check title similarity
                if g_norm == bjt_norm or g_norm in bjt_norm or bjt_norm in g_norm:
                    title_score = 1.0
                else:
                    title_score = SequenceMatcher(None, g_norm, bjt_norm).ratio()

                if title_score < 0.5:
                    continue

                for b_idx in indices:
                    if b_idx in used_bjt_indices:
                        continue
                    # Confirm with text similarity (skip nidāna)
                    tsim = text_similarity(
                        g.get('text', ''), bjt_files[b_idx].get('text', ''),
                        skip=10, n_words=50
                    )
                    combined = title_score * 0.5 + tsim * 0.5
                    if combined > best_score:
                        best_score = combined
                        best_idx = b_idx

            if best_idx is not None and best_score >= 0.35:
                anchors[g_idx] = best_idx
                used_bjt_indices.add(best_idx)

    # Pass 2: Sequential text similarity for unanchored GRETIL suttas.
    # Two modes:
    # A) When title anchors exist: search between neighboring anchors
    #    (allows non-sequential matches within bounded regions)
    # B) When no anchors: forward-only cursor (strictly sequential)
    has_anchors = len(anchors) > 0
    bjt_cursor = 0  # used in mode B

    for g_idx in range(n_gretil):
        if g_idx in anchors:
            bjt_cursor = max(bjt_cursor, anchors[g_idx] + 1)
            continue

        g_text = gretil_files[g_idx].get('text', '')

        if has_anchors:
            # Mode A: search between neighboring anchors
            prev_bjt = -1
            for prev_g in range(g_idx - 1, -1, -1):
                if prev_g in anchors:
                    prev_bjt = anchors[prev_g]
                    break
            next_bjt = n_bjt
            for next_g in range(g_idx + 1, n_gretil):
                if next_g in anchors:
                    next_bjt = anchors[next_g]
                    break
            search_start = max(0, prev_bjt + 1)
            search_end = min(n_bjt, next_bjt)
        else:
            # Mode B: forward-only cursor with adaptive window
            search_start = bjt_cursor
            next_bjt = n_bjt
            for next_g in range(g_idx + 1, n_gretil):
                if next_g in anchors:
                    next_bjt = anchors[next_g]
                    break
            search_end = min(n_bjt, next_bjt)
            remaining_g = n_gretil - g_idx
            remaining_b = search_end - search_start
            max_window = max(20, (remaining_b // max(1, remaining_g)) * 3 + 10)
            search_end = min(search_end, search_start + max_window)

        if search_start >= search_end:
            continue

        best_score = 0.0
        best_idx = -1

        for b_idx in range(search_start, search_end):
            if b_idx in used_bjt_indices:
                continue
            sim1 = text_similarity(g_text, bjt_files[b_idx].get('text', ''),
                                   skip=0, n_words=60)
            sim2 = text_similarity(g_text, bjt_files[b_idx].get('text', ''),
                                   skip=12, n_words=50)
            score = max(sim1, sim2)
            if score > best_score:
                best_score = score
                best_idx = b_idx

        if best_idx >= 0 and best_score >= 0.30:
            anchors[g_idx] = best_idx
            used_bjt_indices.add(best_idx)
            if not has_anchors:
                bjt_cursor = best_idx + 1

    # Build mapping: assign BJT ranges between anchors
    # Sort anchors by g_idx to process in order
    sorted_anchors = sorted(anchors.items(), key=lambda x: x[0])

    mapping = {}

    for i, (g_idx, bjt_start) in enumerate(sorted_anchors):
        g_id = gretil_files[g_idx]['id']

        # Find end: next anchor's BJT position, or end of list
        bjt_end = n_bjt
        if i + 1 < len(sorted_anchors):
            bjt_end = sorted_anchors[i + 1][1]

        # If anchors are non-monotonic (bjt_end <= bjt_start), the range
        # would be empty. Fall back to single-file mapping for this anchor.
        if bjt_end <= bjt_start:
            bjt_file_ids = [bjt_files[bjt_start]['sutta']]
        else:
            bjt_file_ids = [bjt_files[k]['sutta'] for k in range(bjt_start, bjt_end)]

        # Compute confidence
        g_text = gretil_files[g_idx].get('text', '')
        conf = text_similarity(g_text, bjt_files[bjt_start].get('text', ''),
                               skip=0, n_words=60)
        method = 'title+text' if g_idx in {a[0] for a in sorted_anchors
                                            if a[0] in anchors and
                                            gretil_files[a[0]].get('title', '')
                                            not in ('', 'NO TITLE')} else 'text'

        mapping[g_id] = {
            'bjt_files': bjt_file_ids,
            'confidence': round(conf, 3),
            'method': method,
        }

    # Post-processing: assign unmatched GRETIL suttas to nearest neighbor's
    # primary BJT file. This handles condensation: when GRETIL has more
    # suttas than BJT, multiple GRETIL suttas should map to the same BJT file.
    for g_idx in range(n_gretil):
        if g_idx in anchors:
            continue
        g_id = gretil_files[g_idx]['id']

        # Find nearest matched g_idx (prefer closest in either direction)
        nearest = None
        for dist in range(1, max(n_gretil, n_bjt) + 1):
            earlier = g_idx - dist if g_idx - dist >= 0 else None
            later = g_idx + dist if g_idx + dist < n_gretil else None
            if earlier is not None and earlier in anchors:
                nearest = earlier
                break
            if later is not None and later in anchors:
                nearest = later
                break
        if nearest is None:
            continue

        # Assign the first BJT file from the nearest neighbor's mapping
        nearest_id = gretil_files[nearest]['id']
        if nearest_id in mapping and mapping[nearest_id]['bjt_files']:
            primary_bjt = mapping[nearest_id]['bjt_files'][0]
            g_text = gretil_files[g_idx].get('text', '')
            bjt_idx = anchors[nearest]
            conf = text_similarity(g_text, bjt_files[bjt_idx].get('text', ''),
                                   skip=0, n_words=60)
            mapping[g_id] = {
                'bjt_files': [primary_bjt],
                'confidence': round(conf, 3),
                'method': 'interpolated',
            }

    # Identify unmatched (anything still not in mapping)
    unmatched_gretil = []
    for g_idx in range(n_gretil):
        g_id = gretil_files[g_idx]['id']
        if g_id not in mapping:
            unmatched_gretil.append(g_id)

    matched_bjt = set()
    for m in mapping.values():
        for bf in m['bjt_files']:
            matched_bjt.add(bf)
    unmatched_bjt = [b['sutta'] for b in bjt_files if b['sutta'] not in matched_bjt]

    return mapping, unmatched_gretil, unmatched_bjt


# ==================== AN Alignment ====================

def align_an():
    """Align all AN nipātas.

    AN 1-3: vagga-level GRETIL → range of BJT files
    AN 4-11: per-sutta matching

    Unlike SN, GRETIL AN files have no title metadata, so we rely entirely
    on text similarity. However, BJT AN numbering should be correct (nipāta
    numbers in markers are absolute, unlike SN's local numbering).
    """
    print("=" * 60)
    print("Aligning AN (Aṅguttara Nikāya)")
    print("=" * 60)

    print("  Loading GRETIL files...")
    gretil_all = load_all_gretil('an')
    print(f"    {len(gretil_all)} files")

    print("  Loading BJT files...")
    bjt_all = load_all_bjt('an')
    print(f"    {len(bjt_all)} files")

    bjt_title_index = build_bjt_title_index(bjt_all)

    # Group by nipāta
    gretil_by_nip = defaultdict(list)
    for g in gretil_all:
        gretil_by_nip[g['_group']].append(g)

    bjt_by_nip = defaultdict(list)
    for b in bjt_all:
        bjt_by_nip[b['_prefix']].append(b)

    all_mappings = {}
    all_unmatched_g = []
    all_unmatched_b = []
    stats = []

    print(f"\n  Per-nipāta alignment:")

    for nipata in sorted(gretil_by_nip):
        gretil_group = gretil_by_nip[nipata]
        bjt_group = bjt_by_nip.get(nipata, [])

        # For AN, BJT numbering should be correct, so just match by nipāta
        mapping, unmatched_g, unmatched_b = _align_within_group(
            gretil_group, bjt_group, bjt_title_index,
            use_titles=False  # GRETIL AN has no titles
        )
        all_mappings.update(mapping)
        all_unmatched_g.extend(unmatched_g)
        all_unmatched_b.extend(unmatched_b)

        matched = len(mapping)
        total_g = len(gretil_group)
        total_b = len(bjt_group)
        multi = sum(1 for m in mapping.values() if len(m['bjt_files']) > 1)
        avg_conf = (sum(m['confidence'] for m in mapping.values()) / matched
                    if matched else 0)

        level = "vagga" if nipata <= 3 else "sutta"
        status = "OK" if matched == total_g else f"GAPS({total_g - matched})"
        print(f"    AN {nipata:2d} ({level:5s}): "
              f"G={total_g:4d} B={total_b:4d} → "
              f"matched {matched:4d}, multi {multi:3d}, "
              f"conf {avg_conf:.2f}  [{status}]")

        stats.append({
            'nipata': nipata, 'gretil': total_g, 'bjt': total_b,
            'matched': matched, 'unmatched_g': len(unmatched_g),
            'multi_file': multi,
        })

    return all_mappings, all_unmatched_g, all_unmatched_b, stats


# ==================== Output ====================

def save_mapping(nikaya: str, mappings: dict, unmatched_g: list,
                 unmatched_b: list, stats: list):
    """Save alignment mapping to JSON."""
    ALIGN_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        'metadata': {
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'collection': nikaya,
            'gretil_total': sum(s.get('gretil', 0) for s in stats),
            'bjt_total': sum(s.get('bjt', 0) for s in stats),
            'matched': len(mappings),
            'unmatched_gretil': len(unmatched_g),
            'unmatched_bjt': len(unmatched_b),
        },
        'group_stats': stats,
        'mappings': mappings,
        'unmatched_gretil': unmatched_g,
        'unmatched_bjt': unmatched_b,
    }

    out_file = ALIGN_DIR / f"{nikaya}_bjt_mapping.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_file}")
    print(f"  Matched: {len(mappings)}, Unmatched GRETIL: {len(unmatched_g)}, "
          f"Unmatched BJT: {len(unmatched_b)}")

    review_file = ALIGN_DIR / f"{nikaya}_review.txt"
    if unmatched_g:
        with open(review_file, 'w') as f:
            f.write(f"# Unmatched GRETIL {nikaya.upper()} suttas\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for gid in unmatched_g:
                f.write(f"{gid}\n")
        print(f"  Review file: {review_file}")
    elif review_file.exists():
        review_file.unlink()
        print(f"  Removed stale review file: {review_file}")


# ==================== Main ====================

def main():
    collections = sys.argv[1:] if len(sys.argv) > 1 else ['sn', 'an']

    for coll in collections:
        if coll == 'sn':
            mappings, unmatched_g, unmatched_b, stats = align_sn()
            save_mapping('sn', mappings, unmatched_g, unmatched_b, stats)
        elif coll == 'an':
            mappings, unmatched_g, unmatched_b, stats = align_an()
            save_mapping('an', mappings, unmatched_g, unmatched_b, stats)
        else:
            print(f"Unknown collection: {coll}")
        print()


if __name__ == "__main__":
    main()
