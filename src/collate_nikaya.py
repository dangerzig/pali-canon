#!/usr/bin/env python3
"""
Collate variants across editions for any nikaya or pitaka.

Usage:
    python collate_nikaya.py dn           # Collate DN (Dīgha Nikāya)
    python collate_nikaya.py mn           # Collate MN (Majjhima Nikāya)
    python collate_nikaya.py sn           # Collate SN (Saṃyutta Nikāya)
    python collate_nikaya.py an           # Collate AN (Aṅguttara Nikāya)
    python collate_nikaya.py kn           # Collate KN (Khuddaka Nikāya)
    python collate_nikaya.py vinaya       # Collate Vinaya Piṭaka
    python collate_nikaya.py abhidhamma   # Collate Abhidhamma Piṭaka

Classification rules:
- Orthographic only (ṁ/ṃ, ṅ/ṃ): Normalize silently
- SC=VRI≠PTS + PTS not in DPD: Error - correct and note
- SC=VRI≠PTS + all valid words: Variant - record in apparatus
- All three differ: Uncertain - flag for review
- Two-way mode (no VRI): SC≠PTS classification based on DPD validation
"""

import re
import sys
import json
import warnings
from pathlib import Path
from collections import Counter
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
    'kn': ('kn', 'khuddaka'),  # Special handling for Khuddaka texts
    'vinaya': ('vinaya', 'vinaya'),  # Vinaya Piṭaka
    'abhidhamma': ('abhidhamma', 'abhidhamma'),  # Abhidhamma Piṭaka
}

# KN text mappings: (SC abbrev, GRETIL name, VRI CST code, BJT name, Thai name)
# VRI CST code is None if not available in VRI
# BJT/Thai name is None if not available
KN_TEXTS = [
    ('kp', 'khuddakapatha', 's0501m.mul', 'khuddakapatha', 'kp'),
    ('dhp', 'dhammapada', 's0502m.mul', 'dhammapada', 'dhp'),
    ('ud', 'udana', 's0503m.mul', 'udana', 'ud'),
    ('iti', 'itivuttaka', 's0504m.mul', 'itivuttaka', 'iti'),
    ('snp', 'suttanipata', 's0505m.mul', 'suttanipata', 'snp'),
    ('vv', 'vimanavatthu', 's0506m.mul', 'vimanavatthu', 'vv'),
    ('pv', 'petavatthu', 's0507m.mul', 'petavatthu', 'pv'),
    ('thag', 'theragatha', 's0508m.mul', 'theragatha', 'thag'),
    ('thig', 'therigatha', 's0509m.mul', 'therigatha', 'thig'),
    ('tha-ap', 'apadana', 's0510m1.mul', 'apadana1', 'tha-ap'),  # Thera-apadāna (part 1)
    ('thi-ap', 'apadana', 's0510m2.mul', 'apadana2', 'thi-ap'),  # Therī-apadāna (part 2), same GRETIL file
    ('bv', 'buddhavamsa', 's0511m.mul', 'buddhavamsa', 'bv'),
    ('cp', 'cariyapitaka', 's0512m.mul', 'cariyapitaka', 'cp'),
    ('ja', 'jataka', 's0513m.mul', 'jataka', 'ja'),  # Jātaka vol 1 (GRETIL has jataka1-6, BJT has jataka1-6)
    ('mnd', 'mahaniddesa', 's0515m.mul', 'mahaniddesa', 'mnd'),
    ('cnd', 'cullaniddesa', 's0516m.mul', 'cullaniddesa', 'cnd'),
    ('ps', 'patisambhidamagga', 's0517m.mul', 'patisambhidamagga', 'ps'),  # GRETIL/BJT have 1-2
    # Not in VRI:
    ('ne', None, None, None, None),  # Netti - not in GRETIL, VRI, BJT, or Thai
    ('pe', None, None, None, None),  # Peṭakopadesa - not in GRETIL, VRI, BJT, or Thai
    ('mil', None, None, None, None),  # Milindapañha - not in GRETIL, VRI, BJT, or Thai
]

# Vinaya text mappings: (name, GRETIL name, VRI codes, SC name, BJT name, Thai name)
# VRI CST codes: vin01m.mul = Pārājika (Suttavibhaṅga 1)
#                vin02m1.mul = Pācittiya (Suttavibhaṅga 2)
#                vin02m2.mul = Mahāvagga
#                vin02m3.mul = Cūḷavagga
#                vin02m4.mul = Parivāra
VINAYA_TEXTS = [
    ('suttavibhanga1', 'suttavibhanga1', ['vin01m.mul'], 'suttavibhanga1', 'suttavibhanga1', 'suttavibhanga1'),
    ('suttavibhanga2', 'suttavibhanga2', ['vin02m1.mul'], 'suttavibhanga2', 'suttavibhanga2', 'suttavibhanga2'),
    ('mahavagga', 'mahavagga', ['vin02m2.mul'], 'mahavagga', 'mahavagga', 'mahavagga'),
    ('cullavagga', 'cullavagga', ['vin02m3.mul'], 'cullavagga', 'cullavagga', 'cullavagga'),
    ('parivara', 'parivara', ['vin02m4.mul'], 'parivara', 'parivara', 'parivara'),
]

# Abhidhamma text mappings: (name, GRETIL name, VRI codes, SC name, BJT name, Thai name)
# VRI codes: abh01m.mul = Dhammasaṅgaṇī, abh02m.mul = Vibhaṅga
#            abh03m1 = Dhātukathā, abh03m2 = Puggalapaññatti
#            abh03m3 = Kathāvatthu, abh03m4-6 = Yamaka, abh03m7-11 = Paṭṭhāna
ABHIDHAMMA_TEXTS = [
    # (name, gretil_name, vri_codes, sc_name, bjt_name, thai_name)
    # gretil_name: if no exact .json match, globs {name}*.json and combines
    # sc_name/bjt_name/thai_name: str for single file, list for multiple files, None if unavailable
    ('dhammasangani', 'dhammasangani', ['abh01m.mul'], 'dhammasangani', 'dhammasangani', 'dhammasangani'),
    ('vibhanga', 'vibhanga', ['abh02m.mul'], 'vibhanga', 'vibhanga', 'vibhanga'),
    ('dhatukatha', 'dhatukatha', ['abh03m1.mul'], 'dhatukatha', 'dhatukatha', 'dhatukatha'),
    ('puggalapannatti', 'puggalapannatti', ['abh03m2.mul'], 'puggalapannatti', 'puggalapannatti', 'puggalapannatti'),
    ('kathavatthu', 'kathavatthu', ['abh03m3.mul'], 'kathavatthu', ['kathavatthu1', 'kathavatthu2'], 'kathavatthu'),
    # Yamaka: combined (split points differ across witnesses — GRETIL/BJT at 7/8, SC at 5/6, VRI 3 vols)
    ('yamaka', 'yamaka', ['abh03m4.mul', 'abh03m5.mul', 'abh03m6.mul'], 'yamaka', ['yamaka1', 'yamaka2'], 'yamaka'),
    # Patthana: combined (GRETIL has 4 files: patthana1-3 + patthana_duka)
    ('patthana', 'patthana', ['abh03m7.mul', 'abh03m8.mul', 'abh03m10.mul', 'abh03m11.mul'], 'patthana', ['patthana1', 'patthana2'], 'patthana'),
]

# Import canonical tokenization pattern from shared module
try:
    from pali.text import PALI_WORD_PATTERN
except ImportError:
    PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Cache for SC JSON files (avoids re-reading per sutta)
_sc_file_cache = {}


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


def clean_bjt_text(text: str) -> str:
    """Remove BJT-specific markers (section/sutta numbers)."""
    text = re.sub(r'^\s*\d+\.\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.[ ]+\d+\.[ ]+\d+(?:\.[ ]+\d+)?\.?\s*$', '', text, flags=re.MULTILINE)
    return text


def clean_thai_text(text: str) -> str:
    """Remove Thai Royal Edition-specific markers."""
    # Strip bracketed page numbers [N]
    text = re.sub(r'\[\d+\]', '', text)
    # Strip editorial variant annotations (#sī., #ma., #yu., #a., etc.)
    text = re.sub(r'#\w+\.', '', text)
    # Strip underscore separators
    text = text.replace('___', '')
    return text


# ==================== BJT Alignment Mapping ====================

_bjt_mappings = {}  # cache: nikaya → {gretil_id: {bjt_files: [...]}}


def load_bjt_mapping(nikaya: str) -> dict:
    """Load GRETIL→BJT sutta mapping for SN or AN.

    Returns dict: gretil_sutta_id → {'bjt_files': [...], 'confidence': float}
    """
    if nikaya not in _bjt_mappings:
        mapping_file = DATA_DIR / f"alignment/{nikaya}_bjt_mapping.json"
        if mapping_file.exists():
            data = json.loads(mapping_file.read_text())
            _bjt_mappings[nikaya] = data.get('mappings', {})
        else:
            _bjt_mappings[nikaya] = {}
    return _bjt_mappings[nikaya]


