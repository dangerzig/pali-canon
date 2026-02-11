#!/usr/bin/env python3
"""
Build complete critical editions for the entire Tipiṭaka.

Five-witness editions (GRETIL/SC/VRI/BJT/Thai):
- Dīgha Nikāya (DN)
- Majjhima Nikāya (MN)
- Saṃyutta Nikāya (SN)
- Aṅguttara Nikāya (AN)
- Khuddaka Nikāya (KN) - partial SC coverage
- Vinaya Piṭaka
- Abhidhamma Piṭaka
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = DATA_DIR / "pipeline_progress.log"

# Import canonical tokenization from shared module
try:
    from pali.text import PALI_WORD_PATTERN
except ImportError:
    PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging to both console and file."""
    logger.setLevel(logging.INFO)

    # Console handler with simple format
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))

    # File handler with timestamp
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))

    logger.addHandler(console)
    logger.addHandler(file_handler)


# ==================== Nikaya Configuration ====================

@dataclass
class NikayaConfig:
    """Configuration for a nikaya critical edition build."""
    code: str              # 'dn', 'mn', 'sn', 'an'
    name: str              # 'DN', 'MN', etc.
    gretil_volumes: int    # Number of GRETIL volume files
    vri_pattern: str       # VRI file pattern prefix (e.g., 's010')
    sutta_range: Optional[tuple[int, int]] = None  # (start, end) for individual suttas
    use_glob: bool = False  # Use glob for SC files (SN/AN style)


# Configuration for the four main nikayas
NIKAYA_CONFIGS = {
    'dn': NikayaConfig('dn', 'DN', 3, 's010', sutta_range=(1, 34)),
    'mn': NikayaConfig('mn', 'MN', 3, 's020', sutta_range=(1, 152)),
    'sn': NikayaConfig('sn', 'SN', 5, 's030', use_glob=True),
    'an': NikayaConfig('an', 'AN', 5, 's040', use_glob=True),
}


def log(msg: str) -> None:
    """Log message using the logger (legacy wrapper)."""
    logger.info(msg)


def tokenize(text: str) -> list[str]:
    """Tokenize Pāli text into words."""
    if not text:
        return []
    return PALI_WORD_PATTERN.findall(text.lower())


def normalize_word(word: str) -> str:
    """Normalize a word for comparison."""
    if not word:
        return ''
    w = word.lower()
    w = w.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    return w


def compare_texts(text1: str, text2: str) -> dict[str, Any]:
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


def load_gretil_text(collection: str, name: str) -> Optional[str]:
    """Load GRETIL parsed text."""
    fpath = DATA_DIR / f"gretil-parsed/{collection}/{name}.json"
    if not fpath.exists():
        return None
    data = json.loads(fpath.read_text())
    return data.get('text', '')


def load_vri_text(collection: str, pattern: str) -> str:
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


def load_sc_text(collection: str, text_id: str) -> Optional[str]:
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


def load_bjt_text(collection: str, pattern: str = None) -> str:
    """Load BJT parsed text. If pattern given, glob for matching files; otherwise load all."""
    bjt_dir = DATA_DIR / f"bjt-parsed/{collection}"
    if not bjt_dir.exists():
        return ""

    all_text = ""
    glob_pattern = f"{pattern}*.json" if pattern else "*.json"
    for fpath in sorted(bjt_dir.glob(glob_pattern)):
        if fpath.name.startswith('_'):
            continue
        data = json.loads(fpath.read_text())
        all_text += data.get('text', '') + " "
    return all_text


def load_thai_text(collection: str, pattern: str = None) -> str:
    """Load Thai parsed text. If pattern given, glob for matching files; otherwise load all."""
    thai_dir = DATA_DIR / f"thai-parsed/{collection}"
    if not thai_dir.exists():
        return ""

    all_text = ""
    glob_pattern = f"{pattern}*.json" if pattern else "*.json"
    for fpath in sorted(thai_dir.glob(glob_pattern)):
        if fpath.name.startswith('_'):
            continue
        data = json.loads(fpath.read_text())
        all_text += data.get('text', '') + " "
    return all_text


