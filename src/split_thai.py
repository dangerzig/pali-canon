#!/usr/bin/env python3
"""
Split Thai Royal Edition volume files into per-text/per-sutta files.

Usage:
    python split_thai.py              # Split all
    python split_thai.py kn           # Split KN only
    python split_thai.py dn mn        # Split DN and MN

Creates per-sutta/per-text files alongside existing volume files in data/thai-parsed/.

The Thai (Syām Raṭṭha) edition uses a 45-volume layout where some volumes combine
multiple texts. This script splits those combined volumes into individual files
matching the naming conventions used by the collation pipeline.
"""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
THAI_DIR = DATA_DIR / "thai-parsed"

try:
    from pali.text import PALI_WORD_PATTERN, tokenize, normalize_title
except ImportError:
    PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)
    def tokenize(text: str) -> list:
        return PALI_WORD_PATTERN.findall(text.lower())
    def normalize_title(title: str) -> str:
        t = title.lower().strip()
        t = re.sub(r'\s*sutta[ṃm]?\.?\s*$', '', t)
        t = re.sub(r'^(paṭhama|dutiya|tatiya|catuttha|pañcama)\s*', '', t)
        t = re.sub(r'\s+', '', t)
        return t


def save_text(output_dir: Path, filename: str, text_id: str, text: str,
              extra: dict = None):
    """Save a per-text JSON file."""
    words = tokenize(text)
    data = {
        "source": "thai",
        "edition": "Syām Raṭṭha (Royal Thai Edition)",
        "text_id": text_id,
        "text": text.strip(),
        "word_count": len(words),
    }
    if extra:
        data.update(extra)
    with open(output_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_thai_json(filepath: Path) -> str:
    """Load Thai volume JSON and return text."""
    with open(filepath, encoding='utf-8') as f:
        return json.load(f)['text']


GRETIL_DIR = DATA_DIR / "gretil-parsed"


# ==================== GRETIL-Anchored Alignment ====================

def tokenize_with_positions(text: str) -> tuple[list[str], list[int]]:
    """Tokenize text and return (word_list, char_positions)."""
    words = []
    positions = []
    for m in PALI_WORD_PATTERN.finditer(text):
        words.append(m.group().lower())
        positions.append(m.start())
    return words, positions


def text_similarity(words1: list, words2: list, skip: int = 0,
                    n_words: int = 50) -> float:
    """Compare pre-tokenized word sequences using SequenceMatcher."""
    w1 = words1[skip:skip + n_words]
    w2 = words2[skip:skip + n_words]
    if not w1 or not w2:
        return 0.0
    return SequenceMatcher(None, w1, w2).ratio()


def load_gretil_suttas(nikaya: str, group_num: int) -> list[dict]:
    """Load GRETIL per-sutta files for a saṃyutta or nipāta."""
    gretil_dir = GRETIL_DIR / nikaya
    files = []
    for f in gretil_dir.glob(f"{nikaya}{group_num}_*.json"):
        stem_parts = f.stem.split('_')
        if len(stem_parts) != 2 or not stem_parts[1].isdigit():
            continue
        data = json.loads(f.read_text())
        sutta_num = int(stem_parts[1])
        data['_sutta_num'] = sutta_num
        data['_words'] = [w.lower() for w in tokenize(data.get('text', ''))]
        files.append(data)
    files.sort(key=lambda d: d['_sutta_num'])
    return files


def align_gretil_to_thai_text(gretil_suttas: list, thai_words: list,
                               thai_positions: list,
                               use_titles: bool = True) -> list:
    """Align GRETIL suttas to positions in Thai text using text similarity.

    Two-pass algorithm adapted from align_bjt_sn_an.py:
    1. Title-based anchoring (SN only, where GRETIL has titles)
    2. Sequential text similarity with forward cursor

    Args:
        gretil_suttas: GRETIL per-sutta dicts with _words and title
        thai_words: tokenized Thai text (lowercase)
        thai_positions: character position of each word in original text
        use_titles: whether to attempt title-based anchoring

    Returns:
        list of (sutta_file_id, word_idx, confidence, method) in sutta order
    """
    n_gretil = len(gretil_suttas)
    n_thai = len(thai_words)
    if not n_gretil or not n_thai:
        return []

    anchors = {}  # g_idx → thai_word_idx
    methods = {}  # g_idx → method string

    # Pass 1: Title-based anchoring (must be monotonic)
    if use_titles:
        # Build Thai title index
        thai_title_positions = []
        for i, w in enumerate(thai_words):
            if w.endswith('suttaṃ') and len(w) > 7:
                name = w[:-6]
                if len(name) >= 3:
                    thai_title_positions.append((name, i))

        min_pos = 0  # enforce monotonicity
        for g_idx, g in enumerate(gretil_suttas):
            g_title = g.get('title', '')
            if not g_title or g_title == 'NO TITLE':
                continue
            g_norm = normalize_title(g_title)
            if not g_norm or len(g_norm) < 3:
                continue

            best_score = 0.0
            best_word_idx = -1

            for thai_norm, t_word_idx in thai_title_positions:
                if t_word_idx < min_pos:
                    continue  # enforce monotonicity
                if g_norm == thai_norm or g_norm in thai_norm or thai_norm in g_norm:
                    title_score = 1.0
                else:
                    title_score = SequenceMatcher(None, g_norm, thai_norm).ratio()
                if title_score < 0.5:
                    continue

                g_words = g.get('_words', [])
                thai_window = thai_words[t_word_idx:t_word_idx + 70]
                tsim = text_similarity(g_words, thai_window, skip=10, n_words=50)
                combined = title_score * 0.4 + tsim * 0.6

                if combined > best_score:
                    best_score = combined
                    best_word_idx = t_word_idx

            if best_word_idx >= 0 and best_score >= 0.35:
                anchors[g_idx] = best_word_idx
                methods[g_idx] = 'title+text'
                min_pos = best_word_idx + 1

    # Pass 2: Sequential text similarity for unanchored suttas
    # Always use forward cursor to maintain ordering
    cursor = 0

    for g_idx in range(n_gretil):
        if g_idx in anchors:
            cursor = max(cursor, anchors[g_idx] + 1)
            continue

        g_words = gretil_suttas[g_idx].get('_words', [])
        if not g_words:
            continue

        # Search from cursor to next anchor (or end)
        search_start = cursor
        search_end = n_thai
        for next_g in range(g_idx + 1, n_gretil):
            if next_g in anchors:
                search_end = anchors[next_g]
                break

        # Adaptive window: don't search too far ahead if many suttas remain
        remaining_g = sum(1 for gi in range(g_idx, n_gretil) if gi not in anchors)
        remaining_t = search_end - search_start
        if remaining_g > 1:
            max_window = max(100, (remaining_t // remaining_g) * 3 + 50)
            search_end = min(search_end, search_start + max_window)

        if search_start >= search_end:
            continue

        best_score = 0.0
        best_pos = -1
        stride = max(1, min(5, (search_end - search_start) // 50))

        for t_idx in range(search_start, search_end, stride):
            thai_window = thai_words[t_idx:t_idx + 70]
            sim1 = text_similarity(g_words, thai_window, skip=0, n_words=60)
            sim2 = text_similarity(g_words, thai_window, skip=12, n_words=50)
            score = max(sim1, sim2)
            if score > best_score:
                best_score = score
                best_pos = t_idx

        if best_pos >= 0 and best_score >= 0.25:
            anchors[g_idx] = best_pos
            methods[g_idx] = 'text'
            cursor = best_pos + 1

    # Post-processing: interpolate unanchored suttas proportionally
    # Process in sutta order, placing each between its surrounding anchors
    for g_idx in range(n_gretil):
        if g_idx in anchors:
            continue

        # Find previous and next anchors
        prev_g, prev_pos = -1, 0
        for pg in range(g_idx - 1, -1, -1):
            if pg in anchors:
                prev_g, prev_pos = pg, anchors[pg]
                break

        next_g, next_pos = n_gretil, n_thai - 1
        for ng in range(g_idx + 1, n_gretil):
            if ng in anchors:
                next_g, next_pos = ng, anchors[ng]
                break

        # Proportional placement between prev and next
        span_g = next_g - prev_g
        span_t = next_pos - prev_pos
        if span_g > 0:
            frac = (g_idx - prev_g) / span_g
            est_pos = int(prev_pos + frac * span_t)
        else:
            est_pos = prev_pos

        est_pos = max(0, min(n_thai - 1, est_pos))
        anchors[g_idx] = est_pos
        methods[g_idx] = 'interpolated'

    # Build results in sutta order (guaranteed monotonic by construction)
    results = []
    for g_idx in range(n_gretil):
        if g_idx not in anchors:
            continue
        word_idx = anchors[g_idx]
        sutta_id = gretil_suttas[g_idx].get('id', f'unknown_{g_idx}')
        sutta_file_id = sutta_id.replace('.', '_')

        # Compute confidence
        g_words = gretil_suttas[g_idx].get('_words', [])
        conf = 0.0
        if g_words:
            thai_window = thai_words[word_idx:word_idx + 70]
            conf = max(
                text_similarity(g_words, thai_window, skip=0, n_words=60),
                text_similarity(g_words, thai_window, skip=12, n_words=50)
            )

        results.append((sutta_file_id, word_idx, round(conf, 3),
                        methods.get(g_idx, 'interpolated')))

    return results


# ==================== Cleanup ====================

# Volume-level files to keep (everything else in these dirs is a bad split)
KN_VOLUME_FILES = {
    'kn_minor.json', 'kn_verse.json', 'ja.json', 'mnd.json',
    'cnd.json', 'ps.json', 'ap.json'
}

AN_VOLUME_FILES = {
    'an_vol1.json', 'an_vol2.json', 'an_vol3.json',
    'an_vol4.json', 'an_vol5.json'
}

ABHIDHAMMA_VOLUME_FILES = {
    'dhammasangani.json', 'vibhanga.json', 'dhatukatha_puggalapannatti.json',
    'kathavatthu.json', 'yamaka.json', 'patthana.json'
}


def cleanup():
    """Delete wrongly-generated per-text split files."""
    deleted = 0

    # KN: keep only volume-level files
    kn_dir = THAI_DIR / "kn"
    if kn_dir.exists():
        for f in kn_dir.iterdir():
            if f.name.endswith('.json') and f.name not in KN_VOLUME_FILES:
                f.unlink()
                deleted += 1

    # AN: keep only volume files
    an_dir = THAI_DIR / "an"
    if an_dir.exists():
        for f in an_dir.iterdir():
            if f.name.endswith('.json') and f.name not in AN_VOLUME_FILES:
                f.unlink()
                deleted += 1

    # Abhidhamma: keep only volume files
    abh_dir = THAI_DIR / "abhidhamma"
    if abh_dir.exists():
        for f in abh_dir.iterdir():
            if f.name.endswith('.json') and f.name not in ABHIDHAMMA_VOLUME_FILES:
                f.unlink()
                deleted += 1

    # SN: keep only volume files
    sn_dir = THAI_DIR / "sn"
    if sn_dir.exists():
        sn_volume_files = {f'sn_vol{i}.json' for i in range(1, 6)}
        for f in sn_dir.iterdir():
            if f.name.endswith('.json') and f.name not in sn_volume_files:
                f.unlink()
                deleted += 1

    # DN: keep only volume files
    dn_dir = THAI_DIR / "dn"
    if dn_dir.exists():
        dn_volume_files = {f'dn_vol{i}.json' for i in range(1, 4)}
        for f in dn_dir.iterdir():
            if f.name.endswith('.json') and f.name not in dn_volume_files:
                f.unlink()
                deleted += 1

    # MN: keep only volume files
    mn_dir = THAI_DIR / "mn"
    if mn_dir.exists():
        mn_volume_files = {f'mn_vol{i}.json' for i in range(1, 4)}
        for f in mn_dir.iterdir():
            if f.name.endswith('.json') and f.name not in mn_volume_files:
                f.unlink()
                deleted += 1

    print(f"Cleanup: deleted {deleted} wrongly-generated files")
    return deleted


# ==================== KN Splitting ====================

def split_kn():
    """Split KN combined volumes into per-text files."""
    kn_dir = THAI_DIR / "kn"
    total = 0

    # --- kn_minor.json → kp, dhp, ud, iti, snp ---
    minor_file = kn_dir / "kn_minor.json"
    if minor_file.exists():
        text = load_thai_json(minor_file)
        print("  Splitting kn_minor.json (KP + Dhp + Ud + Iti + Snp)...")

        # Find text boundaries using header patterns
        dhp_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+dhammapad',
            text, re.IGNORECASE)
        ud_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+udānaṃ',
            text, re.IGNORECASE)
        iti_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+itivuttakaṃ',
            text, re.IGNORECASE)
        snp_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+suttanipāt',
            text, re.IGNORECASE)

        boundaries = []
        if dhp_start:
            boundaries.append(('dhp', dhp_start.start()))
        if ud_start:
            boundaries.append(('ud', ud_start.start()))
        if iti_start:
            boundaries.append(('iti', iti_start.start()))
        if snp_start:
            boundaries.append(('snp', snp_start.start()))

        if not boundaries:
            print("    WARNING: Could not find text boundaries in kn_minor.json")
        else:
            # KP is everything before the first boundary
            kp_text = text[:boundaries[0][1]]
            save_text(kn_dir, 'kp.json', 'kp', kp_text)
            print(f"    kp: {len(tokenize(kp_text)):,} words")
            total += 1

            # Each subsequent text runs from its start to the next boundary
            for i, (name, start) in enumerate(boundaries):
                end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
                section = text[start:end]
                save_text(kn_dir, f'{name}.json', name, section)
                print(f"    {name}: {len(tokenize(section)):,} words")
                total += 1

    # --- kn_verse.json → vv, pv, thag, thig ---
    verse_file = kn_dir / "kn_verse.json"
    if verse_file.exists():
        text = load_thai_json(verse_file)
        print("  Splitting kn_verse.json (Vv + Pv + Thag + Thig)...")

        pv_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+petavatthu',
            text, re.IGNORECASE)
        thag_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+theragāthā',
            text, re.IGNORECASE)
        thig_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+therīgāthā',
            text, re.IGNORECASE)

        boundaries = []
        if pv_start:
            boundaries.append(('pv', pv_start.start()))
        if thag_start:
            boundaries.append(('thag', thag_start.start()))
        if thig_start:
            boundaries.append(('thig', thig_start.start()))

        if not boundaries:
            print("    WARNING: Could not find text boundaries in kn_verse.json")
        else:
            # Vv is everything before Pv
            vv_text = text[:boundaries[0][1]]
            save_text(kn_dir, 'vv.json', 'vv', vv_text)
            print(f"    vv: {len(tokenize(vv_text)):,} words")
            total += 1

            for i, (name, start) in enumerate(boundaries):
                end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
                section = text[start:end]
                save_text(kn_dir, f'{name}.json', name, section)
                print(f"    {name}: {len(tokenize(section)):,} words")
                total += 1

    # --- ap.json → tha-ap, thi-ap, bv, cp ---
    ap_file = kn_dir / "ap.json"
    if ap_file.exists():
        text = load_thai_json(ap_file)
        print("  Splitting ap.json (Tha-ap + Thi-ap + Bv + Cp)...")

        # Find Therī-Apadāna start
        thi_start = re.search(r'therīapadānaṃ', text, re.IGNORECASE)
        # Find Buddhavaṃsa header
        bv_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+buddhavaṃso',
            text, re.IGNORECASE)
        # Find Cariyāpiṭaka header
        cp_start = re.search(
            r'suttantapiṭake\s+khuddakanikāyassa\s+cariyāpiṭakaṃ',
            text, re.IGNORECASE)

        boundaries = []
        if thi_start:
            boundaries.append(('thi-ap', thi_start.start()))
        if bv_start:
            boundaries.append(('bv', bv_start.start()))
        if cp_start:
            boundaries.append(('cp', cp_start.start()))

        if not boundaries:
            print("    WARNING: Could not find text boundaries in ap.json")
        else:
            # Thera-Apadāna is everything before Therī-Apadāna
            tha_text = text[:boundaries[0][1]]
            save_text(kn_dir, 'tha-ap.json', 'tha-ap', tha_text)
            print(f"    tha-ap: {len(tokenize(tha_text)):,} words")
            total += 1

            for i, (name, start) in enumerate(boundaries):
                end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
                section = text[start:end]
                save_text(kn_dir, f'{name}.json', name, section)
                print(f"    {name}: {len(tokenize(section)):,} words")
                total += 1

    print(f"  KN total: {total} per-text files created")
    return total


