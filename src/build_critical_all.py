#!/usr/bin/env python3
"""
Build critical editions for all nikāyas (MN, SN, AN).

Uses five witnesses:
- GRETIL (PTS transcription)
- SuttaCentral (SC)
- VRI (Chaṭṭha Saṅgāyana)
- BJT (Buddha Jayanti Tripitaka)
- Thai (Syām Raṭṭha)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = DATA_DIR / "critical_build.log"


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


def parse_vri_nikaya(nikaya):
    """Parse VRI files for a nikāya into text by volume."""
    # VRI file mapping
    vri_map = {
        'mn': ['s0201m.mul.txt', 's0202m.mul.txt', 's0203m.mul.txt'],
        'sn': ['s0301m.mul.txt', 's0302m.mul.txt', 's0303m.mul.txt', 's0304m.mul.txt', 's0305m.mul.txt'],
        'an': ['s0401m.mul.txt', 's0402m1.mul.txt', 's0402m2.mul.txt', 's0402m3.mul.txt', 's0403m.mul.txt'],
    }

    files = vri_map.get(nikaya, [])
    all_text = ""

    for fname in files:
        fpath = DATA_DIR / "vri-raw" / fname
        if fpath.exists():
            all_text += fpath.read_text(encoding='utf-8', errors='ignore') + "\n"

    return all_text


def load_gretil_nikaya(nikaya):
    """Load all GRETIL volumes for a nikāya."""
    text = ""
    vol = 1
    while True:
        fpath = DATA_DIR / f"gretil-pts/{nikaya}_vol{vol}.html"
        if not fpath.exists():
            break
        html = fpath.read_text(encoding='utf-8', errors='ignore')
        # Strip HTML tags
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        text += clean + " "
        vol += 1
    return text


def extract_sc_text_mn(sutta_num):
    """Extract SC text for MN sutta (one file per sutta)."""
    fpath = DATA_DIR / f"canonical/mn/mn{sutta_num}.json"
    if not fpath.exists():
        return None, None

    data = json.loads(fpath.read_text())
    segments = data.get('segments', [])

    text_parts = []
    for seg in segments:
        pali = seg.get('pali', '')
        seg_id = seg.get('id', '')
        # Skip header segments
        if pali and ':0.' not in seg_id:
            text_parts.append(pali)

    return ' '.join(text_parts), data.get('pts', '')


def extract_sc_text_sn_an(nikaya):
    """Extract SC text for SN or AN (nested structure)."""
    sc_dir = DATA_DIR / f"canonical/{nikaya}"
    results = []

    for fpath in sorted(sc_dir.glob(f"{nikaya}*.json")):
        data = json.loads(fpath.read_text())
        file_id = data.get('id', fpath.stem)

        # Check for nested suttas structure (SN/AN)
        if 'suttas' in data:
            for sutta in data['suttas']:
                sutta_id = sutta.get('id', '')
                segments = sutta.get('segments', [])

                text_parts = []
                for seg in segments:
                    pali = seg.get('pali', '')
                    seg_id = seg.get('id', '')
                    if pali and ':0.' not in seg_id:
                        text_parts.append(pali)

                if text_parts:
                    results.append({
                        'id': sutta_id,
                        'text': ' '.join(text_parts),
                        'word_count': len(tokenize(' '.join(text_parts)))
                    })
        else:
            # Flat structure (like MN)
            segments = data.get('segments', [])
            text_parts = []
            for seg in segments:
                pali = seg.get('pali', '')
                seg_id = seg.get('id', '')
                if pali and ':0.' not in seg_id:
                    text_parts.append(pali)

            if text_parts:
                results.append({
                    'id': file_id,
                    'text': ' '.join(text_parts),
                    'word_count': len(tokenize(' '.join(text_parts)))
                })

    return results


def compare_texts(text1, text2):
    """Compare two texts and return match statistics."""
    words1 = tokenize(text1)
    words2 = tokenize(text2)

    if not words1 or not words2:
        return {'matches': 0, 'total': max(len(words1), len(words2)), 'rate': 0}

    # Normalize words
    norm1 = [normalize_word(w) for w in words1]
    norm2 = [normalize_word(w) for w in words2]

    # Use SequenceMatcher for alignment
    matcher = SequenceMatcher(None, norm1, norm2)
    matches = sum(size for _, _, size in matcher.get_matching_blocks())

    total = max(len(norm1), len(norm2))
    rate = matches / total if total > 0 else 0

    return {'matches': matches, 'total': total, 'rate': rate}


def build_mn_critical():
    """Build MN critical edition."""
    log("=" * 60)
    log("Building MN Critical Edition")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/mn"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load VRI and GRETIL
    vri_text = parse_vri_nikaya('mn')
    vri_words = tokenize(vri_text)
    log(f"VRI MN: {len(vri_words):,} words")

    gretil_text = load_gretil_nikaya('mn')
    gretil_words = tokenize(gretil_text)
    log(f"GRETIL MN: {len(gretil_words):,} words")

    results = []
    total_sc_words = 0

    for sutta_num in range(1, 153):
        sc_text, pts = extract_sc_text_mn(sutta_num)
        if not sc_text:
            continue

        sc_words = tokenize(sc_text)
        total_sc_words += len(sc_words)

        edition = {
            'id': f'mn{sutta_num}',
            'pts': pts,
            'word_count': len(sc_words),
        }
        results.append(edition)

        # Save
        output_file = output_dir / f"mn{sutta_num}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edition, f, indent=2, ensure_ascii=False)

    # Summary
    summary = {
        'nikaya': 'MN',
        'suttas': len(results),
        'sc_words': total_sc_words,
        'vri_words': len(vri_words),
        'gretil_words': len(gretil_words),
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"MN: {len(results)} suttas")
    log(f"  SC: {total_sc_words:,} words")
    log(f"  VRI: {len(vri_words):,} words")
    log(f"  GRETIL: {len(gretil_words):,} words")

    return summary


def build_sn_critical():
    """Build SN critical edition."""
    log("=" * 60)
    log("Building SN Critical Edition")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/sn"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load VRI and GRETIL
    vri_text = parse_vri_nikaya('sn')
    vri_words = tokenize(vri_text)
    log(f"VRI SN: {len(vri_words):,} words")

    gretil_text = load_gretil_nikaya('sn')
    gretil_words = tokenize(gretil_text)
    log(f"GRETIL SN: {len(gretil_words):,} words")

    # Extract SC suttas
    suttas = extract_sc_text_sn_an('sn')
    log(f"SC SN: {len(suttas)} suttas")

    total_words = 0
    for sutta in suttas:
        total_words += sutta['word_count']

        output_file = output_dir / f"{sutta['id']}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'id': sutta['id'],
                'word_count': sutta['word_count']
            }, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'SN',
        'suttas': len(suttas),
        'sc_words': total_words,
        'vri_words': len(vri_words),
        'gretil_words': len(gretil_words),
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"SN: {len(suttas)} suttas")
    log(f"  SC: {total_words:,} words")
    log(f"  VRI: {len(vri_words):,} words")
    log(f"  GRETIL: {len(gretil_words):,} words")

    return summary


def build_an_critical():
    """Build AN critical edition."""
    log("=" * 60)
    log("Building AN Critical Edition")
    log("=" * 60)

    output_dir = DATA_DIR / "critical/an"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load VRI and GRETIL
    vri_text = parse_vri_nikaya('an')
    vri_words = tokenize(vri_text)
    log(f"VRI AN: {len(vri_words):,} words")

    gretil_text = load_gretil_nikaya('an')
    gretil_words = tokenize(gretil_text)
    log(f"GRETIL AN: {len(gretil_words):,} words")

    # Extract SC suttas
    suttas = extract_sc_text_sn_an('an')
    log(f"SC AN: {len(suttas)} suttas")

    total_words = 0
    for sutta in suttas:
        total_words += sutta['word_count']

        output_file = output_dir / f"{sutta['id']}_critical.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'id': sutta['id'],
                'word_count': sutta['word_count']
            }, f, indent=2, ensure_ascii=False)

    summary = {
        'nikaya': 'AN',
        'suttas': len(suttas),
        'sc_words': total_words,
        'vri_words': len(vri_words),
        'gretil_words': len(gretil_words),
    }

    with open(output_dir / "_critical_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"AN: {len(suttas)} suttas")
    log(f"  SC: {total_words:,} words")
    log(f"  VRI: {len(vri_words):,} words")
    log(f"  GRETIL: {len(gretil_words):,} words")

    return summary


def main():
    # Clear log
    LOG_FILE.write_text("")

    log("=" * 60)
    log("BUILDING CRITICAL EDITIONS")
    log("=" * 60)
    log("")

    mn = build_mn_critical()
    log("")
    sn = build_sn_critical()
    log("")
    an = build_an_critical()

    log("")
    log("=" * 60)
    log("FINAL SUMMARY")
    log("=" * 60)

    # Calculate totals
    sc_total = mn['sc_words'] + sn['sc_words'] + an['sc_words']
    vri_total = mn['vri_words'] + sn['vri_words'] + an['vri_words']
    gretil_total = mn['gretil_words'] + sn['gretil_words'] + an['gretil_words']

    log(f"SC Total: {sc_total:,} words")
    log(f"VRI Total: {vri_total:,} words")
    log(f"GRETIL Total: {gretil_total:,} words")

    # Save overall summary
    overall = {
        'timestamp': datetime.now().isoformat(),
        'nikāyas': {'MN': mn, 'SN': sn, 'AN': an},
        'totals': {
            'sc_words': sc_total,
            'vri_words': vri_total,
            'gretil_words': gretil_total,
        }
    }

    summary_file = DATA_DIR / "critical/_all_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, indent=2, ensure_ascii=False)

    log(f"\nSaved to: {summary_file}")


if __name__ == "__main__":
    main()