def load_bjt_via_mapping(nikaya: str, sutta_id: str) -> dict | None:
    """Load BJT text for a GRETIL sutta using the alignment mapping.

    Returns {'text': cleaned_text, 'raw_text': raw_text} or None.
    """
    mapping = load_bjt_mapping(nikaya)
    entry = mapping.get(sutta_id)
    if not entry:
        return None

    bjt_dir = DATA_DIR / f"bjt-parsed/{nikaya}"
    bjt_texts = []
    for bf in entry.get('bjt_files', []):
        bjt_file = bjt_dir / f"{bf}.json"
        if bjt_file.exists():
            bjt = json.loads(bjt_file.read_text())
            bjt_texts.append(bjt.get('text', ''))

    if bjt_texts:
        combined = ' '.join(bjt_texts)
        return {
            'text': clean_bjt_text(combined),
            'raw_text': combined,
        }
    return None


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


def align_witnesses(gretil_words: list, sc_words: list, vri_words: list,
                    bjt_words: list = None, thai_words: list = None) -> list:
    """Perform multi-way alignment across up to 5 witnesses (GRETIL/SC/VRI/BJT/Thai)."""
    gretil_sc = align_word_sequences(gretil_words, sc_words)
    gretil_vri = align_word_sequences(gretil_words, vri_words)

    combined = {}

    def _ensure_entry(idx, word):
        if idx not in combined:
            combined[idx] = {
                'gretil': word,
                'gretil_idx': idx,
                'sc': None, 'sc_idx': None,
                'vri': None, 'vri_idx': None,
                'bjt': None, 'bjt_idx': None,
                'thai': None, 'thai_idx': None,
                'sc_match': None, 'vri_match': None, 'bjt_match': None,
                'thai_match': None
            }

    for align in gretil_sc:
        idx = align.get('idx1')
        if idx is not None:
            _ensure_entry(idx, align['word1'])
            combined[idx]['sc'] = align['word2']
            combined[idx]['sc_idx'] = align.get('idx2')
            combined[idx]['sc_match'] = align['type']

    for align in gretil_vri:
        idx = align.get('idx1')
        if idx is not None:
            _ensure_entry(idx, align['word1'])
            combined[idx]['vri'] = align['word2']
            combined[idx]['vri_idx'] = align.get('idx2')
            combined[idx]['vri_match'] = align['type']

    if bjt_words is not None:
        gretil_bjt = align_word_sequences(gretil_words, bjt_words)
        for align in gretil_bjt:
            idx = align.get('idx1')
            if idx is not None:
                _ensure_entry(idx, align['word1'])
                combined[idx]['bjt'] = align['word2']
                combined[idx]['bjt_idx'] = align.get('idx2')
                combined[idx]['bjt_match'] = align['type']

    if thai_words is not None:
        gretil_thai = align_word_sequences(gretil_words, thai_words)
        for align in gretil_thai:
            idx = align.get('idx1')
            if idx is not None:
                _ensure_entry(idx, align['word1'])
                combined[idx]['thai'] = align['word2']
                combined[idx]['thai_idx'] = align.get('idx2')
                combined[idx]['thai_match'] = align['type']

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


def classify_variant(gretil: str, sc: str, vri: str, bjt: str = None,
                     thai: str = None) -> dict:
    """Classify a variant reading across up to 5 witnesses."""
    g = gretil.lower() if gretil else None
    s = sc.lower() if sc else None
    v = vri.lower() if vri else None
    b = bjt.lower() if bjt else None
    t = thai.lower() if thai else None

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
    b_norm = normalize_for_comparison(b) if b else None
    t_norm = normalize_for_comparison(t) if t else None

    # Check if all available witnesses agree after normalization
    all_agree = (g_norm == s_norm == v_norm)
    if all_agree and b_norm is not None and b_norm != g_norm:
        all_agree = False
    if all_agree and t_norm is not None and t_norm != g_norm:
        all_agree = False
    if all_agree:
        return {
            'type': 'orthographic',
            'confidence': 1.0,
            'preferred': g,
            'notes': 'All editions agree (orthographic normalization)'
        }

    # SC=VRI agree but differ from PTS
    if s_norm and v_norm and s_norm == v_norm and g_norm != s_norm:
        pts_valid = is_valid_word(g)
        sc_valid = is_valid_word(s)

        # Check if BJT/Thai side with majority (SC/VRI) or minority (PTS)
        bjt_with_majority = b_norm is not None and b_norm == s_norm
        bjt_with_pts = b_norm is not None and b_norm == g_norm
        thai_with_majority = t_norm is not None and t_norm == s_norm
        thai_with_pts = t_norm is not None and t_norm == g_norm

        # Count witnesses in majority coalition
        majority_count = 2  # SC + VRI
        if bjt_with_majority:
            majority_count += 1
        if thai_with_majority:
            majority_count += 1

        if not pts_valid and sc_valid:
            if majority_count >= 4:
                conf = 0.98
            elif majority_count == 3:
                conf = 0.95
            elif bjt_with_pts or thai_with_pts:
                conf = 0.85
            else:
                conf = 0.9
            # Build majority label
            majority_parts = ['SC', 'VRI']
            if bjt_with_majority:
                majority_parts.append('BJT')
            if thai_with_majority:
                majority_parts.append('Thai')
            others = '/'.join(majority_parts)
            # Build minority notes
            extra_notes = []
            if bjt_with_pts:
                extra_notes.append('BJT agrees with PTS')
            elif b and not bjt_with_majority:
                extra_notes.append(f'BJT has "{b}"')
            if thai_with_pts:
                extra_notes.append('Thai agrees with PTS')
            elif t and not thai_with_majority:
                extra_notes.append(f'Thai has "{t}"')
            note_suffix = ', ' + ', '.join(extra_notes) if extra_notes else ''
            return {
                'type': 'error',
                'confidence': conf,
                'preferred': s,
                'notes': f'PTS "{g}" not in DPD, {others} "{s}" is valid{note_suffix}'
            }
        elif pts_valid and sc_valid:
            if majority_count >= 4:
                conf = 0.9
            elif majority_count == 3:
                conf = 0.8
            elif bjt_with_pts or thai_with_pts:
                conf = 0.6
            else:
                conf = 0.7
            majority_parts = ['SC', 'VRI']
            if bjt_with_majority:
                majority_parts.append('BJT')
            if thai_with_majority:
                majority_parts.append('Thai')
            others = '/'.join(majority_parts)
            extra_notes = []
            if bjt_with_pts:
                extra_notes.append('BJT agrees with PTS')
            elif b and not bjt_with_majority:
                extra_notes.append(f'BJT has "{b}"')
            if thai_with_pts:
                extra_notes.append('Thai agrees with PTS')
            elif t and not thai_with_majority:
                extra_notes.append(f'Thai has "{t}"')
            note_suffix = ', ' + ', '.join(extra_notes) if extra_notes else ''
            return {
                'type': 'variant',
                'confidence': conf,
                'preferred': g,
                'notes': f'Textual variant: PTS "{g}" vs {others} "{s}"{note_suffix}'
            }
        else:
            return {
                'type': 'uncertain',
                'confidence': 0.4,
                'preferred': s,
                'notes': f'Neither reading validated: PTS "{g}" vs SC/VRI "{s}"'
            }

    # All three (G/S/V) disagree -- check if BJT/Thai create a majority
    if g_norm != s_norm and g_norm != v_norm and s_norm != v_norm:
        g_valid = is_valid_word(g)
        s_valid = is_valid_word(s) if s else False
        v_valid = is_valid_word(v) if v else False

        # Collect all witness norms for coalition detection
        witness_norms = {'PTS': g_norm}
        if s_norm:
            witness_norms['SC'] = s_norm
        if v_norm:
            witness_norms['VRI'] = v_norm
        if b_norm:
            witness_norms['BJT'] = b_norm
        if t_norm:
            witness_norms['Thai'] = t_norm

        # Find largest coalition
        norm_counts = Counter(witness_norms.values())
        most_common_norm, most_common_count = norm_counts.most_common(1)[0]

        if most_common_count >= 3:
            # 3+ witnesses agree — strong majority
            coalition = [k for k, vn in witness_norms.items() if vn == most_common_norm]
            # Find the actual reading text for the majority norm
            norm_to_reading = {'PTS': g, 'SC': s, 'VRI': v, 'BJT': b, 'Thai': t}
            preferred_reading = next((norm_to_reading[k] for k in coalition if norm_to_reading.get(k)), g)
            others = [f'{k} "{witness_norms[k]}"' for k in witness_norms if witness_norms[k] != most_common_norm]
            return {
                'type': 'uncertain',
                'confidence': 0.7,
                'preferred': preferred_reading,
                'notes': f'{"/".join(coalition)} "{preferred_reading}" vs {", ".join(others)}'
            }
        elif most_common_count == 2:
            # 2 witnesses agree
            coalition = [k for k, vn in witness_norms.items() if vn == most_common_norm]
            norm_to_reading = {'PTS': g, 'SC': s, 'VRI': v, 'BJT': b, 'Thai': t}
            preferred_reading = next((norm_to_reading[k] for k in coalition if norm_to_reading.get(k)), g)
            conf = 0.6 if (preferred_reading and is_valid_word(preferred_reading)) else 0.4
            others = [f'{k} "{witness_norms[k]}"' for k in witness_norms if witness_norms[k] != most_common_norm]
            return {
                'type': 'uncertain',
                'confidence': conf,
                'preferred': preferred_reading,
                'notes': f'{"/".join(coalition)} "{preferred_reading}" vs {", ".join(others)}'
            }

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
            extra = []
            if b:
                extra.append(f'BJT "{b}"')
            if t:
                extra.append(f'Thai "{t}"')
            extra_note = ', ' + ', '.join(extra) if extra else ''
            return {
                'type': 'uncertain',
                'confidence': 0.3,
                'preferred': g,
                'notes': f'Multi-way disagreement: PTS "{g}", SC "{s}", VRI "{v}"{extra_note}'
            }

    if g_norm == s_norm and g_norm != v_norm:
        bjt_confirms = b_norm is not None and b_norm == g_norm
        thai_confirms = t_norm is not None and t_norm == g_norm
        confirm_count = 2 + int(bjt_confirms) + int(thai_confirms)
        conf = min(0.9, 0.5 + confirm_count * 0.1)
        majority_parts = ['PTS', 'SC']
        if bjt_confirms:
            majority_parts.append('BJT')
        if thai_confirms:
            majority_parts.append('Thai')
        majority = '/'.join(majority_parts)
        return {
            'type': 'vri_variant',
            'confidence': conf,
            'preferred': g,
            'notes': f'VRI differs: "{v}" vs {majority} "{g}"'
        }

    if g_norm == v_norm and g_norm != s_norm:
        bjt_confirms = b_norm is not None and b_norm == g_norm
        thai_confirms = t_norm is not None and t_norm == g_norm
        confirm_count = 2 + int(bjt_confirms) + int(thai_confirms)
        conf = min(0.9, 0.5 + confirm_count * 0.1)
        majority_parts = ['PTS', 'VRI']
        if bjt_confirms:
            majority_parts.append('BJT')
        if thai_confirms:
            majority_parts.append('Thai')
        majority = '/'.join(majority_parts)
        return {
            'type': 'sc_variant',
            'confidence': conf,
            'preferred': g,
            'notes': f'SC differs: "{s}" vs {majority} "{g}"'
        }

    return {
        'type': 'unknown',
        'confidence': 0.2,
        'preferred': g,
        'notes': 'Unable to classify'
    }