# ==================== Abhidhamma Splitting ====================

def split_abhidhamma():
    """Split Abhidhamma combined volume into per-text files."""
    abh_dir = THAI_DIR / "abhidhamma"
    total = 0

    # dhatukatha_puggalapannatti.json → dhatukatha, puggalapannatti
    combined_file = abh_dir / "dhatukatha_puggalapannatti.json"
    if combined_file.exists():
        text = load_thai_json(combined_file)
        print("  Splitting dhatukatha_puggalapannatti.json...")

        # Find Puggalapaññatti header
        pp_start = re.search(
            r'abhidhammapiṭake\s+puggalapaññatti',
            text, re.IGNORECASE)

        if pp_start:
            dk_text = text[:pp_start.start()]
            pp_text = text[pp_start.start():]

            save_text(abh_dir, 'dhatukatha.json', 'dhatukatha', dk_text)
            save_text(abh_dir, 'puggalapannatti.json', 'puggalapannatti', pp_text)
            print(f"    dhatukatha: {len(tokenize(dk_text)):,} words")
            print(f"    puggalapannatti: {len(tokenize(pp_text)):,} words")
            total += 2
        else:
            print("    WARNING: Could not find puggalapaññatti boundary")

    print(f"  Abhidhamma total: {total} per-text files created")
    return total