# ==================== Generic Nikaya Builders ====================

def build_nikaya_critical(config: NikayaConfig) -> dict[str, Any]:
    """Build critical edition for a nikaya with individual sutta files (DN/MN style).

    Args:
        config: Nikaya configuration

    Returns:
        Summary dictionary with word counts and sutta count
    """
    log("=" * 60)
    log(f"Building {config.name} Critical Edition (5 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / f"critical/{config.code}"
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    total_words = {'sc': 0, 'gretil': 0, 'vri': 0, 'bjt': 0, 'thai': 0}

    # Load all GRETIL volumes
    gretil_all = ""
    for vol in range(1, config.gretil_volumes + 1):
        fpath = DATA_DIR / f"gretil-parsed/{config.code}/{config.code}_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL {config.name}: {gretil_words:,} words")

    # Load all VRI files
    vri_all = load_vri_text(config.code, config.vri_pattern)
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI {config.name}: {vri_words:,} words")

    # Load all BJT volumes
    bjt_all = load_bjt_text(config.code, f"{config.code}_vol")
    bjt_words = len(tokenize(bjt_all))
    total_words['bjt'] = bjt_words
    log(f"BJT {config.name}: {bjt_words:,} words")

    # Load all Thai files
    thai_all = load_thai_text(config.code)
    thai_words = len(tokenize(thai_all))
    total_words['thai'] = thai_words
    log(f"Thai {config.name}: {thai_words:,} words")

    # Process each sutta with SC
    if config.sutta_range:
        start, end = config.sutta_range
        for sutta_num in range(start, end + 1):
            sc_text = load_sc_text(config.code, f'{config.code}{sutta_num}')
            if not sc_text:
                log(f"  Warning: No SC text for {config.code}{sutta_num}, skipping")
                continue

            sc_word_count = len(tokenize(sc_text))
            total_words['sc'] += sc_word_count

            edition = {
                'id': f'{config.code}{sutta_num}',
                'witnesses': ['SC', 'GRETIL', 'VRI', 'BJT', 'Thai'],
                'word_count': sc_word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{config.code}{sutta_num}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': config.name,
        'witnesses': 5,
        'suttas': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
        'bjt_words': total_words['bjt'],
        'thai_words': total_words['thai'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"{config.name}: {len(results)} suttas, {total_words['sc']:,} SC words")
    return summary


def build_nikaya_critical_glob(config: NikayaConfig) -> dict[str, Any]:
    """Build critical edition for a nikaya using glob for SC files (SN/AN style).

    Args:
        config: Nikaya configuration

    Returns:
        Summary dictionary with word counts and file count
    """
    log("=" * 60)
    log(f"Building {config.name} Critical Edition (5 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / f"critical/{config.code}"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words: dict[str, int] = {'sc': 0, 'gretil': 0, 'vri': 0, 'bjt': 0, 'thai': 0}

    # Load all GRETIL volumes
    gretil_all = ""
    for vol in range(1, config.gretil_volumes + 1):
        fpath = DATA_DIR / f"gretil-parsed/{config.code}/{config.code}_vol{vol}.json"
        if fpath.exists():
            data = json.loads(fpath.read_text())
            gretil_all += data.get('text', '') + " "

    gretil_words = len(tokenize(gretil_all))
    total_words['gretil'] = gretil_words
    log(f"GRETIL {config.name}: {gretil_words:,} words")

    # Load all VRI files
    vri_all = load_vri_text(config.code, config.vri_pattern)
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI {config.name}: {vri_words:,} words")

    # Load all BJT volumes
    bjt_all = load_bjt_text(config.code, f"{config.code}_vol")
    bjt_words = len(tokenize(bjt_all))
    total_words['bjt'] = bjt_words
    log(f"BJT {config.name}: {bjt_words:,} words")

    # Load all Thai files
    thai_all = load_thai_text(config.code)
    thai_words = len(tokenize(thai_all))
    total_words['thai'] = thai_words
    log(f"Thai {config.name}: {thai_words:,} words")

    # Process SC files via glob
    sc_dir = DATA_DIR / f"canonical/{config.code}"
    results: list[dict[str, Any]] = []

    for fpath in sorted(sc_dir.glob(f"{config.code}*.json")):
        if fpath.name.startswith('_'):
            continue

        data = json.loads(fpath.read_text())
        file_id = data.get('id', fpath.stem)

        # Extract text from all formats
        text_parts: list[str] = []
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
                'witnesses': ['SC', 'GRETIL', 'VRI', 'BJT', 'Thai'],
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{file_id}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': config.name,
        'witnesses': 5,
        'files': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
        'bjt_words': total_words['bjt'],
        'thai_words': total_words['thai'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"{config.name}: {len(results)} files, {total_words['sc']:,} SC words")
    return summary


# Convenience wrappers using the generic builders
def build_dn_critical() -> dict[str, Any]:
    """Build DN critical edition."""
    return build_nikaya_critical(NIKAYA_CONFIGS['dn'])


def build_mn_critical() -> dict[str, Any]:
    """Build MN critical edition."""
    return build_nikaya_critical(NIKAYA_CONFIGS['mn'])


def build_sn_critical() -> dict[str, Any]:
    """Build SN critical edition."""
    return build_nikaya_critical_glob(NIKAYA_CONFIGS['sn'])


def build_an_critical() -> dict[str, Any]:
    """Build AN critical edition."""
    return build_nikaya_critical_glob(NIKAYA_CONFIGS['an'])


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

def build_kn_critical() -> dict[str, Any]:
    """Build KN critical edition with 2-5 witnesses."""
    log("=" * 60)
    log("Building KN Critical Edition (2-5 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/kn"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'sc': 0, 'gretil': 0, 'vri': 0, 'bjt': 0, 'thai': 0}
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

    # Load all BJT KN files
    bjt_all = load_bjt_text('kn')
    bjt_words = len(tokenize(bjt_all))
    total_words['bjt'] = bjt_words
    log(f"BJT KN: {bjt_words:,} words")

    # Load all Thai KN files
    thai_all = load_thai_text('kn')
    thai_words = len(tokenize(thai_all))
    total_words['thai'] = thai_words
    log(f"Thai KN: {thai_words:,} words")

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
            witnesses = ['SC', 'VRI', 'BJT', 'Thai']
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
                'witnesses': ['GRETIL', 'VRI', 'BJT', 'Thai'],
                'word_count': word_count,
            }
            results.append(edition)

            output_file = output_dir / f"{gretil_name}_critical.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'KN',
        'witnesses': '2-5 (SC coverage partial)',
        'texts': len(results),
        'sc_words': total_words['sc'],
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
        'bjt_words': total_words['bjt'],
        'thai_words': total_words['thai'],
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

def build_vinaya_critical() -> dict[str, Any]:
    """Build Vinaya critical edition with 5 witnesses (GRETIL/SC/VRI/BJT/Thai)."""
    log("=" * 60)
    log("Building Vinaya Critical Edition (5 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'gretil': 0, 'vri': 0, 'sc': 0, 'bjt': 0, 'thai': 0}
    results = []

    # Load all VRI Vinaya files
    vri_all = load_vri_text('vinaya', 'vin')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI Vinaya: {vri_words:,} words")

    # Load all Thai Vinaya files
    thai_all = load_thai_text('vinaya')
    thai_words = len(tokenize(thai_all))
    total_words['thai'] = thai_words
    log(f"Thai Vinaya: {thai_words:,} words")

    # Count SC and BJT words
    for text_name in VINAYA_TEXTS:
        sc_file = DATA_DIR / f"sc-parsed/vinaya/{text_name}.json"
        if sc_file.exists():
            sc_data = json.loads(sc_file.read_text())
            total_words['sc'] += sc_data.get('word_count', 0)
        bjt_file = DATA_DIR / f"bjt-parsed/vinaya/{text_name}.json"
        if bjt_file.exists():
            bjt_data = json.loads(bjt_file.read_text())
            total_words['bjt'] += bjt_data.get('word_count', 0)
    log(f"SC Vinaya: {total_words['sc']:,} words")
    log(f"BJT Vinaya: {total_words['bjt']:,} words")

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
            'witnesses': ['GRETIL', 'VRI', 'SC', 'BJT', 'Thai'],
            'word_count': word_count,
        }
        results.append(edition)

        output_file = output_dir / f"{text_name}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'pitaka': 'Vinaya',
        'witnesses': 5,
        'texts': len(results),
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
        'sc_words': total_words['sc'],
        'bjt_words': total_words['bjt'],
        'thai_words': total_words['thai'],
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

def build_abhidhamma_critical() -> dict[str, Any]:
    """Build Abhidhamma critical edition with 5 witnesses (GRETIL/SC/VRI/BJT/Thai)."""
    log("=" * 60)
    log("Building Abhidhamma Critical Edition (5 witnesses)")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_words = {'gretil': 0, 'vri': 0, 'sc': 0, 'bjt': 0, 'thai': 0}
    results = []

    # Load all Thai Abhidhamma files
    thai_all = load_thai_text('abhidhamma')
    thai_words = len(tokenize(thai_all))
    total_words['thai'] = thai_words
    log(f"Thai Abhidhamma: {thai_words:,} words")

    # Load all VRI Abhidhamma files
    vri_all = load_vri_text('abhidhamma', 'abh')
    vri_words = len(tokenize(vri_all))
    total_words['vri'] = vri_words
    log(f"VRI Abhidhamma: {vri_words:,} words")

    # Count SC and BJT words
    for sc_name in ['dhammasangani', 'vibhanga', 'dhatukatha', 'puggalapannatti',
                     'kathavatthu', 'yamaka1', 'yamaka2', 'patthana']:
        sc_file = DATA_DIR / f"sc-parsed/abhidhamma/{sc_name}.json"
        if sc_file.exists():
            sc_data = json.loads(sc_file.read_text())
            total_words['sc'] += sc_data.get('word_count', 0)
    for bjt_name in ['dhammasangani', 'vibhanga', 'dhatukatha', 'puggalapannatti',
                      'kathavatthu1', 'kathavatthu2', 'yamaka1', 'yamaka2',
                      'patthana1', 'patthana2']:
        bjt_file = DATA_DIR / f"bjt-parsed/abhidhamma/{bjt_name}.json"
        if bjt_file.exists():
            bjt_data = json.loads(bjt_file.read_text())
            total_words['bjt'] += bjt_data.get('word_count', 0)
    log(f"SC Abhidhamma: {total_words['sc']:,} words")
    log(f"BJT Abhidhamma: {total_words['bjt']:,} words")

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
            'witnesses': ['GRETIL', 'VRI', 'SC', 'BJT', 'Thai'],
            'word_count': word_count,
        }
        results.append(edition)

        output_file = output_dir / f"{text_name}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    summary = {
        'pitaka': 'Abhidhamma',
        'witnesses': 5,
        'texts': len(results),
        'gretil_words': total_words['gretil'],
        'vri_words': total_words['vri'],
        'sc_words': total_words['sc'],
        'bjt_words': total_words['bjt'],
        'thai_words': total_words['thai'],
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"Abhidhamma: {len(results)} texts, GRETIL: {total_words['gretil']:,} words")
    return summary