def get_an_sutta_ids() -> list:
    """Get all AN sutta IDs from the GRETIL parsed data.

    Uses GRETIL as the primary source since VRI only covers nipātas 1-4.
    """
    gretil_dir = DATA_DIR / "gretil-parsed/an"
    summary_file = gretil_dir / "_summary.json"

    if not summary_file.exists():
        return []

    summary = json.loads(summary_file.read_text())
    nipata_counts = summary.get('nipata_counts', {})

    sutta_ids = []
    for nipata, count in sorted(nipata_counts.items(), key=lambda x: int(x[0])):
        for sutta in range(1, count + 1):
            sutta_ids.append(f"an{nipata}.{sutta}")

    return sutta_ids


def load_sutta_data_an(sutta_id: str) -> dict:
    """Load AN sutta data from all available sources.

    Args:
        sutta_id: Full sutta ID like "an1.1", "an4.23"

    Note: VRI only has nipātas 1-4. For nipātas 5-11, only GRETIL and SC
    are available. BJT has per-sutta files but may have more entries than GRETIL
    due to expanded peyyāla.
    """
    data = {}

    # Parse sutta ID
    match = re.match(r'an(\d+)\.(\d+)', sutta_id)
    if not match:
        return data

    nipata = int(match.group(1))
    sutta_num = int(match.group(2))

    gretil_dir = DATA_DIR / "gretil-parsed/an"
    vri_dir = DATA_DIR / "vri-parsed/an"
    sc_dir = DATA_DIR / "canonical/an"
    bjt_dir = DATA_DIR / "bjt-parsed/an"
    thai_dir = DATA_DIR / "thai-parsed/an"

    # GRETIL - file named like an1_1.json
    gretil_file = gretil_dir / f"an{nipata}_{sutta_num}.json"
    if gretil_file.exists():
        gretil = json.loads(gretil_file.read_text())
        raw_text = gretil.get('text', '')
        data['gretil'] = {
            'text': clean_gretil_text(raw_text),
            'raw_text': raw_text,
        }

    # VRI - file named like an1_1.json (only nipātas 1-4)
    if nipata <= 4:
        vri_file = vri_dir / f"an{nipata}_{sutta_num}.json"
        if vri_file.exists():
            vri = json.loads(vri_file.read_text())
            raw_text = vri.get('text', '')
            data['vri'] = {
                'text': clean_vri_text(raw_text),
                'raw_text': raw_text,
            }

    # BJT - use alignment mapping (BJT has more files due to peyyāla expansion)
    bjt_data = load_bjt_via_mapping('an', sutta_id)
    if bjt_data:
        data['bjt'] = bjt_data

    # Thai - file named like an1_1.json
    thai_file = thai_dir / f"an{nipata}_{sutta_num}.json"
    if thai_file.exists():
        thai = json.loads(thai_file.read_text())
        raw_text = thai.get('text', '')
        data['thai'] = {
            'text': clean_thai_text(raw_text),
            'raw_text': raw_text,
        }

    # SC - file named like an{nipata}.json, suttas nested within
    # SC AN uses range IDs like "an1.1-10" while GRETIL uses individual IDs
    sc_file = sc_dir / f"an{nipata}.json"
    if sc_file.exists():
        sc_key = str(sc_file)
        if sc_key not in _sc_file_cache:
            _sc_file_cache[sc_key] = json.loads(sc_file.read_text())
        sc_data = _sc_file_cache[sc_key]
        # Find the sutta - could be exact match or within a range
        for sutta in sc_data.get('suttas', []):
            sc_id = sutta.get('id', '')
            # Check for exact match first
            if sc_id == sutta_id:
                segments = sutta.get('segments', [])
                data['sc'] = {
                    'segments': segments,
                    'text': clean_sc_segments(segments)
                }
                break
            # Check if sutta_id falls within a range (e.g., "an1.1-10")
            range_match = re.match(rf'an{nipata}\.(\d+)-(\d+)', sc_id)
            if range_match:
                range_start = int(range_match.group(1))
                range_end = int(range_match.group(2))
                if range_start <= sutta_num <= range_end:
                    # This sutta is part of a range - extract relevant segments
                    segments = sutta.get('segments', [])
                    # Filter segments for this specific sutta
                    sutta_segments = []
                    for seg in segments:
                        seg_id = seg.get('id', '')
                        # Check if segment belongs to this sutta
                        # Segment IDs look like "an1.1:1.1" or "an1.5:0.1"
                        seg_match = re.match(rf'an{nipata}\.(\d+):', seg_id)
                        if seg_match:
                            seg_sutta = int(seg_match.group(1))
                            if seg_sutta == sutta_num:
                                sutta_segments.append(seg)
                    if sutta_segments:
                        data['sc'] = {
                            'segments': sutta_segments,
                            'text': clean_sc_segments(sutta_segments)
                        }
                    break

    return data


def align_sutta_an(sutta_id: str) -> dict:
    """Align a single AN sutta across available editions.

    Args:
        sutta_id: Full sutta ID like "an1.1"

    For nipātas 1-4: four-way alignment (GRETIL, SC, VRI, BJT)
    For nipātas 5-11: two-way alignment (GRETIL, SC only) + optional BJT
    """
    data = load_sutta_data_an(sutta_id)

    # Parse nipāta to check VRI availability
    match = re.match(r'an(\d+)\.', sutta_id)
    nipata = int(match.group(1)) if match else 0

    # Determine required sources
    if nipata <= 4:
        # Full four-way collation
        missing = [k for k in ['gretil', 'sc', 'vri'] if k not in data]
    else:
        # Two-way only (no VRI for nipātas 5-11)
        missing = [k for k in ['gretil', 'sc'] if k not in data]

    if missing:
        return {'error': f'Missing sources: {missing}'}

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    bjt_words = tokenize(data['bjt']['text']) if 'bjt' in data else None
    thai_words = tokenize(data['thai']['text']) if 'thai' in data else None

    if nipata <= 4 and 'vri' in data:
        vri_words = tokenize(data['vri']['text'])
        alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                    bjt_words=bjt_words, thai_words=thai_words)
    else:
        # Two-way alignment only
        alignment = align_word_sequences(gretil_words, sc_words)
        # Convert to multi-way format for consistent processing
        alignment = [
            {
                'gretil': a.get('word1'),
                'gretil_idx': a.get('idx1'),
                'sc': a.get('word2'),
                'sc_idx': a.get('idx2'),
                'vri': None,
                'vri_idx': None,
                'sc_match': a.get('type'),
                'vri_match': None,
                'bjt': None,
                'bjt_idx': None,
                'bjt_match': None,
                'thai': None,
                'thai_idx': None,
                'thai_match': None
            }
            for a in alignment
        ]
        # If BJT available but no VRI, add BJT via pairwise alignment
        if bjt_words:
            gretil_bjt = align_word_sequences(gretil_words, bjt_words)
            bjt_map = {a['idx1']: a for a in gretil_bjt if a.get('idx1') is not None}
            for pos in alignment:
                gi = pos.get('gretil_idx')
                if gi is not None and gi in bjt_map:
                    bm = bjt_map[gi]
                    pos['bjt'] = bm.get('word2')
                    pos['bjt_idx'] = bm.get('idx2')
                    pos['bjt_match'] = bm.get('type')
        # If Thai available but no VRI, add Thai via pairwise alignment
        if thai_words:
            gretil_thai = align_word_sequences(gretil_words, thai_words)
            thai_map = {a['idx1']: a for a in gretil_thai if a.get('idx1') is not None}
            for pos in alignment:
                gi = pos.get('gretil_idx')
                if gi is not None and gi in thai_map:
                    tm = thai_map[gi]
                    pos['thai'] = tm.get('word2')
                    pos['thai_idx'] = tm.get('idx2')
                    pos['thai_match'] = tm.get('type')

    return {
        'sutta': sutta_id,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(tokenize(data['vri']['text'])) if 'vri' in data else 0,
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0
        },
        'alignment': alignment,
        'has_vri': 'vri' in data,
        'has_bjt': 'bjt' in data,
        'has_thai': 'thai' in data
    }