# ==================== DN Splitting ====================

# DN sutta names for title matching
DN_NAMES = {
    'brahmajāla': 1, 'sāmaññaphala': 2, 'ambaṭṭha': 3,
    'soṇadaṇḍa': 4, 'kūṭadanta': 5,
    'mahāli': 6, 'mahālī': 6,
    'jāliya': 7,
    'sīhanāda': 8, 'kassapasīhanāda': 8, 'mahāsīhanāda': 8,
    'poṭṭhapāda': 9, 'subha': 10,
    'kevaḍḍha': 11, 'kevaṭṭa': 11, 'lohicca': 12, 'tevijja': 13,
    'mahāpadāna': 14, 'mahānidāna': 15, 'mahāparinibbāna': 16,
    'mahāsudassana': 17, 'janavasabha': 18, 'mahāgovinda': 19,
    'mahāsamaya': 20, 'sakkapañha': 21,
    'mahāsatipaṭṭhāna': 22,
    'pāyāsirājañña': 23, 'pāyāsi': 23,
    'pāṭika': 24, 'pāthika': 24, 'udumbarika': 25,
    'cakkavattisīhanāda': 26, 'cakkavatti': 26,
    'aggañña': 27, 'sampasādanīya': 28, 'sampasādaniya': 28,
    'pāsādika': 29,
    'lakkhaṇa': 30, 'sigāla': 31, 'sigālovāda': 31, 'siṅgālaka': 31,
    'āṭānāṭiya': 32, 'saṅgīti': 33, 'dasuttara': 34,
}

