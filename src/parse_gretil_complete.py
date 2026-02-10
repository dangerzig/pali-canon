#!/usr/bin/env python3
"""
Parse complete GRETIL PTS editions for the entire Tipitaka.

Handles:
- Vinaya Pitaka (5 volumes)
- Sutta Pitaka: DN, MN, SN, AN, KN
- Abhidhamma Pitaka (7 books)

Outputs JSON files with extracted text.
"""

import re
import json
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed"


class TextExtractor(HTMLParser):
    """Extract plain text from GRETIL HTML."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = False
        self.skip_tags = {'script', 'style', 'head'}
        self.current_skip = None

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        elif tag in self.skip_tags:
            self.current_skip = tag

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        elif tag == self.current_skip:
            self.current_skip = None

    def handle_data(self, data):
        if self.in_body and not self.current_skip:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)


def extract_text_from_html(html_content):
    """Extract plain text from HTML."""
    parser = TextExtractor()
    try:
        parser.feed(html_content)
    except Exception:
        # Fallback: simple regex-based extraction
        text = re.sub(r'<[^>]+>', ' ', html_content)
        return re.sub(r'\s+', ' ', text).strip()

    text = parser.get_text()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_file(filepath, collection, name):
    """Parse a single GRETIL HTML file."""
    if not filepath.exists():
        return None

    html = filepath.read_text(encoding='utf-8', errors='ignore')
    text = extract_text_from_html(html)

    return {
        'collection': collection,
        'name': name,
        'source_file': filepath.name,
        'text': text,
        'word_count': len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', text, re.IGNORECASE)),
    }


def parse_vinaya():
    """Parse Vinaya Pitaka files."""
    print("\n" + "=" * 60)
    print("VINAYA PITAKA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        'suttavibhanga1': ('vinaya_suttavibhanga1.htm', 'Suttavibhaṅga I (Pārājika)'),
        'suttavibhanga2': ('vinaya_suttavibhanga2.htm', 'Suttavibhaṅga II (Pācittiya)'),
        'mahavagga': ('vinaya_mahavagga.htm', 'Mahāvagga'),
        'cullavagga': ('vinaya_cullavagga.htm', 'Cūḷavagga'),
        'parivara': ('vinaya_parivara.htm', 'Parivāra'),
    }

    results = []
    total_words = 0

    for key, (filename, title) in files.items():
        filepath = GRETIL_DIR / filename
        data = parse_file(filepath, 'vinaya', key)

        if data:
            data['title'] = title
            output_file = output_dir / f"{key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND")

    summary = {
        'pitaka': 'Vinaya',
        'texts': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def parse_dn():
    """Parse Digha Nikaya files."""
    print("\nDN (Dīgha Nikāya):")
    output_dir = OUTPUT_DIR / "dn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for vol in range(1, 4):
        # Try both naming conventions
        for pattern in [f"dn_vol{vol}.html", f"dighn{vol}pu.htm"]:
            filepath = GRETIL_DIR / pattern
            if filepath.exists():
                data = parse_file(filepath, 'dn', f'vol{vol}')
                if data:
                    data['volume'] = vol
                    output_file = output_dir / f"dn_vol{vol}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  Vol {vol}: {data['word_count']:,} words")
                    results.append(data)
                    total_words += data['word_count']
                break

    summary = {'nikaya': 'DN', 'volumes': len(results), 'total_words': total_words}
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_mn():
    """Parse Majjhima Nikaya files."""
    print("\nMN (Majjhima Nikāya):")
    output_dir = OUTPUT_DIR / "mn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for vol in range(1, 4):
        for pattern in [f"mn_vol{vol}.html", f"majjn{vol}pu.htm"]:
            filepath = GRETIL_DIR / pattern
            if filepath.exists():
                data = parse_file(filepath, 'mn', f'vol{vol}')
                if data:
                    data['volume'] = vol
                    output_file = output_dir / f"mn_vol{vol}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  Vol {vol}: {data['word_count']:,} words")
                    results.append(data)
                    total_words += data['word_count']
                break

    summary = {'nikaya': 'MN', 'volumes': len(results), 'total_words': total_words}
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_sn():
    """Parse Samyutta Nikaya files."""
    print("\nSN (Saṃyutta Nikāya):")
    output_dir = OUTPUT_DIR / "sn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for vol in range(1, 6):
        for pattern in [f"sn_vol{vol}.html", f"samyu{vol}pu.htm"]:
            filepath = GRETIL_DIR / pattern
            if filepath.exists():
                data = parse_file(filepath, 'sn', f'vol{vol}')
                if data:
                    data['volume'] = vol
                    output_file = output_dir / f"sn_vol{vol}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  Vol {vol}: {data['word_count']:,} words")
                    results.append(data)
                    total_words += data['word_count']
                break

    summary = {'nikaya': 'SN', 'volumes': len(results), 'total_words': total_words}
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_an():
    """Parse Anguttara Nikaya files."""
    print("\nAN (Aṅguttara Nikāya):")
    output_dir = OUTPUT_DIR / "an"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for vol in range(1, 6):
        for pattern in [f"an_vol{vol}.html", f"angut{vol}pu.htm"]:
            filepath = GRETIL_DIR / pattern
            if filepath.exists():
                data = parse_file(filepath, 'an', f'vol{vol}')
                if data:
                    data['volume'] = vol
                    output_file = output_dir / f"an_vol{vol}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  Vol {vol}: {data['word_count']:,} words")
                    results.append(data)
                    total_words += data['word_count']
                break

    summary = {'nikaya': 'AN', 'volumes': len(results), 'total_words': total_words}
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_kn():
    """Parse Khuddaka Nikaya files."""
    print("\n" + "=" * 60)
    print("KHUDDAKA NIKAYA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "kn"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map of files to parse
    files = {
        'khuddakapatha': ('kn_khuddakapatha.htm', 'Khuddakapāṭha'),
        'dhammapada': ('kn_dhammapada.htm', 'Dhammapada'),
        'udana': ('kn_udana.htm', 'Udāna'),
        'itivuttaka': ('itivutpu.htm', 'Itivuttaka'),
        'suttanipata': ('kn_suttanipata.htm', 'Suttanipāta'),
        'vimanavatthu': ('kn_vimanavatthu.htm', 'Vimānavatthu'),
        'petavatthu': ('kn_petavatthu.htm', 'Petavatthu'),
        'theragatha': ('theragpu.htm', 'Theragāthā'),
        'therigatha': ('therigpu.htm', 'Therīgāthā'),
        'jataka1': ('jatak1pu.htm', 'Jātaka Vol 1'),
        'jataka2': ('jatak2pu.htm', 'Jātaka Vol 2'),
        'jataka3': ('jatak3pu.htm', 'Jātaka Vol 3'),
        'jataka4': ('jatak4pu.htm', 'Jātaka Vol 4'),
        'jataka5': ('jatak5pu.htm', 'Jātaka Vol 5'),
        'jataka6': ('jatak6pu.htm', 'Jātaka Vol 6'),
        'mahaniddesa': ('nidde1pu.htm', 'Mahāniddesa'),
        'cullaniddesa': ('nidde2pu.htm', 'Cūḷaniddesa'),
        'patisambhidamagga1': ('patis1pu.htm', 'Paṭisambhidāmagga Vol 1'),
        'patisambhidamagga2': ('patis2pu.htm', 'Paṭisambhidāmagga Vol 2'),
        'apadana': ('kn_apadana.htm', 'Apadāna'),
        'buddhavamsa': ('kn_buddhavamsa.htm', 'Buddhavaṃsa'),
        'cariyapitaka': ('kn_cariyapitaka.htm', 'Cariyāpiṭaka'),
    }

    results = []
    total_words = 0

    for key, (filename, title) in files.items():
        filepath = GRETIL_DIR / filename
        data = parse_file(filepath, 'kn', key)

        if data:
            data['title'] = title
            output_file = output_dir / f"{key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND ({filename})")

    summary = {
        'nikaya': 'Khuddaka',
        'texts': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def parse_abhidhamma():
    """Parse Abhidhamma Pitaka files."""
    print("\n" + "=" * 60)
    print("ABHIDHAMMA PITAKA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        'dhammasangani': ('abhi_dhammasangani.htm', 'Dhammasaṅgaṇī'),
        'vibhanga': ('abhi_vibhanga.htm', 'Vibhaṅga'),
        'dhatukatha': ('abhi_dhatukatha.htm', 'Dhātukathā'),
        'puggalapannatti': ('abhi_puggalapannatti.htm', 'Puggalapaññatti'),
        'kathavatthu': ('abhi_kathavatthu.htm', 'Kathāvatthu'),
        'yamaka1': ('abhi_yamaka1.htm', 'Yamaka Vol 1'),
        'yamaka2': ('abhi_yamaka2.htm', 'Yamaka Vol 2'),
        'patthana1': ('abhi_patthana1.htm', 'Paṭṭhāna Vol 1'),
        'patthana2': ('abhi_patthana2.htm', 'Paṭṭhāna Vol 2'),
        'patthana3': ('abhi_patthana3.htm', 'Paṭṭhāna Vol 3'),
        'patthana_duka': ('abhi_patthana_duka.htm', 'Paṭṭhāna Duka'),
    }

    results = []
    total_words = 0

    for key, (filename, title) in files.items():
        filepath = GRETIL_DIR / filename
        data = parse_file(filepath, 'abhidhamma', key)

        if data:
            data['title'] = title
            output_file = output_dir / f"{key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND ({filename})")

    summary = {
        'pitaka': 'Abhidhamma',
        'texts': len(results),
        'total_words': total_words,
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


def main():
    print("=" * 60)
    print("PARSING COMPLETE GRETIL PTS TIPITAKA")
    print("=" * 60)

    results = {}

    # Vinaya Pitaka
    results['vinaya'] = parse_vinaya()

    # Sutta Pitaka
    print("\n" + "=" * 60)
    print("SUTTA PITAKA")
    print("=" * 60)

    results['dn'] = parse_dn()
    results['mn'] = parse_mn()
    results['sn'] = parse_sn()
    results['an'] = parse_an()
    results['kn'] = parse_kn()

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
    print("COMPLETE TIPITAKA SUMMARY")
    print("=" * 60)

    summary = {
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

    with open(OUTPUT_DIR / "_complete_summary.json", 'w', encoding='utf-8') as f:
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
    print()
    print(f"Summary saved to: {OUTPUT_DIR / '_complete_summary.json'}")

    return summary


if __name__ == "__main__":
    main()