def collate_sutta_an(sutta_id: str, max_variants: int = 1000) -> dict:
    """Collate a single AN sutta and classify all variants."""
    alignment_data = align_sutta_an(sutta_id)
    if 'error' in alignment_data:
        return {'error': alignment_data['error']}

    alignment = alignment_data.get('alignment', [])
    has_vri = alignment_data.get('has_vri', False)
    has_bjt = alignment_data.get('has_bjt', False)
    has_thai = alignment_data.get('has_thai', False)

    collation = {
        'sutta': sutta_id,
        'nikaya': 'AN',
        'word_counts': alignment_data.get('word_counts'),
        'has_vri': has_vri,
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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


def main_an(output_dir: Path):
    """Main function for collating AN (Aṅguttara Nikāya)."""
    sutta_ids = get_an_sutta_ids()
    total_suttas = len(sutta_ids)

    print("=" * 70)
    print(f"Collating Variants: AN ({total_suttas} suttas)")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print("Note: VRI available for nipātas 1-4 only; nipātas 5-11 use GRETIL+SC")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    processed = 0
    with_vri = 0
    without_vri = 0
    with_bjt = 0
    without_bjt = 0
    with_thai = 0
    without_thai = 0

    for sutta_id in sutta_ids:
        processed += 1
        if processed % 50 == 0 or processed <= 10:
            print(f"Collating {sutta_id} ({processed}/{total_suttas})...", end=" ")

        collation = collate_sutta_an(sutta_id)

        if 'error' in collation:
            if processed % 50 == 0 or processed <= 10:
                print(f"SKIPPED: {collation['error']}")
            skipped.append(sutta_id)
            continue

        if collation.get('has_vri'):
            with_vri += 1
        else:
            without_vri += 1
        if collation.get('has_bjt'):
            with_bjt += 1
        else:
            without_bjt += 1
        if collation.get('has_thai'):
            with_thai += 1
        else:
            without_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        if processed % 50 == 0 or processed <= 10:
            markers = ""
            if collation.get('has_vri'):
                markers += " [+VRI]"
            if collation.get('has_bjt'):
                markers += " [+BJT]"
            if collation.get('has_thai'):
                markers += " [+Thai]"
            print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        # Save collation - convert an1.1 to an1_1 for filename
        safe_id = sutta_id.replace('.', '_')
        output_file = output_dir / f"{safe_id}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_id,
            'has_vri': collation.get('has_vri', False),
            'has_bjt': collation.get('has_bjt', False),
            'has_thai': collation.get('has_thai', False),
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
    print(f"    With VRI (nipātas 1-4): {with_vri}")
    print(f"    Without VRI (nipātas 5-11): {without_vri}")
    print(f"    With BJT: {with_bjt}")
    print(f"    Without BJT: {without_bjt}")
    print(f"    With Thai: {with_thai}")
    print(f"    Without Thai: {without_thai}")
    if skipped:
        print(f"  Skipped (missing data): {len(skipped)} suttas")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'nikaya': 'AN',
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST, nipātas 1-4 only)',
                              'BJT (Buddha Jayanti)', 'Thai (Syām Raṭṭha)']
            },
            'dpd_words': len(dpd),
            'suttas_processed': len(results),
            'suttas_with_vri': with_vri,
            'suttas_without_vri': without_vri,
            'suttas_with_bjt': with_bjt,
            'suttas_without_bjt': without_bjt,
            'suttas_with_thai': with_thai,
            'suttas_without_thai': without_thai,
            'suttas_skipped': len(skipped),
            'skipped_ids': skipped[:100],
            'suttas': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_dir}")


def load_text_data_kn(sc_abbrev: str, gretil_name: str, vri_code: str,
                      bjt_name: str = None, thai_name: str = None) -> dict:
    """Load KN text data from all available sources.

    Args:
        sc_abbrev: SC abbreviation like "dhp", "snp"
        gretil_name: GRETIL name like "dhammapada", "suttanipata"
        vri_code: VRI CST code like "s0502m.mul" or None if not available
        bjt_name: BJT file name like "dhammapada" or None if not available
        thai_name: Thai file name like "dhp" or None if not available
    """
    data = {}

    gretil_dir = DATA_DIR / "gretil-parsed/kn"
    vri_dir = DATA_DIR / "vri-parsed/kn"
    sc_dir = DATA_DIR / "canonical/kn"
    bjt_dir = DATA_DIR / "bjt-parsed/kn"
    thai_dir = DATA_DIR / "thai-parsed/kn"

    # GRETIL
    if gretil_name:
        # Handle multi-file texts (jataka1-6, patisambhidamagga1-2)
        gretil_files = list(gretil_dir.glob(f"{gretil_name}*.json"))
        if gretil_files:
            combined_text = []
            for gf in sorted(gretil_files):
                if gf.name == '_summary.json':
                    continue
                gretil = json.loads(gf.read_text())
                raw_text = gretil.get('text', '')
                combined_text.append(clean_gretil_text(raw_text))
            if combined_text:
                full_text = ' '.join(combined_text)

                # Special handling for Apadāna: split into Thera and Therī sections
                # GRETIL apadana.json contains both sections; split at "THERĪAPADĀNA ATHA"
                # (hyphen removed by clean_gretil_text)
                if gretil_name == 'apadana':
                    theri_marker = re.search(r'THERĪAPADĀNA\s+ATHA', full_text, re.IGNORECASE)
                    if theri_marker:
                        if sc_abbrev == 'tha-ap':
                            # Thera-Apadāna: use text before Therī section
                            full_text = full_text[:theri_marker.start()].strip()
                        elif sc_abbrev == 'thi-ap':
                            # Therī-Apadāna: use text from Therī section onward
                            full_text = full_text[theri_marker.start():].strip()
                    else:
                        warnings.warn(
                            f"Apadāna split marker 'THERĪAPADĀNA ATHA' not found in GRETIL text. "
                            f"Using combined text for {sc_abbrev}. Collation may be degraded.",
                            UserWarning
                        )

                data['gretil'] = {
                    'text': full_text,
                    'files': [f.name for f in gretil_files]
                }

    # VRI
    if vri_code:
        vri_file = vri_dir / f"{vri_code}.json"
        if vri_file.exists():
            vri = json.loads(vri_file.read_text())
            raw_text = vri.get('text', '')
            data['vri'] = {
                'text': clean_vri_text(raw_text),
                'raw_text': raw_text,
            }

    # SC
    sc_file = sc_dir / f"{sc_abbrev}.json"
    if sc_file.exists():
        sc = json.loads(sc_file.read_text())
        # SC KN files can have different structures
        segments = []
        if 'segments' in sc:
            segments = sc.get('segments', [])
        elif 'items' in sc:
            # Dhammapada, etc. use 'items' for vaggas
            for item in sc.get('items', []):
                segments.extend(item.get('segments', []))
        elif 'texts' in sc:
            # Some KN files nest texts
            for text in sc.get('texts', []):
                segments.extend(text.get('segments', []))
        elif 'suttas' in sc:
            # Like AN/SN nested structure
            for sutta in sc.get('suttas', []):
                segments.extend(sutta.get('segments', []))
        elif 'vaggas' in sc:
            # Vagga structure
            for vagga in sc.get('vaggas', []):
                segments.extend(vagga.get('segments', []))
        data['sc'] = {
            'segments': segments,
            'text': clean_sc_segments(segments)
        }

    # BJT
    if bjt_name:
        # Handle multi-file texts (jataka1-6, patisambhidamagga1-2)
        bjt_files = list(bjt_dir.glob(f"{bjt_name}*.json"))
        bjt_files = [f for f in bjt_files if f.name != '_summary.json']
        if bjt_files:
            combined_text = []
            for bf in sorted(bjt_files):
                bjt = json.loads(bf.read_text())
                raw_text = bjt.get('text', '')
                combined_text.append(clean_bjt_text(raw_text))
            if combined_text:
                data['bjt'] = {
                    'text': ' '.join(combined_text),
                    'files': [f.name for f in sorted(bjt_files)]
                }

    # Thai
    if thai_name:
        thai_file = thai_dir / f"{thai_name}.json"
        if thai_file.exists():
            thai = json.loads(thai_file.read_text())
            raw_text = thai.get('text', '')
            data['thai'] = {
                'text': clean_thai_text(raw_text),
                'raw_text': raw_text,
            }

    return data