DN_VOL_RANGES = [(1, 13), (14, 23), (24, 34)]


def split_dn():
    """Split DN volumes into per-sutta files using title markers."""
    output_dir = THAI_DIR / "dn"
    print("Splitting DN...")
    total = 0

    for vol_idx, (sutta_start, sutta_end) in enumerate(DN_VOL_RANGES):
        vol_num = vol_idx + 1
        vol_file = output_dir / f"dn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        text = load_thai_json(vol_file)
        starts = {}  # dn_num → position

        def add_start(dn_num, pos):
            if sutta_start <= dn_num <= sutta_end and dn_num not in starts:
                starts[dn_num] = pos

        def is_ending(pos):
            following = text[pos:pos + 150]
            return 'niṭṭhita' in following.lower()

        # Pattern A: {name}suttaṃ {ordinal} [page]
        for m in re.finditer(
            r'([\wāīūṭḍṇṅñṃḷ]+)suttaṃ\s+(?:paṭhamaṃ|dutiyaṃ|tatiyaṃ|catutthaṃ|'
            r'pañcamaṃ|chaṭṭhaṃ|sattamaṃ|aṭṭhamaṃ|navamaṃ|dasamaṃ|'
            r'ekādasamaṃ|dvādasamaṃ|terasamaṃ)\s*\[',
            text, re.IGNORECASE
        ):
            if is_ending(m.start()):
                continue
            name = m.group(1).lower()
            dn_num = DN_NAMES.get(name)
            if dn_num:
                add_start(dn_num, m.start())

        # Pattern B: {name}suttaṃ [page] evamme (no ordinal)
        for m in re.finditer(
            r'([\wāīūṭḍṇṅñṃḷ]+)suttaṃ\s+\[\d+\]\s+evamme',
            text, re.IGNORECASE
        ):
            if is_ending(m.start()):
                continue
            name = m.group(1).lower()
            dn_num = DN_NAMES.get(name)
            if dn_num:
                add_start(dn_num, m.start())

        # Pattern C: {name}suttaṃ {number} [page] (numeric ordinal)
        for m in re.finditer(
            r'([\wāīūṭḍṇṅñṃḷ]+)suttaṃ\s+\d+\s+\[\d+\]\s+evamme',
            text, re.IGNORECASE
        ):
            if is_ending(m.start()):
                continue
            name = m.group(1).lower()
            dn_num = DN_NAMES.get(name)
            if dn_num:
                add_start(dn_num, m.start())

        # Sort by position and extract text
        sorted_starts = sorted(starts.items(), key=lambda x: x[1])

        for i, (dn_num, start) in enumerate(sorted_starts):
            end = sorted_starts[i + 1][1] if i + 1 < len(sorted_starts) else len(text)
            sutta_text = text[start:end]
            save_text(output_dir, f"dn{dn_num}.json", f"dn{dn_num}", sutta_text,
                      extra={"sutta": dn_num})
            total += 1

        found = sorted(starts.keys())
        print(f"  Vol {vol_num}: {len(sorted_starts)} suttas "
              f"(DN {sutta_start}-{sutta_end}, found {found})")

    print(f"  DN total: {total} per-sutta files")
    return total


