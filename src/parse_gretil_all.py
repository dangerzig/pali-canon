#!/usr/bin/env python3
"""
Parse GRETIL PTS editions for all nikāyas (MN, SN, AN).
DN parser already exists separately.

Outputs JSON files with extracted text for each sutta.
"""

import re
import json
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"


class TextExtractor(HTMLParser):
    """Extract plain text from GRETIL HTML."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False

    def handle_data(self, data):
        if self.in_body:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)


def extract_text_from_html(html_content):
    """Extract plain text from HTML."""
    parser = TextExtractor()
    parser.feed(html_content)
    text = parser.get_text()

    # Clean up
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def parse_mn():
    """Parse Majjhima Nikāya GRETIL files."""
    print("Parsing MN...")
    output_dir = DATA_DIR / "gretil-parsed/mn"
    output_dir.mkdir(parents=True, exist_ok=True)

    # MN sutta ranges by volume
    # Vol 1: MN 1-76, Vol 2: MN 77-106, Vol 3: MN 107-152
    vol_ranges = {
        1: (1, 76),
        2: (77, 106),
        3: (107, 152),
    }

    results = []

    for vol in range(1, 4):
        vol_file = GRETIL_DIR / f"mn_vol{vol}.html"
        if not vol_file.exists():
            print(f"  Vol {vol}: File not found")
            continue

        html = vol_file.read_text(encoding='utf-8', errors='ignore')
        text = extract_text_from_html(html)

        # For now, save entire volume as single file
        # More sophisticated sutta splitting would require pattern matching
        start, end = vol_ranges[vol]

        output_file = output_dir / f"mn_vol{vol}.json"
        data = {
            'volume': vol,
            'suttas': f"MN {start}-{end}",
            'text': text,
            'word_count': len(text.split()),
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Vol {vol}: {data['word_count']:,} words")
        results.append(data)

    # Save summary
    summary = {
        'nikaya': 'MN',
        'volumes': len(results),
        'total_words': sum(r['word_count'] for r in results),
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {summary['total_words']:,} words")
    return summary


def parse_sn():
    """Parse Saṃyutta Nikāya GRETIL files."""
    print("Parsing SN...")
    output_dir = DATA_DIR / "gretil-parsed/sn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for vol in range(1, 6):
        vol_file = GRETIL_DIR / f"sn_vol{vol}.html"
        if not vol_file.exists():
            print(f"  Vol {vol}: File not found")
            continue

        html = vol_file.read_text(encoding='utf-8', errors='ignore')
        text = extract_text_from_html(html)

        output_file = output_dir / f"sn_vol{vol}.json"
        data = {
            'volume': vol,
            'text': text,
            'word_count': len(text.split()),
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Vol {vol}: {data['word_count']:,} words")
        results.append(data)

    summary = {
        'nikaya': 'SN',
        'volumes': len(results),
        'total_words': sum(r['word_count'] for r in results),
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {summary['total_words']:,} words")
    return summary


def parse_an():
    """Parse Aṅguttara Nikāya GRETIL files."""
    print("Parsing AN...")
    output_dir = DATA_DIR / "gretil-parsed/an"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for vol in range(1, 6):
        vol_file = GRETIL_DIR / f"an_vol{vol}.html"
        if not vol_file.exists():
            print(f"  Vol {vol}: File not found")
            continue

        html = vol_file.read_text(encoding='utf-8', errors='ignore')
        text = extract_text_from_html(html)

        output_file = output_dir / f"an_vol{vol}.json"
        data = {
            'volume': vol,
            'text': text,
            'word_count': len(text.split()),
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Vol {vol}: {data['word_count']:,} words")
        results.append(data)

    summary = {
        'nikaya': 'AN',
        'volumes': len(results),
        'total_words': sum(r['word_count'] for r in results),
    }

    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {summary['total_words']:,} words")
    return summary


def main():
    print("=" * 60)
    print("Parsing GRETIL PTS Editions")
    print("=" * 60)
    print()

    mn = parse_mn()
    print()
    sn = parse_sn()
    print()
    an = parse_an()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = mn['total_words'] + sn['total_words'] + an['total_words']
    print(f"MN: {mn['total_words']:,} words")
    print(f"SN: {sn['total_words']:,} words")
    print(f"AN: {an['total_words']:,} words")
    print(f"Total (MN+SN+AN): {total:,} words")

    # Save overall summary
    overall = {
        'nikāyas': {
            'MN': mn,
            'SN': sn,
            'AN': an,
        },
        'total_words': total,
    }

    summary_file = DATA_DIR / "gretil-parsed/_gretil_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to: {summary_file}")


if __name__ == "__main__":
    main()