def collate_text_kn(sc_abbrev: str, gretil_name: str, vri_code: str,
                    bjt_name: str = None, thai_name: str = None,
                    max_variants: int = 1000) -> dict:
    """Collate a single KN text across editions."""
    data = load_text_data_kn(sc_abbrev, gretil_name, vri_code, bjt_name=bjt_name,
                             thai_name=thai_name)

    # Determine required sources
    has_vri = vri_code is not None and 'vri' in data
    has_gretil = gretil_name is not None and 'gretil' in data
    has_bjt = bjt_name is not None and 'bjt' in data
    has_thai = thai_name is not None and 'thai' in data

    if not has_gretil:
        return {'error': 'Missing GRETIL source'}
    if 'sc' not in data:
        return {'error': 'Missing SC source'}

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    bjt_words = tokenize(data['bjt']['text']) if has_bjt else None
    thai_words = tokenize(data['thai']['text']) if has_thai else None

    if has_vri:
        vri_words = tokenize(data['vri']['text'])
        alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                    bjt_words=bjt_words, thai_words=thai_words)
    else:
        # Two-way alignment only
        alignment = align_word_sequences(gretil_words, sc_words)
        alignment = [
            {
                'gretil': a.get('word1'),
                'gretil_idx': a.get('idx1'),
                'sc': a.get('word2'),
                'sc_idx': a.get('idx2'),
                'vri': None,
                'vri_idx': None,
                'sc_match': a.get('type'),
                'vri_match': None,
                'bjt': None,
                'bjt_idx': None,
                'bjt_match': None,
                'thai': None,
                'thai_idx': None,
                'thai_match': None
            }
            for a in alignment
        ]
        # If BJT available but no VRI, add BJT via pairwise alignment
        if bjt_words:
            gretil_bjt = align_word_sequences(gretil_words, bjt_words)
            bjt_map = {a['idx1']: a for a in gretil_bjt if a.get('idx1') is not None}
            for pos in alignment:
                gi = pos.get('gretil_idx')
                if gi is not None and gi in bjt_map:
                    bm = bjt_map[gi]
                    pos['bjt'] = bm.get('word2')
                    pos['bjt_idx'] = bm.get('idx2')
                    pos['bjt_match'] = bm.get('type')
        # If Thai available but no VRI, add Thai via pairwise alignment
        if thai_words:
            gretil_thai = align_word_sequences(gretil_words, thai_words)
            thai_map = {a['idx1']: a for a in gretil_thai if a.get('idx1') is not None}
            for pos in alignment:
                gi = pos.get('gretil_idx')
                if gi is not None and gi in thai_map:
                    tm = thai_map[gi]
                    pos['thai'] = tm.get('word2')
                    pos['thai_idx'] = tm.get('idx2')
                    pos['thai_match'] = tm.get('type')

    collation = {
        'text': sc_abbrev,
        'nikaya': 'KN',
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(tokenize(data['vri']['text'])) if has_vri else 0,
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0
        },
        'has_vri': has_vri,
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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


def main_kn(output_dir: Path):
    """Main function for collating KN (Khuddaka Nikāya)."""
    # Filter to texts with at least GRETIL source
    available_texts = [(sc, gr, vri, bjt, thai) for sc, gr, vri, bjt, thai in KN_TEXTS if gr is not None]
    total_texts = len(available_texts)

    print("=" * 70)
    print(f"Collating Variants: KN ({total_texts} texts)")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    with_vri = 0
    without_vri = 0
    with_bjt = 0
    without_bjt = 0
    with_thai = 0
    without_thai = 0

    for sc_abbrev, gretil_name, vri_code, bjt_name, thai_name in available_texts:
        print(f"Collating {sc_abbrev.upper()} ({gretil_name})...", end=" ")

        collation = collate_text_kn(sc_abbrev, gretil_name, vri_code,
                                    bjt_name=bjt_name, thai_name=thai_name)

        if 'error' in collation:
            print(f"SKIPPED: {collation['error']}")
            skipped.append(sc_abbrev)
            continue

        if collation.get('has_vri'):
            with_vri += 1
        else:
            without_vri += 1
        if collation.get('has_bjt'):
            with_bjt += 1
        else:
            without_bjt += 1
        if collation.get('has_thai'):
            with_thai += 1
        else:
            without_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        markers = ""
        if collation.get('has_vri'):
            markers += " [+VRI]"
        if collation.get('has_bjt'):
            markers += " [+BJT]"
        if collation.get('has_thai'):
            markers += " [+Thai]"
        print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        # Save collation
        output_file = output_dir / f"{sc_abbrev}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'text': sc_abbrev,
            'gretil_name': gretil_name,
            'has_vri': collation.get('has_vri', False),
            'has_bjt': collation.get('has_bjt', False),
            'has_thai': collation.get('has_thai', False),
            'stats': stats
        })

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Texts processed: {len(results)}/{total_texts}")
    print(f"    With VRI: {with_vri}")
    print(f"    Without VRI: {without_vri}")
    print(f"    With BJT: {with_bjt}")
    print(f"    Without BJT: {without_bjt}")
    print(f"    With Thai: {with_thai}")
    print(f"    Without Thai: {without_thai}")
    if skipped:
        print(f"  Skipped (missing data): {skipped}")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'nikaya': 'KN',
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)',
                              'BJT (Buddha Jayanti)', 'Thai (Syām Raṭṭha)']
            },
            'dpd_words': len(dpd),
            'texts_processed': len(results),
            'texts_with_vri': with_vri,
            'texts_without_vri': without_vri,
            'texts_with_bjt': with_bjt,
            'texts_without_bjt': without_bjt,
            'texts_with_thai': with_thai,
            'texts_without_thai': without_thai,
            'texts_skipped': skipped,
            'texts': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_dir}")


def load_text_data_vinaya(name: str, gretil_name: str, vri_codes: list,
                         sc_name: str = None, bjt_name: str = None,
                         thai_name: str = None) -> dict:
    """Load Vinaya text data from all available sources."""
    data = {}

    gretil_dir = DATA_DIR / "gretil-parsed/vinaya"
    vri_dir = DATA_DIR / "vri-parsed/vinaya"
    sc_dir = DATA_DIR / "sc-parsed/vinaya"
    bjt_dir = DATA_DIR / "bjt-parsed/vinaya"
    thai_dir = DATA_DIR / "thai-parsed/vinaya"

    # GRETIL
    if gretil_name:
        gretil_file = gretil_dir / f"{gretil_name}.json"
        if gretil_file.exists():
            gretil = json.loads(gretil_file.read_text())
            raw_text = gretil.get('text', '')
            data['gretil'] = {
                'text': clean_gretil_text(raw_text),
                'raw_text': raw_text,
            }

    # VRI (may be multiple files to concatenate)
    if vri_codes:
        vri_texts = []
        for vc in vri_codes:
            vri_file = vri_dir / f"{vc}.json"
            if vri_file.exists():
                vri = json.loads(vri_file.read_text())
                vri_texts.append(vri.get('text', ''))
        if vri_texts:
            raw_text = ' '.join(vri_texts)
            data['vri'] = {
                'text': clean_vri_text(raw_text),
                'raw_text': raw_text,
            }

    # SC
    if sc_name:
        sc_file = sc_dir / f"{sc_name}.json"
        if sc_file.exists():
            sc = json.loads(sc_file.read_text())
            raw_text = sc.get('text', '')
            data['sc'] = {
                'text': raw_text.strip(),
                'raw_text': raw_text,
            }

    # BJT (may be a single name or list of names)
    bjt_names = [bjt_name] if isinstance(bjt_name, str) else (bjt_name or [])
    if bjt_names:
        bjt_texts = []
        for bn in bjt_names:
            bjt_file = bjt_dir / f"{bn}.json"
            if bjt_file.exists():
                bjt = json.loads(bjt_file.read_text())
                bjt_texts.append(bjt.get('text', ''))
        if bjt_texts:
            raw_text = ' '.join(bjt_texts)
            data['bjt'] = {
                'text': clean_bjt_text(raw_text),
                'raw_text': raw_text,
            }

    # Thai
    if thai_name:
        thai_file = thai_dir / f"{thai_name}.json"
        if thai_file.exists():
            thai = json.loads(thai_file.read_text())
            raw_text = thai.get('text', '')
            data['thai'] = {
                'text': clean_thai_text(raw_text),
                'raw_text': raw_text,
            }

    return data