# ==================== MN Splitting ====================

def split_mn():
    """Split MN volumes into per-sutta files.

    Uses 'evamme sutaṃ' as the primary sutta boundary marker (every MN sutta
    starts with this formula). Falls back to {name}suttaṃ title for sutta start
    position when the title precedes evamme.
    """
    output_dir = THAI_DIR / "mn"
    print("Splitting MN...")
    total = 0

    MN_VOL_RANGES = [(1, 50), (51, 100), (101, 152)]

    for vol_idx, (sutta_start, sutta_end) in enumerate(MN_VOL_RANGES):
        vol_num = vol_idx + 1
        vol_file = output_dir / f"mn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        text = load_thai_json(vol_file)

        # Find all 'evamme sutaṃ' occurrences
        evamme_positions = [m.start() for m in re.finditer(
            r'evamme sutaṃ', text, re.IGNORECASE)]

        # For each evamme, look backwards for the sutta title
        # Title pattern: {name}suttaṃ [page] appears before evamme
        sutta_positions = []
        for ev_pos in evamme_positions:
            # Look back up to 200 chars for {name}suttaṃ [N]
            lookback = text[max(0, ev_pos - 200):ev_pos]
            title_match = None
            for m in re.finditer(
                r'([\wāīūṭḍṇṅñṃḷ]+)suttaṃ\s+\[\d+\]',
                lookback, re.IGNORECASE
            ):
                if len(m.group(1)) >= 4:
                    title_match = m

            if title_match:
                # Use the title position as sutta start
                title_pos = max(0, ev_pos - 200) + title_match.start()
                sutta_positions.append(title_pos)
            else:
                # No title found — use evamme position directly
                sutta_positions.append(ev_pos)

        sutta_positions = sorted(set(sutta_positions))

        # Assign sequential MN numbers
        expected = sutta_end - sutta_start + 1
        for i, pos in enumerate(sutta_positions):
            mn_num = sutta_start + i
            if mn_num > sutta_end:
                break
            end = sutta_positions[i + 1] if i + 1 < len(sutta_positions) else len(text)
            sutta_text = text[pos:end]
            save_text(output_dir, f"mn{mn_num}.json", f"mn{mn_num}", sutta_text,
                      extra={"sutta": mn_num})
            total += 1

        found_count = min(len(sutta_positions), expected)
        print(f"  Vol {vol_num}: {found_count}/{expected} suttas "
              f"(MN {sutta_start}-{sutta_end})")

    print(f"  MN total: {total} per-sutta files")
    return total


# ==================== SN Splitting ====================

