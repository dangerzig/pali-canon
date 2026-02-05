#!/usr/bin/env python3
"""
Parse complete VRI (Vipassana Research Institute) Chaṭṭha Saṅgāyana texts.

Handles the entire Tipitaka:
- Vinaya Pitaka (vin*.mul.txt)
- Sutta Pitaka (s01*-s05*.mul.txt)
- Abhidhamma Pitaka (abh*.mul.txt)
"""

import re
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed"


def clean_vri_text(text: str) -> str:
    """Clean VRI text."""
    text = text.lstrip('\ufeff')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_vri_file(file_path: Path) -> dict:
    """Parse a VRI mūla text file."""
    if not file_path.exists():
        return None

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    text = clean_vri_text(text)

    word_count = len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', text.lower()))

    return {
        'file': file_path.name,
        'text': text,
        'word_count': word_count,
    }


def parse_vinaya():
    """Parse Vinaya Pitaka VRI files."""
    print("\n" + "=" * 60)
    print("VINAYA PITAKA (VRI)")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    # VRI Vinaya files
    files = {
        'patimokkha': 'vin01m.mul.txt',
        'suttavibhanga1': 'vin02m1.mul.txt',
        'suttavibhanga2': 'vin02m4.mul.txt',  # vin02m2 and vin02m3 are empty
        'mahavagga': None,  # Need to find correct file
        'cullavagga': None,
        'parivara': None,
    }

    # Find all vinaya mūla files
    vin_files = sorted(VRI_DIR.glob("vin*.mul.txt"))

    results = []
    total_words = 0

    for vf in vin_files:
        if vf.stat().st_size == 0:
            continue

        data = parse_vri_file(vf)
        if data and data['word_count'] > 0:
            output_file = output_dir / f"{vf.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {vf.name}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    summary = {
        'pitaka': 'Vinaya',
        'source': 'VRI CST',
        'files': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def parse_sutta_nikaya(code: str, name: str, file_pattern: str):
    """Parse a Sutta Nikaya collection."""
    print(f"\n{name}:")

    output_dir = OUTPUT_DIR / code.lower()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(VRI_DIR.glob(f"{file_pattern}*.mul.txt"))

    results = []
    total_words = 0

    for sf in files:
        if sf.stat().st_size == 0:
            continue

        data = parse_vri_file(sf)
        if data and data['word_count'] > 0:
            output_file = output_dir / f"{sf.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {sf.name}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    summary = {
        'nikaya': name,
        'source': 'VRI CST',
        'files': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_khuddaka():
    """Parse Khuddaka Nikaya VRI files."""
    print("\n" + "=" * 60)
    print("KHUDDAKA NIKAYA (VRI)")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "kn"
    output_dir.mkdir(parents=True, exist_ok=True)

    # KN files are s05XX
    files = sorted(VRI_DIR.glob("s05*.mul.txt"))

    results = []
    total_words = 0

    for kf in files:
        if kf.stat().st_size == 0:
            continue

        data = parse_vri_file(kf)
        if data and data['word_count'] > 0:
            output_file = output_dir / f"{kf.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {kf.name}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    summary = {
        'nikaya': 'Khuddaka',
        'source': 'VRI CST',
        'files': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def parse_abhidhamma():
    """Parse Abhidhamma Pitaka VRI files."""
    print("\n" + "=" * 60)
    print("ABHIDHAMMA PITAKA (VRI)")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Abhidhamma files are abh*.mul.txt
    files = sorted(VRI_DIR.glob("abh*.mul.txt"))

    results = []
    total_words = 0

    for af in files:
        if af.stat().st_size == 0:
            continue

        data = parse_vri_file(af)
        if data and data['word_count'] > 0:
            output_file = output_dir / f"{af.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {af.name}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    summary = {
        'pitaka': 'Abhidhamma',
        'source': 'VRI CST',
        'files': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def main():
    print("=" * 60)
    print("PARSING COMPLETE VRI TIPITAKA")
    print("=" * 60)

    results = {}

    # Vinaya Pitaka
    results['vinaya'] = parse_vinaya()

    # Sutta Pitaka
    print("\n" + "=" * 60)
    print("SUTTA PITAKA (VRI)")
    print("=" * 60)

    results['dn'] = parse_sutta_nikaya('dn', 'Dīgha Nikāya', 's010')
    results['mn'] = parse_sutta_nikaya('mn', 'Majjhima Nikāya', 's020')
    results['sn'] = parse_sutta_nikaya('sn', 'Saṃyutta Nikāya', 's030')
    results['an'] = parse_sutta_nikaya('an', 'Aṅguttara Nikāya', 's040')
    results['kn'] = parse_khuddaka()

    # Abhidhamma Pitaka
    results['abhidhamma'] = parse_abhidhamma()

    # Calculate totals
    sutta_words = sum(results[k].get('total_words', 0) for k in ['dn', 'mn', 'sn', 'an', 'kn'])

    total_words = (
        results['vinaya'].get('total_words', 0) +
        sutta_words +
        results['abhidhamma'].get('total_words', 0)
    )

    # Save overall summary
    print("\n" + "=" * 60)
    print("COMPLETE VRI TIPITAKA SUMMARY")
    print("=" * 60)

    summary = {
        'source': 'VRI Chaṭṭha Saṅgāyana (CST4)',
        'vinaya_pitaka': results['vinaya'],
        'sutta_pitaka': {
            'dn': results['dn'],
            'mn': results['mn'],
            'sn': results['sn'],
            'an': results['an'],
            'kn': results['kn'],
            'total_words': sutta_words,
        },
        'abhidhamma_pitaka': results['abhidhamma'],
        'total_words': total_words,
    }

    with open(OUTPUT_DIR / "_vri_complete_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nVinaya Piṭaka:     {results['vinaya'].get('total_words', 0):>10,} words")
    print(f"Sutta Piṭaka:      {sutta_words:>10,} words")
    print(f"  - DN:            {results['dn'].get('total_words', 0):>10,} words")
    print(f"  - MN:            {results['mn'].get('total_words', 0):>10,} words")
    print(f"  - SN:            {results['sn'].get('total_words', 0):>10,} words")
    print(f"  - AN:            {results['an'].get('total_words', 0):>10,} words")
    print(f"  - KN:            {results['kn'].get('total_words', 0):>10,} words")
    print(f"Abhidhamma Piṭaka: {results['abhidhamma'].get('total_words', 0):>10,} words")
    print(f"{'─' * 35}")
    print(f"TOTAL TIPITAKA:    {total_words:>10,} words")

    return summary


if __name__ == "__main__":
    main()