def collate_text_vinaya(name: str, gretil_name: str, vri_codes: list,
                        sc_name: str = None, bjt_name: str = None,
                        thai_name: str = None,
                        max_variants: int = 1000) -> dict:
    """Collate a Vinaya text across all available witnesses (up to 5)."""
    data = load_text_data_vinaya(name, gretil_name, vri_codes, sc_name,
                                 bjt_name, thai_name)

    if 'gretil' not in data:
        return {'error': 'Missing GRETIL source'}

    has_vri = bool(vri_codes) and 'vri' in data
    has_sc = 'sc' in data
    has_bjt = 'bjt' in data
    has_thai = 'thai' in data

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text']) if has_sc else None
    vri_words = tokenize(data['vri']['text']) if has_vri else None
    bjt_words = tokenize(data['bjt']['text']) if has_bjt else None
    thai_words = tokenize(data['thai']['text']) if has_thai else None

    # Use full multi-way alignment when SC is available
    if has_sc and has_vri:
        alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                    bjt_words=bjt_words, thai_words=thai_words)
    elif has_vri:
        # Fallback: GRETIL-VRI pairwise, add BJT/Thai if available
        raw_align = align_word_sequences(gretil_words, vri_words)
        alignment = [
            {
                'gretil': a.get('word1'),
                'gretil_idx': a.get('idx1'),
                'vri': a.get('word2'),
                'vri_idx': a.get('idx2'),
                'sc': None, 'sc_idx': None,
                'bjt': None, 'bjt_idx': None,
                'thai': None, 'thai_idx': None,
                'vri_match': a.get('type'),
                'sc_match': None, 'bjt_match': None, 'thai_match': None
            }
            for a in raw_align
        ]
        # Add BJT via pairwise alignment if available
        if bjt_words:
            bjt_align = align_word_sequences(gretil_words, bjt_words)
            bjt_map = {}
            for a in bjt_align:
                idx = a.get('idx1')
                if idx is not None:
                    bjt_map[idx] = a
            for pos in alignment:
                idx = pos.get('gretil_idx')
                if idx in bjt_map:
                    pos['bjt'] = bjt_map[idx]['word2']
                    pos['bjt_idx'] = bjt_map[idx].get('idx2')
                    pos['bjt_match'] = bjt_map[idx]['type']
        # Add Thai via pairwise alignment if available
        if thai_words:
            thai_align = align_word_sequences(gretil_words, thai_words)
            thai_map = {}
            for a in thai_align:
                idx = a.get('idx1')
                if idx is not None:
                    thai_map[idx] = a
            for pos in alignment:
                idx = pos.get('gretil_idx')
                if idx in thai_map:
                    pos['thai'] = thai_map[idx]['word2']
                    pos['thai_idx'] = thai_map[idx].get('idx2')
                    pos['thai_match'] = thai_map[idx]['type']
    else:
        return {'error': 'Missing VRI source'}

    collation = {
        'text': name,
        'pitaka': 'Vinaya',
        'word_counts': {
            'gretil': len(gretil_words),
            'vri': len(vri_words) if vri_words else 0,
            'sc': len(sc_words) if sc_words else 0,
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0,
        },
        'has_vri': has_vri,
        'has_sc': has_sc,
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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


def main_vinaya(output_dir: Path):
    """Main function for collating Vinaya Piṭaka."""
    available_texts = [(n, gr, vri, sc, bjt, thai)
                       for n, gr, vri, sc, bjt, thai in VINAYA_TEXTS
                       if gr is not None]
    total_texts = len(available_texts)

    print("=" * 70)
    print(f"Collating Variants: Vinaya ({total_texts} texts)")
    print("Witnesses: GRETIL (PTS), VRI (CST), SC (Mahāsaṅgīti), BJT, Thai")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    with_vri = 0
    without_vri = 0
    with_thai = 0
    without_thai = 0

    for name, gretil_name, vri_codes, sc_name, bjt_name, thai_name in available_texts:
        print(f"Collating {name.upper()} ({gretil_name})...", end=" ")

        collation = collate_text_vinaya(name, gretil_name, vri_codes,
                                         sc_name, bjt_name, thai_name)

        if 'error' in collation:
            print(f"SKIPPED: {collation['error']}")
            skipped.append(name)
            continue

        if collation.get('has_vri'):
            with_vri += 1
        else:
            without_vri += 1
        if collation.get('has_thai'):
            with_thai += 1
        else:
            without_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        markers = ""
        if collation.get('has_thai'):
            markers += " [+Thai]"
        print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        # Save collation
        output_file = output_dir / f"{name}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'text': name,
            'gretil_name': gretil_name,
            'has_vri': collation.get('has_vri', False),
            'has_thai': collation.get('has_thai', False),
            'stats': stats
        })

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Texts processed: {len(results)}/{total_texts}")
    print(f"    With VRI: {with_vri}")
    print(f"    With Thai: {with_thai}")
    if skipped:
        print(f"  Skipped (missing VRI): {skipped}")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    # Save summary
    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pitaka': 'Vinaya',
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['VRI (CST)', 'SC (Mahāsaṅgīti)', 'BJT',
                              'Thai (Syām Raṭṭha)'],
            },
            'dpd_words': len(dpd),
            'texts_processed': len(results),
            'texts_with_vri': with_vri,
            'texts_with_thai': with_thai,
            'texts_skipped': skipped,
            'texts': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_dir}")


def load_text_data_abhidhamma(name: str, gretil_name: str, vri_codes: list,
                              sc_name: str = None, bjt_name=None,
                              thai_name=None) -> dict:
    """Load Abhidhamma text data from all available sources."""
    data = {}

    gretil_dir = DATA_DIR / "gretil-parsed/abhidhamma"
    vri_dir = DATA_DIR / "vri-parsed/abhidhamma"
    sc_dir = DATA_DIR / "sc-parsed/abhidhamma"
    bjt_dir = DATA_DIR / "bjt-parsed/abhidhamma"
    thai_dir = DATA_DIR / "thai-parsed/abhidhamma"

    # GRETIL - handle multi-file texts (yamaka1-2, patthana1-3)
    if gretil_name:
        gretil_file = gretil_dir / f"{gretil_name}.json"
        if gretil_file.exists():
            gretil = json.loads(gretil_file.read_text())
            raw_text = gretil.get('text', '')
            data['gretil'] = {
                'text': clean_gretil_text(raw_text),
                'raw_text': raw_text,
            }
        else:
            # Try glob for multi-file texts
            gretil_files = sorted(f for f in gretil_dir.glob(f"{gretil_name}*.json")
                                  if f.name != '_summary.json')
            if gretil_files:
                combined_text = []
                for gf in gretil_files:
                    g = json.loads(gf.read_text())
                    combined_text.append(clean_gretil_text(g.get('text', '')))
                data['gretil'] = {
                    'text': ' '.join(combined_text),
                    'files': [f.name for f in gretil_files]
                }

    # VRI (may be multiple files)
    if vri_codes:
        vri_texts = []
        for vc in vri_codes:
            vri_file = vri_dir / f"{vc}.json"
            if vri_file.exists():
                vri = json.loads(vri_file.read_text())
                vri_texts.append(vri.get('text', ''))
        if vri_texts:
            raw_text = ' '.join(vri_texts)
            data['vri'] = {
                'text': clean_vri_text(raw_text),
                'raw_text': raw_text,
            }

    # SC (may be single file or multi-file via glob)
    if sc_name:
        sc_names = [sc_name] if isinstance(sc_name, str) else sc_name
        sc_file = sc_dir / f"{sc_names[0]}.json"
        if len(sc_names) == 1 and sc_file.exists():
            sc = json.loads(sc_file.read_text())
            raw_text = sc.get('text', '')
            data['sc'] = {
                'text': raw_text.strip(),
                'raw_text': raw_text,
            }
        else:
            # Try glob for multi-file texts (e.g. yamaka -> yamaka1.json, yamaka2.json)
            sc_texts = []
            if len(sc_names) > 1:
                # Explicit list of filenames
                for sn in sc_names:
                    sf = sc_dir / f"{sn}.json"
                    if sf.exists():
                        s = json.loads(sf.read_text())
                        sc_texts.append(s.get('text', '').strip())
            else:
                sc_files = sorted(
                    f for f in sc_dir.glob(f"{sc_names[0]}*.json")
                    if f.name != '_summary.json')
                for sf in sc_files:
                    s = json.loads(sf.read_text())
                    sc_texts.append(s.get('text', '').strip())
            if sc_texts:
                raw_text = ' '.join(sc_texts)
                data['sc'] = {'text': raw_text, 'raw_text': raw_text}

    # BJT (may be single name or list)
    bjt_names = [bjt_name] if isinstance(bjt_name, str) else (bjt_name or [])
    if bjt_names:
        bjt_texts = []
        for bn in bjt_names:
            bjt_file = bjt_dir / f"{bn}.json"
            if bjt_file.exists():
                bjt = json.loads(bjt_file.read_text())
                bjt_texts.append(bjt.get('text', ''))
        if bjt_texts:
            raw_text = ' '.join(bjt_texts)
            data['bjt'] = {
                'text': clean_bjt_text(raw_text),
                'raw_text': raw_text,
            }

    # Thai
    if thai_name:
        thai_file = thai_dir / f"{thai_name}.json"
        if thai_file.exists():
            thai = json.loads(thai_file.read_text())
            raw_text = thai.get('text', '')
            data['thai'] = {
                'text': clean_thai_text(raw_text),
                'raw_text': raw_text,
            }

    return data