# Mapping of saṃyutta name stems → saṃyutta numbers
SN_SAMYUTTA_NAMES = {
    'devatā': 1, 'devaputta': 2, 'kosala': 3, 'māra': 4, 'bhikkhunī': 5,
    'brahma': 6, 'brāhmaṇa': 7, 'vaṅgīsa': 8, 'vana': 9,
    'yakkha': 10, 'sakka': 11,
    'nidāna': 12, 'abhisamaya': 12, 'abhisamayadhātu': 12,
    'dhātu': 14, 'anamatagga': 15,
    'kassapa': 16, 'lābhasakkāra': 17, 'rāhula': 18, 'lakkhaṇa': 19,
    'opamma': 20, 'bhikkhu': 21,
    'khandha': 22, 'rādha': 23, 'diṭṭhi': 24,
    'okkanta': 25, 'uppāda': 26, 'kilesa': 27,
    'sārīputta': 28, 'nāga': 29, 'supaṇṇa': 30, 'gandhabbakāya': 31,
    'valāhaka': 32, 'vacchagotta': 33, 'jhāna': [34, 53], 'samādhi': 34,
    'saḷāyatana': 35, 'vedanā': 36, 'mātugāma': 37, 'jambukhādaka': 38,
    'sāmaṇḍaka': 39, 'moggallāna': 40,
    'citta': 41, 'cittagahapatipucchā': 41,
    'gāmaṇi': 42, 'gāmaṇī': 42,
    'asaṅkhata': 43, 'abyākata': 44,
    'magga': 45, 'bojjhaṅga': 46, 'satipaṭṭhāna': 47, 'indriya': 48,
    'sammappadhāna': 49, 'bala': 50, 'iddhipāda': 51,
    'anuruddha': 52, 'ānāpāna': 54,
    'sotāpatti': 55, 'sacca': 56,
}

# SN volume → saṃyutta ranges
SN_VOL_SAMYUTTAS = [
    (1, 11),   # Vol 1: Sagāthāvagga
    (12, 21),  # Vol 2: Nidānavagga
    (22, 34),  # Vol 3: Khandhavagga
    (35, 44),  # Vol 4: Saḷāyatanavagga
    (45, 56),  # Vol 5: Mahāvagga
]


def _find_samyutta_regions(text, sam_start, sam_end):
    """Find saṃyutta text regions within a volume.

    Uses both start headers ({name}saṃyuttaṃ + vagga/underscore) and
    end markers ({name}saṃyuttaṃ samattaṃ/niṭṭhitaṃ) to build regions.

    Returns dict of sam_num → (start_pos, end_pos).
    """
    # Collect all saṃyutta markers
    starts = {}  # sam_num → position
    ends = {}    # sam_num → position

    for m in re.finditer(r'([a-zāīūṭḍṇṅñṃḷ]+)saṃyuttaṃ', text, re.IGNORECASE):
        name = m.group(1).lower()
        if 'vagga' in name or 'nikāya' in name or 'mahāvāra' in name:
            continue
        # Also skip if name is very short (probably part of another word)
        if len(name) < 3:
            continue

        sam_value = SN_SAMYUTTA_NAMES.get(name)
        if sam_value is None:
            continue
        # Handle list values (e.g., 'jhāna' maps to both 34 and 53)
        candidates = sam_value if isinstance(sam_value, list) else [sam_value]
        sam_num = None
        for c in candidates:
            if sam_start <= c <= sam_end:
                sam_num = c
                break
        if sam_num is None:
            continue

        after = text[m.end():m.end()+30].strip()

        # Check if this is an ending
        if 'samattaṃ' in after or 'niṭṭhitaṃ' in after:
            if sam_num not in ends:
                ends[sam_num] = m.end() + 30  # past the ending marker
            continue

        # Check if this is a start (followed by vagga/underscore/bracket/page)
        if re.match(r'[\s_]+|[a-zāīūṭḍṇṅñṃḷ]+vaggo|\[\d+\]',
                    after, re.IGNORECASE):
            if sam_num not in starts:
                starts[sam_num] = m.start()

    # Build regions: combine starts and ends
    regions = {}

    # First saṃyutta always starts at beginning of volume
    if sam_start not in starts:
        starts[sam_start] = 0

    # For each saṃyutta in range, determine its region
    for sam in range(sam_start, sam_end + 1):
        # Start: use detected start, or end of previous saṃyutta
        if sam in starts:
            s = starts[sam]
        else:
            # Search backward for nearest end marker
            found = False
            for prev in range(sam - 1, sam_start - 1, -1):
                if prev in ends:
                    s = ends[prev]
                    found = True
                    break
            if not found:
                continue  # Can't determine start

        # End: use end of this saṃyutta, or start of next, or volume end
        e = len(text)
        if sam in ends:
            e = ends[sam]
        else:
            # Look for start of next saṃyutta
            for next_sam in range(sam + 1, sam_end + 1):
                if next_sam in starts:
                    e = starts[next_sam]
                    break

        if s < e:
            regions[sam] = (s, e)

    return regions


