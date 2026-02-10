#!/usr/bin/env python3
"""
Parse SuttaCentral bilara-data Vinaya and Abhidhamma root texts.

Reads segmented JSON files from the bilara-data repository and
concatenates them into continuous texts matching GRETIL divisions.

SC Vinaya structure -> GRETIL mapping:
  pli-tv-bu-vb (bhikkhu vibhanga)  -> suttavibhanga1 (pj, ss, ay, np)
                                    + suttavibhanga2 (pc, pd, sk, as)
  pli-tv-bi-vb (bhikkhuni vibhanga) -> appended to respective sections
  pli-tv-kd1-10                     -> mahavagga
  pli-tv-kd11-22                    -> cullavagga
  pli-tv-pvr                        -> parivara

SC Abhidhamma structure -> GRETIL mapping:
  ds/   -> dhammasangani
  vb/   -> vibhanga
  dt/   -> dhatukatha
  pp/   -> puggalapannatti
  kv/   -> kathavatthu
  ya/   -> yamaka1, yamaka2
  patthana/ -> patthana1, patthana2, patthana3, patthana_duka
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BILARA_DIR = DATA_DIR / "bilara-data" / "root" / "pli" / "ms"
OUTPUT_DIR = DATA_DIR / "sc-parsed"


def load_bilara_file(filepath: Path) -> str:
    """Load a bilara JSON file and return concatenated text."""
    data = json.loads(filepath.read_text(encoding='utf-8'))
    # Strip HTML tags from values, concatenate
    parts = []
    for key, value in data.items():
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', value).strip()
        if text and text != '{}':
            parts.append(text)
    return ' '.join(parts)


def load_bilara_dir(dirpath: Path, pattern: str = '*_root-pli-ms.json') -> str:
    """Load all bilara files in a directory (sorted) and concatenate."""
    files = sorted(dirpath.glob(pattern))
    texts = []
    for f in files:
        text = load_bilara_file(f)
        if text:
            texts.append(text)
    return ' '.join(texts)


def load_bilara_tree(dirpath: Path) -> str:
    """Recursively load all bilara files under a directory tree."""
    texts = []
    # First load files directly in this directory
    for f in sorted(dirpath.glob('*_root-pli-ms.json')):
        text = load_bilara_file(f)
        if text:
            texts.append(text)
    # Then recurse into subdirectories
    for subdir in sorted(d for d in dirpath.iterdir() if d.is_dir()):
        text = load_bilara_tree(subdir)
        if text:
            texts.append(text)
    return ' '.join(texts)


def save_text(output_dir: Path, name: str, title: str, text: str,
              collection: str) -> dict:
    """Save parsed text to JSON file."""
    word_count = len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', text, re.IGNORECASE))
    data = {
        'collection': collection,
        'name': name,
        'title': title,
        'text': text,
        'word_count': word_count,
        'source': 'SC (SuttaCentral Mahāsaṅgīti)',
    }
    output_file = output_dir / f"{name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def parse_vinaya():
    """Parse SC Vinaya Pitaka into GRETIL-compatible divisions."""
    print("\n" + "=" * 60)
    print("SC VINAYA PITAKA")
    print("=" * 60)

    vin_dir = BILARA_DIR / "vinaya"
    output_dir = OUTPUT_DIR / "vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    # Suttavibhanga 1: Bhikkhu Parajika + Sanghadisesa + Aniyata + Nissaggiya
    # + Bhikkhuni Parajika + Sanghadisesa
    sv1_parts = []
    bu_vb = vin_dir / "pli-tv-bu-vb"
    for subdir_name in ['pli-tv-bu-vb-pj', 'pli-tv-bu-vb-ss',
                        'pli-tv-bu-vb-ay', 'pli-tv-bu-vb-np']:
        subdir = bu_vb / subdir_name
        if subdir.is_dir():
            sv1_parts.append(load_bilara_tree(subdir))
        elif (bu_vb / f"{subdir_name}_root-pli-ms.json").exists():
            sv1_parts.append(load_bilara_file(
                bu_vb / f"{subdir_name}_root-pli-ms.json"))

    # Also include bhikkhuni pj and ss in suttavibhanga1
    bi_vb = vin_dir / "pli-tv-bi-vb"
    for subdir_name in ['pli-tv-bi-vb-pj', 'pli-tv-bi-vb-ss']:
        subdir = bi_vb / subdir_name
        if subdir.is_dir():
            sv1_parts.append(load_bilara_tree(subdir))

    # Bhikkhu Patimokkha
    bu_pm = vin_dir / "pli-tv-bu-pm_root-pli-ms.json"
    if bu_pm.exists():
        sv1_parts.insert(0, load_bilara_file(bu_pm))

    sv1_text = ' '.join(p for p in sv1_parts if p)
    data = save_text(output_dir, 'suttavibhanga1',
                     'Suttavibhaṅga I (Pārājika)', sv1_text, 'vinaya')
    print(f"  {data['title']}: {data['word_count']:,} words")
    results.append(data)
    total_words += data['word_count']

    # Suttavibhanga 2: Bhikkhu Pacittiya + Patidesaniya + Sekhiya + As
    # + Bhikkhuni equivalents
    sv2_parts = []
    for subdir_name in ['pli-tv-bu-vb-pc', 'pli-tv-bu-vb-pd',
                        'pli-tv-bu-vb-sk']:
        subdir = bu_vb / subdir_name
        if subdir.is_dir():
            sv2_parts.append(load_bilara_tree(subdir))
    # Adhikarana-samatha (top-level file)
    as_file = bu_vb / "pli-tv-bu-vb-as1-7_root-pli-ms.json"
    if as_file.exists():
        sv2_parts.append(load_bilara_file(as_file))

    # Bhikkhuni sections
    for subdir_name in ['pli-tv-bi-vb-np', 'pli-tv-bi-vb-pc',
                        'pli-tv-bi-vb-pd', 'pli-tv-bi-vb-sk']:
        subdir = bi_vb / subdir_name
        if subdir.is_dir():
            sv2_parts.append(load_bilara_tree(subdir))
    bi_as = bi_vb / "pli-tv-bi-vb-as1-7_root-pli-ms.json"
    if bi_as.exists():
        sv2_parts.append(load_bilara_file(bi_as))

    # Bhikkhuni Patimokkha
    bi_pm = vin_dir / "pli-tv-bi-pm_root-pli-ms.json"
    if bi_pm.exists():
        sv2_parts.insert(0, load_bilara_file(bi_pm))

    sv2_text = ' '.join(p for p in sv2_parts if p)
    data = save_text(output_dir, 'suttavibhanga2',
                     'Suttavibhaṅga II (Pācittiya)', sv2_text, 'vinaya')
    print(f"  {data['title']}: {data['word_count']:,} words")
    results.append(data)
    total_words += data['word_count']

    # Mahavagga: kd1-10
    kd_dir = vin_dir / "pli-tv-kd"
    mv_parts = []
    for i in range(1, 11):
        kd_file = kd_dir / f"pli-tv-kd{i}_root-pli-ms.json"
        if kd_file.exists():
            mv_parts.append(load_bilara_file(kd_file))
    mv_text = ' '.join(p for p in mv_parts if p)
    data = save_text(output_dir, 'mahavagga', 'Mahāvagga', mv_text, 'vinaya')
    print(f"  {data['title']}: {data['word_count']:,} words")
    results.append(data)
    total_words += data['word_count']

    # Cullavagga: kd11-22
    cv_parts = []
    for i in range(11, 23):
        kd_file = kd_dir / f"pli-tv-kd{i}_root-pli-ms.json"
        if kd_file.exists():
            cv_parts.append(load_bilara_file(kd_file))
    cv_text = ' '.join(p for p in cv_parts if p)
    data = save_text(output_dir, 'cullavagga', 'Cūḷavagga', cv_text, 'vinaya')
    print(f"  {data['title']}: {data['word_count']:,} words")
    results.append(data)
    total_words += data['word_count']

    # Parivara
    pvr_dir = vin_dir / "pli-tv-pvr"
    pvr_text = load_bilara_tree(pvr_dir)
    data = save_text(output_dir, 'parivara', 'Parivāra', pvr_text, 'vinaya')
    print(f"  {data['title']}: {data['word_count']:,} words")
    results.append(data)
    total_words += data['word_count']

    summary = {
        'pitaka': 'Vinaya',
        'source': 'SC (SuttaCentral)',
        'texts': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def parse_abhidhamma():
    """Parse SC Abhidhamma Pitaka into GRETIL-compatible divisions."""
    print("\n" + "=" * 60)
    print("SC ABHIDHAMMA PITAKA")
    print("=" * 60)

    abh_dir = BILARA_DIR / "abhidhamma"
    output_dir = OUTPUT_DIR / "abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    # Simple one-to-one mappings
    simple_maps = [
        ('ds', 'dhammasangani', 'Dhammasaṅgaṇī'),
        ('vb', 'vibhanga', 'Vibhaṅga'),
        ('dt', 'dhatukatha', 'Dhātukathā'),
        ('pp', 'puggalapannatti', 'Puggalapaññatti'),
        ('kv', 'kathavatthu', 'Kathāvatthu'),
    ]

    for sc_dir, gretil_name, title in simple_maps:
        dirpath = abh_dir / sc_dir
        if dirpath.is_dir():
            text = load_bilara_tree(dirpath)
            data = save_text(output_dir, gretil_name, title, text,
                             'abhidhamma')
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    # Yamaka: split into yamaka1 (ya1-ya5) and yamaka2 (ya6-ya10)
    ya_dir = abh_dir / "ya"
    if ya_dir.is_dir():
        ya1_parts = []
        ya2_parts = []
        for subdir in sorted(ya_dir.iterdir()):
            if not subdir.is_dir():
                continue
            # Extract number from directory name (ya1, ya2, etc.)
            m = re.search(r'ya(\d+)', subdir.name)
            if m:
                num = int(m.group(1))
                text = load_bilara_tree(subdir)
                if num <= 5:
                    ya1_parts.append(text)
                else:
                    ya2_parts.append(text)

        ya1_text = ' '.join(p for p in ya1_parts if p)
        data = save_text(output_dir, 'yamaka1', 'Yamaka I', ya1_text,
                         'abhidhamma')
        print(f"  Yamaka I: {data['word_count']:,} words")
        results.append(data)
        total_words += data['word_count']

        ya2_text = ' '.join(p for p in ya2_parts if p)
        data = save_text(output_dir, 'yamaka2', 'Yamaka II', ya2_text,
                         'abhidhamma')
        print(f"  Yamaka II: {data['word_count']:,} words")
        results.append(data)
        total_words += data['word_count']

    # Patthana: multiple volumes
    # GRETIL has patthana1 (tika), patthana2, patthana3, patthana_duka
    # SC has patthana1-24 directories
    # We'll concatenate all into a single text for now, since the mapping
    # between SC's 24 paccayas and GRETIL's volume splits is complex
    pat_dir = abh_dir / "patthana"
    if pat_dir.is_dir():
        pat_text = load_bilara_tree(pat_dir)
        data = save_text(output_dir, 'patthana', 'Paṭṭhāna', pat_text,
                         'abhidhamma')
        print(f"  Paṭṭhāna: {data['word_count']:,} words")
        results.append(data)
        total_words += data['word_count']

    summary = {
        'pitaka': 'Abhidhamma',
        'source': 'SC (SuttaCentral)',
        'texts': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def main():
    import sys
    print("=" * 60)
    print("PARSING SC (SUTTACENTRAL) VINAYA & ABHIDHAMMA")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {
        'vinaya', 'abhidhamma'}

    results = {}
    if 'vinaya' in targets:
        results['vinaya'] = parse_vinaya()
    if 'abhidhamma' in targets:
        results['abhidhamma'] = parse_abhidhamma()

    total = sum(r.get('total_words', 0) for r in results.values())
    print(f"\nGrand total: {total:,} words")
    return results


if __name__ == "__main__":
    main()