def collate_text_abhidhamma(name: str, gretil_name: str, vri_codes: list,
                            sc_name: str = None, bjt_name=None,
                            thai_name=None,
                            max_variants: int = 1000) -> dict:
    """Collate an Abhidhamma text across all available witnesses (up to 5)."""
    data = load_text_data_abhidhamma(name, gretil_name, vri_codes, sc_name,
                                      bjt_name, thai_name)

    if 'gretil' not in data:
        return {'error': 'Missing GRETIL source'}

    has_vri = bool(vri_codes) and 'vri' in data
    has_sc = 'sc' in data
    has_bjt = 'bjt' in data
    has_thai = 'thai' in data

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text']) if has_sc else None
    vri_words = tokenize(data['vri']['text']) if has_vri else None
    bjt_words = tokenize(data['bjt']['text']) if has_bjt else None
    thai_words = tokenize(data['thai']['text']) if has_thai else None

    # Use full multi-way alignment when SC is available
    if has_sc and has_vri:
        alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                    bjt_words=bjt_words, thai_words=thai_words)
    elif has_vri:
        # Fallback: GRETIL-VRI pairwise, add BJT/Thai if available
        raw_align = align_word_sequences(gretil_words, vri_words)
        alignment = [
            {
                'gretil': a.get('word1'),
                'gretil_idx': a.get('idx1'),
                'vri': a.get('word2'),
                'vri_idx': a.get('idx2'),
                'sc': None, 'sc_idx': None,
                'bjt': None, 'bjt_idx': None,
                'thai': None, 'thai_idx': None,
                'vri_match': a.get('type'),
                'sc_match': None, 'bjt_match': None, 'thai_match': None
            }
            for a in raw_align
        ]
        if bjt_words:
            bjt_align = align_word_sequences(gretil_words, bjt_words)
            bjt_map = {}
            for a in bjt_align:
                idx = a.get('idx1')
                if idx is not None:
                    bjt_map[idx] = a
            for pos in alignment:
                idx = pos.get('gretil_idx')
                if idx in bjt_map:
                    pos['bjt'] = bjt_map[idx]['word2']
                    pos['bjt_idx'] = bjt_map[idx].get('idx2')
                    pos['bjt_match'] = bjt_map[idx]['type']
        if thai_words:
            thai_align = align_word_sequences(gretil_words, thai_words)
            thai_map = {}
            for a in thai_align:
                idx = a.get('idx1')
                if idx is not None:
                    thai_map[idx] = a
            for pos in alignment:
                idx = pos.get('gretil_idx')
                if idx in thai_map:
                    pos['thai'] = thai_map[idx]['word2']
                    pos['thai_idx'] = thai_map[idx].get('idx2')
                    pos['thai_match'] = thai_map[idx]['type']
    else:
        return {'error': 'Missing VRI source'}

    collation = {
        'text': name,
        'pitaka': 'Abhidhamma',
        'word_counts': {
            'gretil': len(gretil_words),
            'vri': len(vri_words) if vri_words else 0,
            'sc': len(sc_words) if sc_words else 0,
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0,
        },
        'has_vri': has_vri,
        'has_sc': has_sc,
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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


def main_abhidhamma(output_dir: Path):
    """Main function for collating Abhidhamma Piṭaka."""
    available_texts = [(n, gr, vri, sc, bjt, thai)
                       for n, gr, vri, sc, bjt, thai in ABHIDHAMMA_TEXTS
                       if gr is not None]
    total_texts = len(available_texts)

    print("=" * 70)
    print(f"Collating Variants: Abhidhamma ({total_texts} texts)")
    print("Witnesses: GRETIL (PTS), VRI (CST), SC (Mahāsaṅgīti), BJT, Thai")
    print("=" * 70)
    print()

    dpd = load_dpd_words()
    print(f"DPD words loaded: {len(dpd):,}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    skipped = []
    with_vri = 0
    with_thai = 0

    for name, gretil_name, vri_codes, sc_name, bjt_name, thai_name in available_texts:
        print(f"Collating {name.upper()} ({gretil_name})...", end=" ")

        collation = collate_text_abhidhamma(name, gretil_name, vri_codes,
                                             sc_name, bjt_name, thai_name)

        if 'error' in collation:
            print(f"SKIPPED: {collation['error']}")
            skipped.append(name)
            continue

        if collation.get('has_vri'):
            with_vri += 1
        if collation.get('has_thai'):
            with_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        markers = ""
        if collation.get('has_thai'):
            markers += " [+Thai]"
        print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        output_file = output_dir / f"{name}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'text': name,
            'gretil_name': gretil_name,
            'has_vri': collation.get('has_vri', False),
            'has_thai': collation.get('has_thai', False),
            'stats': stats
        })

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    total_errors = sum(r['stats']['errors'] for r in results)
    total_variants = sum(r['stats']['variants'] for r in results)
    total_uncertain = sum(r['stats']['uncertain'] for r in results)

    print(f"  Texts processed: {len(results)}/{total_texts}")
    print(f"    With VRI: {with_vri}")
    print(f"    With Thai: {with_thai}")
    if skipped:
        print(f"  Skipped (missing VRI): {skipped}")
    print(f"  Total errors found: {total_errors}")
    print(f"  Total variants recorded: {total_variants}")
    print(f"  Total uncertain: {total_uncertain}")

    summary_file = output_dir / "_collation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pitaka': 'Abhidhamma',
            'editions': {
                'primary': 'PTS (GRETIL)',
                'witnesses': ['VRI (CST)', 'SC (Mahāsaṅgīti)', 'BJT',
                              'Thai (Syām Raṭṭha)'],
            },
            'dpd_words': len(dpd),
            'texts_processed': len(results),
            'texts_with_vri': with_vri,
            'texts_with_thai': with_thai,
            'texts_skipped': skipped,
            'texts': results,
            'totals': {
                'errors': total_errors,
                'variants': total_variants,
                'uncertain': total_uncertain
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_dir}")


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
    """Load SN sutta data from all available sources.

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
    bjt_dir = DATA_DIR / "bjt-parsed/sn"
    thai_dir = DATA_DIR / "thai-parsed/sn"

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

    # BJT - use alignment mapping (BJT file numbering differs from GRETIL)
    bjt_data = load_bjt_via_mapping('sn', sutta_id)
    if bjt_data:
        data['bjt'] = bjt_data

    # Thai - file named like sn1_1.json
    thai_file = thai_dir / f"sn{samyutta}_{sutta_num}.json"
    if thai_file.exists():
        thai = json.loads(thai_file.read_text())
        raw_text = thai.get('text', '')
        data['thai'] = {
            'text': clean_thai_text(raw_text),
            'raw_text': raw_text,
        }

    # SC - file named like sn{samyutta}.json, suttas nested within
    sc_file = sc_dir / f"sn{samyutta}.json"
    if sc_file.exists():
        sc_key = str(sc_file)
        if sc_key not in _sc_file_cache:
            _sc_file_cache[sc_key] = json.loads(sc_file.read_text())
        sc_data = _sc_file_cache[sc_key]
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
    """Load sutta data from all available sources."""
    data = {}

    gretil_dir = DATA_DIR / f"gretil-parsed/{nikaya}"
    vri_dir = DATA_DIR / f"vri-parsed/{nikaya}"
    sc_dir = DATA_DIR / f"canonical/{nikaya}"
    bjt_dir = DATA_DIR / f"bjt-parsed/{nikaya}"
    thai_dir = DATA_DIR / f"thai-parsed/{nikaya}"

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

    # BJT
    bjt_file = bjt_dir / f"{nikaya}{sutta_num}.json"
    if bjt_file.exists():
        bjt = json.loads(bjt_file.read_text())
        raw_text = bjt.get('text', '')
        data['bjt'] = {
            'text': clean_bjt_text(raw_text),
            'raw_text': raw_text,
        }

    # Thai
    thai_file = thai_dir / f"{nikaya}{sutta_num}.json"
    if thai_file.exists():
        thai = json.loads(thai_file.read_text())
        raw_text = thai.get('text', '')
        data['thai'] = {
            'text': clean_thai_text(raw_text),
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
    """Align a single sutta across all available editions."""
    data = load_sutta_data(nikaya, sutta_num)

    missing = [k for k in ['gretil', 'sc', 'vri'] if k not in data]
    if missing:
        return {'error': f'Missing sources: {missing}'}

    gretil_words = tokenize(data['gretil']['text'])
    sc_words = tokenize(data['sc']['text'])
    vri_words = tokenize(data['vri']['text'])
    bjt_words = tokenize(data['bjt']['text']) if 'bjt' in data else None
    thai_words = tokenize(data['thai']['text']) if 'thai' in data else None

    alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                bjt_words=bjt_words, thai_words=thai_words)

    return {
        'sutta': sutta_num,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(vri_words),
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0
        },
        'alignment': alignment,
        'has_bjt': 'bjt' in data,
        'has_thai': 'thai' in data
    }


def align_sutta_sn(sutta_id: str) -> dict:
    """Align a single SN sutta across all available editions.

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
    bjt_words = tokenize(data['bjt']['text']) if 'bjt' in data else None
    thai_words = tokenize(data['thai']['text']) if 'thai' in data else None

    alignment = align_witnesses(gretil_words, sc_words, vri_words,
                                bjt_words=bjt_words, thai_words=thai_words)

    return {
        'sutta': sutta_id,
        'word_counts': {
            'gretil': len(gretil_words),
            'sc': len(sc_words),
            'vri': len(vri_words),
            'bjt': len(bjt_words) if bjt_words else 0,
            'thai': len(thai_words) if thai_words else 0
        },
        'alignment': alignment,
        'has_bjt': 'bjt' in data,
        'has_thai': 'thai' in data
    }