def split_sn():
    """Split SN volumes into per-sutta files.

    Uses GRETIL-anchored alignment (text similarity) for all volumes.
    """
    output_dir = THAI_DIR / "sn"
    gretil_dir = DATA_DIR / "gretil-parsed/sn"
    print("Splitting SN...")
    total = 0

    # Load GRETIL summary for sutta counts
    summary_file = gretil_dir / "_summary.json"
    if summary_file.exists():
        samyutta_counts = json.loads(summary_file.read_text()
                                     ).get('samyutta_counts', {})
    else:
        samyutta_counts = {}

    for vol_idx, (sam_start, sam_end) in enumerate(SN_VOL_SAMYUTTAS):
        vol_num = vol_idx + 1
        vol_file = output_dir / f"sn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        text = load_thai_json(vol_file)
        vol_total = 0

        # All volumes: GRETIL-anchored alignment
        all_gretil = []
        for sam in range(sam_start, sam_end + 1):
            all_gretil.extend(load_gretil_suttas('sn', sam))

        if not all_gretil:
            continue

        thai_words, thai_positions = tokenize_with_positions(text)
        results = align_gretil_to_thai_text(
            all_gretil, thai_words, thai_positions, use_titles=True)

        # Save per-sutta files using aligned positions
        for i, (sutta_file_id, word_idx, conf, method) in enumerate(results):
            # Determine char range: from this word to next sutta's word
            char_start = thai_positions[word_idx] if word_idx < len(thai_positions) else 0
            if i + 1 < len(results):
                next_word_idx = results[i + 1][1]
                char_end = thai_positions[next_word_idx] if next_word_idx < len(thai_positions) else len(text)
            else:
                char_end = len(text)
            sutta_text = text[char_start:char_end]

            # Extract samyutta and sutta number from file id (sn22_1)
            parts = sutta_file_id.replace('sn', '').split('_')
            sam_num = int(parts[0])
            sutta_num = int(parts[1])

            save_text(output_dir, f"{sutta_file_id}.json", sutta_file_id,
                      sutta_text,
                      extra={"sutta": f"sn{sam_num}.{sutta_num}"})
            vol_total += 1

        total += vol_total
        expected_total = sum(
            int(samyutta_counts.get(str(s), 0))
            for s in range(sam_start, sam_end + 1))
        print(f"  Vol {vol_num}: {vol_total}/{expected_total} suttas "
              f"(SN {sam_start}-{sam_end})")

    print(f"  SN total: {total} per-sutta files")
    return total


# ==================== AN Splitting ====================

# Nipāta name → number mapping
AN_NIPATA_NAMES = {
    'eka': 1, 'duka': 2, 'tika': 3, 'catukka': 4, 'pañcaka': 5,
    'chakka': 6, 'sattaka': 7, 'aṭṭhaka': 8, 'navaka': 9,
    'dasaka': 10, 'ekādasaka': 11,
}

# AN volume → nipāta ranges (Thai Royal Edition layout)
AN_VOL_NIPATAS = [
    (1, 3),    # Vol 1: Eka+Duka+Tikanipāta
    (4, 4),    # Vol 2: Catukkanipāta
    (5, 6),    # Vol 3: Pañcaka+Chakkanipāta
    (7, 9),    # Vol 4: Sattaka+Aṭṭhaka+Navakanipāta
    (10, 11),  # Vol 5: Dasaka+Ekādasakanipāta
]


def _find_an_sutta_starts_by_vagga(text):
    """Find vagga-level boundaries in AN text (for AN 1-3).

    GRETIL AN 1-3 treats each vagga as a "sutta", so vagga boundaries
    are the correct splitting unit. Returns positions of vagga starts.
    """
    # Find vagga ending markers: 'vaggo {footnote}? {ordinal} .'
    vagga_ordinals = (
        'paṭhamo', 'dutiyo', 'tatiyo', 'catuttho', 'pañcamo',
        'chaṭṭho', 'sattamo', 'aṭṭhamo', 'navamo', 'dasamo',
        'ekādasamo', 'dvādasamo', 'terasamo', 'cuddasamo',
        'pannarasamo', 'soḷasamo', 'sattarasamo', 'aṭṭhārasamo',
        'ekūnavīsatimo', 'vīsatimo')
    ord_pat = '|'.join(vagga_ordinals)
    endings = list(re.finditer(
        rf'vaggo\s*\d*\s*({ord_pat})\s*\.',
        text, re.IGNORECASE))

    # Vagga starts: position 0 plus position after each vagga ending
    positions = [0]
    for m in endings:
        positions.append(m.end())
    return positions


def _find_an_sutta_starts_by_bracket(text):
    """Find sutta boundaries using monotonically increasing bracket numbers.

    In AN 4+, bracket numbers [N] mark individual sutta starts. Footnote
    brackets also use [N] but don't follow the monotonic sequence.
    We filter by only accepting brackets whose number > previous accepted.
    """
    positions = []
    last_num = 0

    for m in re.finditer(r'\[(\d+)\]', text):
        num = int(m.group(1))
        if num > last_num:
            positions.append(m.start())
            last_num = num

    return positions


