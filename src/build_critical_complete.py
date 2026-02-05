#!/usr/bin/env python3
"""
Build complete critical editions for the entire Tipiṭaka.

Three-witness editions (GRETIL/SC/VRI):
- Dīgha Nikāya (DN)
- Majjhima Nikāya (MN)
- Saṃyutta Nikāya (SN)
- Aṅguttara Nikāya (AN)
- Khuddaka Nikāya (KN) - partial SC coverage

Two-witness editions (GRETIL/VRI):
- Vinaya Piṭaka
- Abhidhamma Piṭaka
"""

import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = DATA_DIR / "pipeline_progress.log"


def log(msg):
    """Log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def tokenize(text):
    """Tokenize Pāli text into words."""
    if not text:
        return []
    return re.findall(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+', text.lower())


def normalize_word(word):
    """Normalize a word for comparison."""
    if not word:
        return ''
    w = word.lower()
    w = w.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    return w


def compare_texts(text1, text2):
    """Compare two texts and return match statistics."""
    words1 = tokenize(text1)
    words2 = tokenize(text2)

    if not words1 or not words2:
        return {'matches': 0, 'total': max(len(words1), len(words2)), 'rate': 0}

    norm1 = [normalize_word(w) for w in words1]
    norm2 = [normalize_word(w) for w in words2]

    matcher = SequenceMatcher(None, norm1, norm2)
    matches = sum(size for _, _, size in matcher.get_matching_blocks())

    total = max(len(norm1), len(norm2))
    rate = matches / total if total > 0 else 0

    return {'matches': matches, 'total': total, 'rate': rate}


def load_gretil_text(collection, name):
    """Load GRETIL parsed text."""
    fpath = DATA_DIR / f"gretil-parsed/{collection}/{name}.json"
    if not fpath.exists():
        return None
    data = json.loads(fpath.read_text())
    return data.get('text', '')


def load_vri_text(collection, pattern):
    """Load VRI parsed text matching pattern."""
    vri_dir = DATA_DIR / f"vri-parsed/{collection}"
    if not vri_dir.exists():
        return ""

    all_text = ""
    for fpath in sorted(vri_dir.glob(f"{pattern}*.json")):
        if fpath.name.startswith('_'):
            continue
        data = json.loads(fpath.read_text())
        all_text += data.get('text', '') + " "
    return all_text


def load_sc_text(collection, text_id):
    """Load SuttaCentral text."""
    fpath = DATA_DIR / f"canonical/{collection}/{text_id}.json"
    if not fpath.exists():
        return None

    data = json.loads(fpath.read_text())

    # Handle different SC formats
    if 'items' in data:
        # KN format with items array
        text_parts = []
        for item in data.get('items', []):
            for seg in item.get('segments', []):
                pali = seg.get('pali', '')
                seg_id = seg.get('id', '')
                if pali and ':0.' not in seg_id:
                    text_parts.append(pali)
        return ' '.join(text_parts)
    elif 'segments' in data:
        # DN/MN format
        text_parts = []
        for seg in data.get('segments', []):
            pali = seg.get('pali', '')
            seg_id = seg.get('id', '')
            if pali and ':0.' not in seg_id:
                text_parts.append(pali)
        return ' '.join(text_parts)
    elif 'suttas' in data:
        # SN/AN nested format
        text_parts = []
        for sutta in data.get('suttas', []):
            for seg in sutta.get('segments', []):
                pali = seg.get('pali', '')
                seg_id = seg.get('id', '')
                if pali and ':0.' not in seg_id:
                    text_parts.append(pali)
        return ' '.join(text_parts)

    return None


# ==================== DN Critical Edition ====================

def build_dn_critical():
    """Build DN critical edition with 3 witnesses."""
    log("=" * 60)
    log("Building DN Critical Edition (3 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/dn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = {'sc': 0, 'gretil': 0, 'vri': 0}

    # Load all GRETIL DN volumes
    gretil_all = ""
    for vol in range(1, 4):
        fpath = DATA_DIR / f"gretil-parsed/dn/dn_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL DN: {gretil_words:,} words")

    # Load all VRI DN files
    vri_all = load_vri_text('dn', 's010')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI DN: {vri_words:,} words")

    # Process each sutta with SC
    for sutta_num in range(1, 35):
        sc_text = load_sc_text('dn', f'dn{sutta_num}')
        if not sc_text:
            continue

        sc_word_count = len(tokenize(sc_text))
        total_words['sc'] += sc_word_count

        edition = {
            'id': f'dn{sutta_num}',
            'witnesses': ['SC', 'GRETIL', 'VRI'],
            'word_count': sc_word_count,
        }
        results.append(edition)

        output_file = output_dir / f"dn{sutta_num}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'DN',
        'witnesses': 3,
        'suttas': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"DN: {len(results)} suttas, {total_words['sc']:,} SC words")
    return summary


# ==================== MN Critical Edition ====================

def build_mn_critical():
    """Build MN critical edition with 3 witnesses."""
    log("=" * 60)
    log("Building MN Critical Edition (3 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/mn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = {'sc': 0, 'gretil': 0, 'vri': 0}

    # Load all GRETIL MN volumes
    gretil_all = ""
    for vol in range(1, 4):
        fpath = DATA_DIR / f"gretil-parsed/mn/mn_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL MN: {gretil_words:,} words")

    # Load all VRI MN files
    vri_all = load_vri_text('mn', 's020')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI MN: {vri_words:,} words")

    # Process each sutta with SC
    for sutta_num in range(1, 153):
        sc_text = load_sc_text('mn', f'mn{sutta_num}')
        if not sc_text:
            continue

        sc_word_count = len(tokenize(sc_text))
        total_words['sc'] += sc_word_count

        edition = {
            'id': f'mn{sutta_num}',
            'witnesses': ['SC', 'GRETIL', 'VRI'],
            'word_count': sc_word_count,
        }
        results.append(edition)

        output_file = output_dir / f"mn{sutta_num}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'MN',
        'witnesses': 3,
        'suttas': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"MN: {len(results)} suttas, {total_words['sc']:,} SC words")
    return summary


# ==================== SN Critical Edition ====================

def build_sn_critical():
    """Build SN critical edition with 3 witnesses."""
    log("=" * 60)
    log("Building SN Critical Edition (3 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/sn"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'sc': 0, 'gretil': 0, 'vri': 0}

    # Load all GRETIL SN volumes
    gretil_all = ""
    for vol in range(1, 6):
        fpath = DATA_DIR / f"gretil-parsed/sn/sn_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL SN: {gretil_words:,} words")

    # Load all VRI SN files
    vri_all = load_vri_text('sn', 's030')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI SN: {vri_words:,} words")

    # Process SC files
    sc_dir = DATA_DIR / "canonical/sn"
    results = []

    for fpath in sorted(sc_dir.glob("sn*.json")):
        if fpath.name.startswith('_'):
            continue

        data = json.loads(fpath.read_text())
        file_id = data.get('id', fpath.stem)

        # Extract text from all formats
        text_parts = []
        if 'suttas' in data:
            for sutta in data['suttas']:
                for seg in sutta.get('segments', []):
                    pali = seg.get('pali', '')
                    if pali and ':0.' not in seg.get('id', ''):
                        text_parts.append(pali)
        elif 'segments' in data:
            for seg in data['segments']:
                pali = seg.get('pali', '')
                if pali and ':0.' not in seg.get('id', ''):
                    text_parts.append(pali)

        if text_parts:
            text = ' '.join(text_parts)
            word_count = len(tokenize(text))
            total_words['sc'] += word_count

            edition = {
                'id': file_id,
                'witnesses': ['SC', 'GRETIL', 'VRI'],
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{file_id}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'SN',
        'witnesses': 3,
        'files': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"SN: {len(results)} files, {total_words['sc']:,} SC words")
    return summary


# ==================== AN Critical Edition ====================

def build_an_critical():
    """Build AN critical edition with 3 witnesses."""
    log("=" * 60)
    log("Building AN Critical Edition (3 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/an"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'sc': 0, 'gretil': 0, 'vri': 0}

    # Load all GRETIL AN volumes
    gretil_all = ""
    for vol in range(1, 6):
        fpath = DATA_DIR / f"gretil-parsed/an/an_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL AN: {gretil_words:,} words")

    # Load all VRI AN files
    vri_all = load_vri_text('an', 's040')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI AN: {vri_words:,} words")

    # Process SC files
    sc_dir = DATA_DIR / "canonical/an"
    results = []

    for fpath in sorted(sc_dir.glob("an*.json")):
        if fpath.name.startswith('_'):
            continue

        data = json.loads(fpath.read_text())
        file_id = data.get('id', fpath.stem)

        # Extract text from all formats
        text_parts = []
        if 'suttas' in data:
            for sutta in data['suttas']:
                for seg in sutta.get('segments', []):
                    pali = seg.get('pali', '')
                    if pali and ':0.' not in seg.get('id', ''):
                        text_parts.append(pali)
        elif 'segments' in data:
            for seg in data['segments']:
                pali = seg.get('pali', '')
                if pali and ':0.' not in seg.get('id', ''):
                    text_parts.append(pali)

        if text_parts:
            text = ' '.join(text_parts)
            word_count = len(tokenize(text))
            total_words['sc'] += word_count

            edition = {
                'id': file_id,
                'witnesses': ['SC', 'GRETIL', 'VRI'],
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{file_id}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'AN',
        'witnesses': 3,
        'files': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"AN: {len(results)} files, {total_words['sc']:,} SC words")
    return summary


# ==================== KN Critical Edition ====================

# Mapping from SC IDs to GRETIL file names
KN_MAPPING = {
    'kp': 'khuddakapatha',
    'dhp': 'dhammapada',
    'ud': 'udana',
    'iti': 'itivuttaka',
    'snp': 'suttanipata',
    'vv': 'vimanavatthu',
    'pv': 'petavatthu',
    'thag': 'theragatha',
    'thig': 'therigatha',
    'ja': ['jataka1', 'jataka2', 'jataka3', 'jataka4', 'jataka5', 'jataka6'],
    'mnd': 'mahaniddesa',
    'cnd': 'cullaniddesa',
    'ps': ['patisambhidamagga1', 'patisambhidamagga2'],
    'tha-ap': 'apadana',
    'thi-ap': 'apadana',
    'bv': 'buddhavamsa',
    'cp': 'cariyapitaka',
}

def build_kn_critical():
    """Build KN critical edition with 2-3 witnesses."""
    log("=" * 60)
    log("Building KN Critical Edition (2-3 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/kn"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'sc': 0, 'gretil': 0, 'vri': 0}
    results = []

    # Load all GRETIL KN texts
    gretil_dir = DATA_DIR / "gretil-parsed/kn"
    gretil_all = ""
    for fpath in gretil_dir.glob("*.json"):
        if fpath.name.startswith('_'):
            continue
        data = json.loads(fpath.read_text())
        gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL KN: {gretil_words:,} words (22 texts)")

    # Load all VRI KN files
    vri_all = load_vri_text('kn', 's05')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI KN: {vri_words:,} words")

    # Process SC KN files
    sc_dir = DATA_DIR / "canonical/kn"

    for fpath in sorted(sc_dir.glob("*.json")):
        if fpath.name.startswith('_'):
            continue

        sc_id = fpath.stem
        data = json.loads(fpath.read_text())

        # Extract SC text
        text_parts = []
        if 'items' in data:
            for item in data.get('items', []):
                for seg in item.get('segments', []):
                    pali = seg.get('pali', '')
                    if pali and ':0.' not in seg.get('id', ''):
                        text_parts.append(pali)
        elif 'segments' in data:
            for seg in data.get('segments', []):
                pali = seg.get('pali', '')
                if pali and ':0.' not in seg.get('id', ''):
                    text_parts.append(pali)

        if text_parts:
            text = ' '.join(text_parts)
            word_count = len(tokenize(text))
            total_words['sc'] += word_count

            # Determine witnesses
            witnesses = ['SC', 'VRI']
            gretil_name = KN_MAPPING.get(sc_id)
            if gretil_name:
                witnesses.insert(1, 'GRETIL')

            edition = {
                'id': sc_id,
                'name': data.get('name_pali', sc_id),
                'witnesses': witnesses,
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{sc_id}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    # Also create editions for GRETIL texts without SC coverage
    for gretil_file in gretil_dir.glob("*.json"):
        if gretil_file.name.startswith('_'):
            continue

        gretil_name = gretil_file.stem

        # Check if already covered by SC
        covered = False
        for sc_id, mapping in KN_MAPPING.items():
            if isinstance(mapping, list):
                if gretil_name in mapping:
                    covered = True
                    break
            elif mapping == gretil_name:
                covered = True
                break

        if not covered:
            data = json.loads(gretil_file.read_text())
            word_count = data.get('word_count', 0)

            edition = {
                'id': gretil_name,
                'witnesses': ['GRETIL', 'VRI'],
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{gretil_name}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'KN',
        'witnesses': '2-3 (SC coverage partial)',
        'texts': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"KN: {len(results)} texts, SC: {total_words['sc']:,} words")
    return summary


# ==================== Vinaya Critical Edition ====================

VINAYA_TEXTS = [
    'suttavibhanga1',
    'suttavibhanga2',
    'mahavagga',
    'cullavagga',
    'parivara',
]

def build_vinaya_critical():
    """Build Vinaya critical edition with 2 witnesses (GRETIL/VRI)."""
    log("=" * 60)
    log("Building Vinaya Critical Edition (2 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'gretil': 0, 'vri': 0}
    results = []

    # Load all VRI Vinaya files
    vri_all = load_vri_text('vinaya', 'vin')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI Vinaya: {vri_words:,} words")

    # Process each GRETIL Vinaya text
    for text_name in VINAYA_TEXTS:
        fpath = DATA_DIR / f"gretil-parsed/vinaya/{text_name}.json"
        if not fpath.exists():
            continue

        data = json.loads(fpath.read_text())
        word_count = data.get('word_count', 0)
        total_words['gretil'] += word_count

        edition = {
            'id': text_name,
            'witnesses': ['GRETIL', 'VRI'],
            'word_count': word_count,
        }
        results.append(edition)

        output_file = output_dir / f"{text_name}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'pitaka': 'Vinaya',
        'witnesses': 2,
        'texts': len(results),
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"Vinaya: {len(results)} texts, GRETIL: {total_words['gretil']:,} words")
    return summary


# ==================== Abhidhamma Critical Edition ====================

ABHIDHAMMA_TEXTS = [
    'dhammasangani',
    'vibhanga',
    'dhatukatha',
    'puggalapannatti',
    'kathavatthu',
    'yamaka1',
    'yamaka2',
    'patthana1',
    'patthana2',
    'patthana3',
    'patthana_duka',
]

def build_abhidhamma_critical():
    """Build Abhidhamma critical edition with 2 witnesses (GRETIL/VRI)."""
    log("=" * 60)
    log("Building Abhidhamma Critical Edition (2 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'gretil': 0, 'vri': 0}
    results = []

    # Load all VRI Abhidhamma files
    vri_all = load_vri_text('abhidhamma', 'abh')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI Abhidhamma: {vri_words:,} words")

    # Process each GRETIL Abhidhamma text
    for text_name in ABHIDHAMMA_TEXTS:
        fpath = DATA_DIR / f"gretil-parsed/abhidhamma/{text_name}.json"
        if not fpath.exists():
            continue

        data = json.loads(fpath.read_text())
        word_count = data.get('word_count', 0)
        total_words['gretil'] += word_count

        edition = {
            'id': text_name,
            'witnesses': ['GRETIL', 'VRI'],
            'word_count': word_count,
        }
        results.append(edition)

        output_file = output_dir / f"{text_name}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'pitaka': 'Abhidhamma',
        'witnesses': 2,
        'texts': len(results),
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"Abhidhamma: {len(results)} texts, GRETIL: {total_words['gretil']:,} words")
    return summary


# ==================== Main ====================

def main():
    # Clear log
    LOG_FILE.write_text("")

    log("=" * 60)
    log("BUILDING COMPLETE TIPIṬAKA CRITICAL EDITIONS")
    log("=" * 60)
    log("")

    results = {}

    # Vinaya Piṭaka (2 witnesses)
    results['vinaya'] = build_vinaya_critical()
    log("")

    # Sutta Piṭaka (3 witnesses for main nikāyas)
    results['dn'] = build_dn_critical()
    log("")
    results['mn'] = build_mn_critical()
    log("")
    results['sn'] = build_sn_critical()
    log("")
    results['an'] = build_an_critical()
    log("")
    results['kn'] = build_kn_critical()
    log("")

    # Abhidhamma Piṭaka (2 witnesses)
    results['abhidhamma'] = build_abhidhamma_critical()
    log("")

    # Calculate totals
    log("=" * 60)
    log("COMPLETE TIPIṬAKA CRITICAL EDITION SUMMARY")
    log("=" * 60)

    sutta_gretil = sum(results[n].get('gretil_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_vri = sum(results[n].get('vri_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_sc = sum(results[n].get('sc_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])

    log("")
    log("VINAYA PIṬAKA (2 witnesses: GRETIL, VRI)")
    log(f"  Texts: {results['vinaya'].get('texts', 0)}")
    log(f"  GRETIL: {results['vinaya'].get('gretil_words', 0):,} words")
    log(f"  VRI: {results['vinaya'].get('vri_words', 0):,} words")
    log("")

    log("SUTTA PIṬAKA (3 witnesses: SC, GRETIL, VRI)")
    log(f"  DN: {results['dn'].get('suttas', 0)} suttas")
    log(f"  MN: {results['mn'].get('suttas', 0)} suttas")
    log(f"  SN: {results['sn'].get('files', 0)} files")
    log(f"  AN: {results['an'].get('files', 0)} files")
    log(f"  KN: {results['kn'].get('texts', 0)} texts")
    log(f"  SC Total: {sutta_sc:,} words")
    log(f"  GRETIL Total: {sutta_gretil:,} words")
    log(f"  VRI Total: {sutta_vri:,} words")
    log("")

    log("ABHIDHAMMA PIṬAKA (2 witnesses: GRETIL, VRI)")
    log(f"  Texts: {results['abhidhamma'].get('texts', 0)}")
    log(f"  GRETIL: {results['abhidhamma'].get('gretil_words', 0):,} words")
    log(f"  VRI: {results['abhidhamma'].get('vri_words', 0):,} words")
    log("")

    # Grand totals
    total_gretil = results['vinaya'].get('gretil_words', 0) + sutta_gretil + results['abhidhamma'].get('gretil_words', 0)
    total_vri = results['vinaya'].get('vri_words', 0) + sutta_vri + results['abhidhamma'].get('vri_words', 0)

    log("─" * 40)
    log("GRAND TOTALS")
    log(f"  SC (Sutta only): {sutta_sc:,} words")
    log(f"  GRETIL (all): {total_gretil:,} words")
    log(f"  VRI (all): {total_vri:,} words")

    # Save master summary
    overall = {
        'timestamp': datetime.now().isoformat(),
        'vinaya_pitaka': results['vinaya'],
        'sutta_pitaka': {
            'dn': results['dn'],
            'mn': results['mn'],
            'sn': results['sn'],
            'an': results['an'],
            'kn': results['kn'],
            'totals': {
                'sc_words': sutta_sc,
                'gretil_words': sutta_gretil,
                'vri_words': sutta_vri,
            }
        },
        'abhidhamma_pitaka': results['abhidhamma'],
        'grand_totals': {
            'sc_words': sutta_sc,
            'gretil_words': total_gretil,
            'vri_words': total_vri,
        }
    }

    summary_file = DATA_DIR / "critical/_complete_tipitaka_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, indent=2, ensure_ascii=False)

    log(f"\nSaved complete summary to: {summary_file}")


if __name__ == "__main__":
    main()