def collate_sutta(nikaya: str, sutta_num: int, max_variants: int = 1000) -> dict:
    """Collate a single sutta and classify all variants."""
    alignment_data = align_sutta(nikaya, sutta_num)
    if 'error' in alignment_data:
        return {'error': alignment_data['error']}

    alignment = alignment_data.get('alignment', [])
    has_bjt = alignment_data.get('has_bjt', False)
    has_thai = alignment_data.get('has_thai', False)

    collation = {
        'sutta': sutta_num,
        'nikaya': nikaya.upper(),
        'word_counts': alignment_data.get('word_counts'),
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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
    has_bjt = alignment_data.get('has_bjt', False)
    has_thai = alignment_data.get('has_thai', False)

    collation = {
        'sutta': sutta_id,
        'nikaya': 'SN',
        'word_counts': alignment_data.get('word_counts'),
        'has_bjt': has_bjt,
        'has_thai': has_thai,
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
    """Process alignment data and classify variants.

    Handles five-way (GRETIL/SC/VRI/BJT/Thai), three-way (GRETIL/SC/VRI), and
    two-way (GRETIL/SC) collation. BJT and Thai are used in classification
    decisions to refine confidence scores and identify majority readings.
    """
    has_vri = collation.get('has_vri', True)
    has_bjt = collation.get('has_bjt', False)
    has_thai = collation.get('has_thai', False)

    for i, pos in enumerate(alignment):
        g = pos.get('gretil')
        s = pos.get('sc')
        v = pos.get('vri')
        b = pos.get('bjt')
        t = pos.get('thai')

        # Check for match - all available witnesses must agree
        all_match = pos.get('sc_match') == 'match'
        if has_vri:
            all_match = all_match and pos.get('vri_match') == 'match'
        if has_bjt:
            all_match = all_match and pos.get('bjt_match') == 'match'
        if has_thai:
            all_match = all_match and pos.get('thai_match') == 'match'
        if all_match:
            collation['stats']['match'] += 1
            continue

        if has_vri:
            # Three/four/five-way classification
            classification = classify_variant(g, s, v, b, t)
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
                        'bjt': b,
                        'thai': t,
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
                        'bjt': b,
                        'thai': t,
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
                        'bjt': b,
                        'thai': t,
                        **classification
                    })
            elif var_type in ('alignment_artifact', 'fragment'):
                collation['stats']['other'] += 1
            else:
                collation['stats']['other'] += 1
        else:
            # Two-way classification (GRETIL vs SC, no VRI)
            g_norm = normalize_for_comparison(g) if g else None
            s_norm = normalize_for_comparison(s) if s else None
            b_norm = normalize_for_comparison(b) if b else None
            t_norm = normalize_for_comparison(t) if t else None

            if g_norm == s_norm:
                collation['stats']['orthographic'] += 1
            elif g and s:
                g_valid = is_valid_word(g)
                s_valid = is_valid_word(s)
                bjt_with_sc = b_norm is not None and b_norm == s_norm
                bjt_with_pts = b_norm is not None and b_norm == g_norm
                thai_with_sc = t_norm is not None and t_norm == s_norm
                thai_with_pts = t_norm is not None and t_norm == g_norm
                if s_valid and not g_valid:
                    # PTS (GRETIL) error, SC is correct
                    sc_supporters = ['SC']
                    if bjt_with_sc:
                        sc_supporters.append('BJT')
                    if thai_with_sc:
                        sc_supporters.append('Thai')
                    conf = min(0.98, 0.85 + 0.05 * len(sc_supporters))
                    others = '/'.join(sc_supporters)
                    extra_notes = []
                    if bjt_with_pts:
                        extra_notes.append('BJT agrees with PTS')
                    if thai_with_pts:
                        extra_notes.append('Thai agrees with PTS')
                    note_suffix = ', ' + ', '.join(extra_notes) if extra_notes else ''
                    collation['stats']['errors'] += 1
                    if len(collation['errors']) < max_variants:
                        collation['errors'].append({
                            'position': i,
                            'gretil': g,
                            'sc': s,
                            'vri': None,
                            'bjt': b,
                            'thai': t,
                            'type': 'error',
                            'confidence': conf,
                            'preferred': s,
                            'notes': f'PTS "{g}" not in DPD, {others} "{s}" is valid{note_suffix}'
                        })
                elif g_valid and not s_valid:
                    # SC error, PTS (GRETIL) is correct
                    pts_supporters = ['PTS']
                    if bjt_with_pts:
                        pts_supporters.append('BJT')
                    if thai_with_pts:
                        pts_supporters.append('Thai')
                    conf = min(0.98, 0.85 + 0.05 * len(pts_supporters))
                    others = '/'.join(pts_supporters)
                    extra_notes = []
                    if bjt_with_sc:
                        extra_notes.append('BJT agrees with SC')
                    if thai_with_sc:
                        extra_notes.append('Thai agrees with SC')
                    note_suffix = ', ' + ', '.join(extra_notes) if extra_notes else ''
                    collation['stats']['errors'] += 1
                    if len(collation['errors']) < max_variants:
                        collation['errors'].append({
                            'position': i,
                            'gretil': g,
                            'sc': s,
                            'vri': None,
                            'bjt': b,
                            'thai': t,
                            'type': 'sc_error',
                            'confidence': conf,
                            'preferred': g,
                            'notes': f'SC "{s}" not in DPD, {others} "{g}" is valid{note_suffix}'
                        })
                elif g_valid and s_valid:
                    # Both valid - textual variant
                    extra = []
                    if bjt_with_sc:
                        extra.append('BJT agrees with SC')
                    elif bjt_with_pts:
                        extra.append('BJT agrees with PTS')
                    if thai_with_sc:
                        extra.append('Thai agrees with SC')
                    elif thai_with_pts:
                        extra.append('Thai agrees with PTS')
                    note_suffix = ' (' + ', '.join(extra) + ')' if extra else ''
                    collation['stats']['variants'] += 1
                    if len(collation['variants']) < max_variants:
                        collation['variants'].append({
                            'position': i,
                            'gretil': g,
                            'sc': s,
                            'vri': None,
                            'bjt': b,
                            'thai': t,
                            'type': 'variant',
                            'notes': f'Textual variant: PTS "{g}" vs SC "{s}"{note_suffix}'
                        })
                else:
                    # Neither valid
                    collation['stats']['uncertain'] += 1
                    if len(collation['uncertain']) < max_variants:
                        collation['uncertain'].append({
                            'position': i,
                            'gretil': g,
                            'sc': s,
                            'vri': None,
                            'bjt': b,
                            'thai': t,
                            'type': 'uncertain',
                            'notes': f'Neither reading validated: PTS "{g}" vs SC "{s}"'
                        })
            else:
                # One is missing
                collation['stats']['uncertain'] += 1
                if len(collation['uncertain']) < max_variants:
                    collation['uncertain'].append({
                        'position': i,
                        'gretil': g,
                        'sc': s,
                        'vri': None,
                        'bjt': b,
                        'thai': t,
                        'type': 'missing',
                        'notes': 'One reading missing'
                    })

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
    with_bjt = 0
    without_bjt = 0
    with_thai = 0
    without_thai = 0

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

        if collation.get('has_bjt'):
            with_bjt += 1
        else:
            without_bjt += 1
        if collation.get('has_thai'):
            with_thai += 1
        else:
            without_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        if processed % 100 == 0 or processed <= 10:
            markers = ""
            if collation.get('has_bjt'):
                markers += " [+BJT]"
            if collation.get('has_thai'):
                markers += " [+Thai]"
            print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        # Save collation - convert sn1.1 to sn1_1 for filename
        safe_id = sutta_id.replace('.', '_')
        output_file = output_dir / f"{safe_id}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_id,
            'has_bjt': collation.get('has_bjt', False),
            'has_thai': collation.get('has_thai', False),
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
    print(f"    With BJT: {with_bjt}")
    print(f"    Without BJT: {without_bjt}")
    print(f"    With Thai: {with_thai}")
    print(f"    Without Thai: {without_thai}")
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
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)',
                              'BJT (Buddha Jayanti)', 'Thai (Syām Raṭṭha)']
            },
            'dpd_words': len(dpd),
            'suttas_processed': len(results),
            'suttas_with_bjt': with_bjt,
            'suttas_without_bjt': without_bjt,
            'suttas_with_thai': with_thai,
            'suttas_without_thai': without_thai,
            'suttas_skipped': len(skipped),
            'skipped_ids': skipped[:100],
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
        print("Usage: python collate_nikaya.py <collection>")
        print("  Sutta Piṭaka: dn, mn, sn, an, kn")
        print("  Other: vinaya, abhidhamma")
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
        main_an(output_dir)
        return
    elif structure == 'khuddaka':
        main_kn(output_dir)
        return
    elif structure == 'vinaya':
        main_vinaya(output_dir)
        return
    elif structure == 'abhidhamma':
        main_abhidhamma(output_dir)
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
    with_bjt = 0
    without_bjt = 0
    with_thai = 0
    without_thai = 0

    for sutta_num in range(1, num_suttas + 1):
        print(f"Collating {nikaya.upper()} {sutta_num}...", end=" ")

        collation = collate_sutta(nikaya, sutta_num)

        if 'error' in collation:
            print(f"SKIPPED: {collation['error']}")
            skipped.append(sutta_num)
            continue

        if collation.get('has_bjt'):
            with_bjt += 1
        else:
            without_bjt += 1
        if collation.get('has_thai'):
            with_thai += 1
        else:
            without_thai += 1

        stats = collation['stats']
        total = stats['total_positions']
        match_pct = stats['match'] / total * 100 if total > 0 else 0

        markers = ""
        if collation.get('has_bjt'):
            markers += " [+BJT]"
        if collation.get('has_thai'):
            markers += " [+Thai]"
        print(f"Match: {match_pct:.1f}%, Errors: {stats['errors']}, Variants: {stats['variants']}{markers}")

        # Save collation
        output_file = output_dir / f"{nikaya}{sutta_num}_collation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collation, f, indent=2, ensure_ascii=False)

        results.append({
            'sutta': sutta_num,
            'has_bjt': collation.get('has_bjt', False),
            'has_thai': collation.get('has_thai', False),
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
    print(f"    With BJT: {with_bjt}")
    print(f"    Without BJT: {without_bjt}")
    print(f"    With Thai: {with_thai}")
    print(f"    Without Thai: {without_thai}")
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
                'witnesses': ['SC (Mahāsaṅgīti)', 'VRI (CST)',
                              'BJT (Buddha Jayanti)', 'Thai (Syām Raṭṭha)']
            },
            'dpd_words': len(dpd),
            'suttas_processed': len(results),
            'suttas_with_bjt': with_bjt,
            'suttas_without_bjt': without_bjt,
            'suttas_with_thai': with_thai,
            'suttas_without_thai': without_thai,
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