def split_an():
    """Split AN volumes into per-sutta files.

    Uses different strategies by nipāta:
    - AN 1-3 (vol1): vagga-level splitting (GRETIL treats vaggas as suttas)
    - AN 4-11 (vol2-5): bracket-based splitting with monotonic filtering
    """
    output_dir = THAI_DIR / "an"
    gretil_dir = DATA_DIR / "gretil-parsed/an"
    print("Splitting AN...")
    total = 0

    # Load GRETIL summary for expected counts
    summary_file = gretil_dir / "_summary.json"
    if summary_file.exists():
        nipata_counts = json.loads(summary_file.read_text()
                                   ).get('nipata_counts', {})
    else:
        nipata_counts = {}

    for vol_idx, (nip_start, nip_end) in enumerate(AN_VOL_NIPATAS):
        vol_num = vol_idx + 1
        vol_file = output_dir / f"an_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        text = load_thai_json(vol_file)
        vol_total = 0

        # Find nipāta boundaries
        nipata_starts = {}
        for m in re.finditer(
            r'([\wāīūṭḍṇṅñṃḷ]+)nipāto',
            text, re.IGNORECASE
        ):
            name = m.group(1).lower()
            after_nipato = text[m.end():m.end() + 30]
            if 'samatt' in after_nipato or 'niṭṭhit' in after_nipato:
                continue
            # Check longest stems first to avoid partial matches
            # (e.g., 'ekādasaka' matching 'dasaka' before 'ekādasaka')
            for stem, num in sorted(AN_NIPATA_NAMES.items(),
                                    key=lambda x: -len(x[0])):
                if name.endswith(stem) or name == stem:
                    if nip_start <= num <= nip_end and num not in nipata_starts:
                        nipata_starts[num] = m.start()
                    break

        if not nipata_starts:
            if nip_start == nip_end:
                nipata_starts[nip_start] = 0
            else:
                print(f"  Vol {vol_num}: WARNING - no nipāta headers found")
                continue

        sorted_nips = sorted(nipata_starts.items())

        for ni, (nip_num, nip_start_pos) in enumerate(sorted_nips):
            nip_end_pos = (sorted_nips[ni + 1][1]
                           if ni + 1 < len(sorted_nips) else len(text))
            nip_text = text[nip_start_pos:nip_end_pos]
            expected = int(nipata_counts.get(str(nip_num), 0))

            if nip_num <= 3:
                # AN 1-3: GRETIL-anchored alignment
                gretil = load_gretil_suttas('an', nip_num)
                if not gretil:
                    continue
                thai_words, thai_pos = tokenize_with_positions(nip_text)
                results = align_gretil_to_thai_text(
                    gretil, thai_words, thai_pos, use_titles=False)

                for ri, (sutta_file_id, word_idx, conf, method) in enumerate(results):
                    char_start = thai_pos[word_idx] if word_idx < len(thai_pos) else 0
                    if ri + 1 < len(results):
                        next_word_idx = results[ri + 1][1]
                        char_end = thai_pos[next_word_idx] if next_word_idx < len(thai_pos) else len(nip_text)
                    else:
                        char_end = len(nip_text)
                    sutta_text = nip_text[char_start:char_end]

                    parts = sutta_file_id.replace('an', '').split('_')
                    sutta_num = int(parts[1])

                    save_text(output_dir, f"{sutta_file_id}.json",
                              sutta_file_id, sutta_text,
                              extra={"sutta": f"an{nip_num}.{sutta_num}"})
                    vol_total += 1

                if len(results) != expected and expected > 0:
                    print(f"    AN {nip_num}: {len(results)}/{expected} (GRETIL-anchored)")
            else:
                # AN 4+: bracket-based sutta splitting
                positions = _find_an_sutta_starts_by_bracket(nip_text)
                count = (min(len(positions), expected)
                         if expected > 0 else len(positions))

                for i in range(count):
                    sutta_num = i + 1
                    start = positions[i]
                    end = (positions[i + 1] if i + 1 < len(positions)
                           else len(nip_text))
                    sutta_text = nip_text[start:end]
                    sutta_id = f"an{nip_num}_{sutta_num}"
                    save_text(output_dir, f"{sutta_id}.json", sutta_id,
                              sutta_text,
                              extra={"sutta": f"an{nip_num}.{sutta_num}"})
                    vol_total += 1

                if count != expected and expected > 0:
                    print(f"    AN {nip_num}: {count}/{expected} suttas")

        total += vol_total
        print(f"  Vol {vol_num}: {vol_total} suttas "
              f"(AN {sorted_nips[0][0]}-{sorted_nips[-1][0]})")

    print(f"  AN total: {total} per-sutta files")
    return total


# ==================== Main ====================

def main():
    targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {'all'}

    if 'all' in targets or 'cleanup' in targets:
        cleanup()
        print()

    if 'all' in targets or 'kn' in targets:
        print("KN (Khuddaka Nikāya)")
        split_kn()
        print()

    if 'all' in targets or 'abhidhamma' in targets:
        print("ABHIDHAMMA")
        split_abhidhamma()
        print()

    if 'all' in targets or 'dn' in targets:
        split_dn()
        print()

    if 'all' in targets or 'mn' in targets:
        split_mn()
        print()

    if 'all' in targets or 'sn' in targets:
        split_sn()
        print()

    if 'all' in targets or 'an' in targets:
        split_an()
        print()


if __name__ == '__main__':
    main()