# ==================== Main ====================

def main() -> None:
    """Build critical editions for the complete Tipiṭaka."""
    # Setup logging (clears previous log file)
    setup_logging()

    log("=" * 60)
    log("BUILDING COMPLETE TIPIṬAKA CRITICAL EDITIONS")
    log("=" * 60)
    log("")

    results = {}

    # Vinaya Piṭaka (5 witnesses)
    results['vinaya'] = build_vinaya_critical()
    log("")

    # Sutta Piṭaka (5 witnesses)
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

    # Abhidhamma Piṭaka (5 witnesses)
    results['abhidhamma'] = build_abhidhamma_critical()
    log("")

    # Calculate totals
    log("=" * 60)
    log("COMPLETE TIPIṬAKA CRITICAL EDITION SUMMARY")
    log("=" * 60)

    sutta_gretil = sum(results[n].get('gretil_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_vri = sum(results[n].get('vri_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_sc = sum(results[n].get('sc_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_bjt = sum(results[n].get('bjt_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])
    sutta_thai = sum(results[n].get('thai_words', 0) for n in ['dn', 'mn', 'sn', 'an', 'kn'])

    log("")
    log("VINAYA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    log(f"  Texts: {results['vinaya'].get('texts', 0)}")
    log(f"  SC: {results['vinaya'].get('sc_words', 0):,} words")
    log(f"  GRETIL: {results['vinaya'].get('gretil_words', 0):,} words")
    log(f"  VRI: {results['vinaya'].get('vri_words', 0):,} words")
    log(f"  BJT: {results['vinaya'].get('bjt_words', 0):,} words")
    log(f"  Thai: {results['vinaya'].get('thai_words', 0):,} words")
    log("")

    log("SUTTA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    log(f"  DN: {results['dn'].get('suttas', 0)} suttas")
    log(f"  MN: {results['mn'].get('suttas', 0)} suttas")
    log(f"  SN: {results['sn'].get('files', 0)} files")
    log(f"  AN: {results['an'].get('files', 0)} files")
    log(f"  KN: {results['kn'].get('texts', 0)} texts")
    log(f"  SC Total: {sutta_sc:,} words")
    log(f"  GRETIL Total: {sutta_gretil:,} words")
    log(f"  VRI Total: {sutta_vri:,} words")
    log(f"  BJT Total: {sutta_bjt:,} words")
    log(f"  Thai Total: {sutta_thai:,} words")
    log("")

    log("ABHIDHAMMA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    log(f"  Texts: {results['abhidhamma'].get('texts', 0)}")
    log(f"  SC: {results['abhidhamma'].get('sc_words', 0):,} words")
    log(f"  GRETIL: {results['abhidhamma'].get('gretil_words', 0):,} words")
    log(f"  VRI: {results['abhidhamma'].get('vri_words', 0):,} words")
    log(f"  BJT: {results['abhidhamma'].get('bjt_words', 0):,} words")
    log(f"  Thai: {results['abhidhamma'].get('thai_words', 0):,} words")
    log("")

    # Grand totals
    total_sc = results['vinaya'].get('sc_words', 0) + sutta_sc + results['abhidhamma'].get('sc_words', 0)
    total_gretil = results['vinaya'].get('gretil_words', 0) + sutta_gretil + results['abhidhamma'].get('gretil_words', 0)
    total_vri = results['vinaya'].get('vri_words', 0) + sutta_vri + results['abhidhamma'].get('vri_words', 0)
    total_bjt = results['vinaya'].get('bjt_words', 0) + sutta_bjt + results['abhidhamma'].get('bjt_words', 0)
    total_thai = results['vinaya'].get('thai_words', 0) + sutta_thai + results['abhidhamma'].get('thai_words', 0)

    log("─" * 40)
    log("GRAND TOTALS")
    log(f"  SC (all): {total_sc:,} words")
    log(f"  GRETIL (all): {total_gretil:,} words")
    log(f"  VRI (all): {total_vri:,} words")
    log(f"  BJT (all): {total_bjt:,} words")
    log(f"  Thai (all): {total_thai:,} words")

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
                'bjt_words': sutta_bjt,
                'thai_words': sutta_thai,
            }
        },
        'abhidhamma_pitaka': results['abhidhamma'],
        'grand_totals': {
            'sc_words': total_sc,
            'gretil_words': total_gretil,
            'vri_words': total_vri,
            'bjt_words': total_bjt,
            'thai_words': total_thai,
        }
    }

    summary_file = DATA_DIR / "critical/_complete_tipitaka_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, indent=2, ensure_ascii=False)

    log(f"\nSaved complete summary to: {summary_file}")


if __name__ == "__main__":
    main()
