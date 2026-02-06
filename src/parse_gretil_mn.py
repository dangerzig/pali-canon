#!/usr/bin/env python3
"""
Parse GRETIL MN HTML files into individual sutta JSON files.

GRETIL MN format:
- Three volume files: mn_vol1.html (MN 1-76), mn_vol2.html (MN 77-106), mn_vol3.html (MN 107-152)
- Sutta markers vary by volume:
  - Vol 1: % VAGGA.SUTTA SUTTANAME. (ABSOLUTE_NUM) PAGE%
  - Vols 2-3: <i>VAGGA.SUTTA SUTTANAME (ABSOLUTE_NUM) PAGE</i>
"""

import re
import json
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed" / "mn"

# Pre-compiled patterns
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Volume to sutta range mapping: (filename, start_sutta, end_sutta)
VOLUMES = [
    ("mn_vol1.html", 1, 76),
    ("mn_vol2.html", 77, 106),
    ("mn_vol3.html", 107, 152),
]


class TextExtractor(HTMLParser):
    """Extract text from GRETIL HTML preserving structure markers."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_body = False
        self.skip_tags = {'script', 'style', 'head'}
        self.current_skip = None
        self.in_italic = False

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        elif tag in self.skip_tags:
            self.current_skip = tag
        elif tag == 'br' and self.in_body and not self.current_skip:
            self.text_parts.append('\n')
        elif tag == 'i' and self.in_body:
            self.in_italic = True
            self.text_parts.append('<<<ITALIC>>>')

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        elif tag == self.current_skip:
            self.current_skip = None
        elif tag == 'i' and self.in_italic:
            self.in_italic = False
            self.text_parts.append('<<</ITALIC>>>')

    def handle_data(self, data):
        if self.in_body and not self.current_skip:
            self.text_parts.append(data)

    def get_text(self):
        return ''.join(self.text_parts)


def extract_text_from_html(filepath):
    """Extract text from HTML file with italic markers preserved."""
    html = filepath.read_text(encoding='utf-8', errors='ignore')
    parser = TextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        # Fallback: simple regex-based extraction
        text = re.sub(r'<[^>]+>', '\n', html)
        return text


def find_sutta_info_from_html(filepath):
    """Extract sutta numbers and titles from raw HTML."""
    html = filepath.read_text(encoding='utf-8', errors='ignore')

    sutta_info = {}  # sutta_num -> title

    # Pattern for sutta markers with number in parentheses
    # Matches both % markers and <i> markers
    # Note: some numbers have trailing periods like (115.) or (114.)
    # Note: some titles end with SUTTAM instead of SUTTAṂ
    pattern = re.compile(r'(?:%|<i>)[^<%]*?([A-ZĀĪŪṬḌṆṄÑṂḶ][A-ZĀĪŪṬḌṆṄÑṂḶA-zāīūṭḍṇṅñṃḷ{}\d\- ]*SUTTA[MṂ])[^<%]*?\((\d+)\.?\)')

    for match in pattern.finditer(html):
        title = match.group(1)
        sutta_num = int(match.group(2))

        if sutta_num not in sutta_info:
            # Clean up title (remove braces and trailing numbers)
            title = re.sub(r'[{}\d]', '', title)
            sutta_info[sutta_num] = title

    return sutta_info


def find_sutta_boundaries(text, sutta_info, start_sutta, end_sutta):
    """Find where each sutta starts in the extracted text."""
    boundaries = []  # list of (sutta_num, title, position)

    # Sort suttas by number
    sorted_suttas = sorted(
        [(num, title) for num, title in sutta_info.items()
         if start_sutta <= num <= end_sutta],
        key=lambda x: x[0]
    )

    for sutta_num, title in sorted_suttas:
        # Search for the sutta marker pattern in text
        # Try multiple patterns since formatting varies
        patterns = [
            # Volume 1 style: %...TITLE...%
            rf'%[^%]*{re.escape(title)}[^%]*\({sutta_num}\.?\)[^%]*%',
            # Volume 2-3 style: <<<ITALIC>>>...TITLE...<</ITALIC>>>
            rf'<<<ITALIC>>>[^<]*{re.escape(title)}[^<]*\({sutta_num}\.?\)[^<]*<<</ITALIC>>>',
            # Just the title followed by number (with optional period)
            rf'{re.escape(title)}[^\n]*\({sutta_num}\.?\)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                boundaries.append((sutta_num, title, match.start()))
                break
        else:
            # If no pattern matches, try just looking for (N) near the title
            simple_pattern = rf'\({sutta_num}\.?\)'
            for match in re.finditer(simple_pattern, text):
                # Check if the title appears near this position
                context_start = max(0, match.start() - 200)
                context = text[context_start:match.end()]
                if title[:10] in context:  # First 10 chars of title
                    boundaries.append((sutta_num, title, context_start))
                    break

    # Sort by position
    boundaries.sort(key=lambda x: x[2])
    return boundaries


def clean_sutta_text(text):
    """Clean extracted sutta text."""
    # Remove % header markers
    text = re.sub(r'%[^%]*%', '', text)

    # Remove italic markers and their content (page headers)
    text = re.sub(r'<<<ITALIC>>>[^<]*<<</ITALIC>>>', '', text)

    # Remove [page NNN] markers
    text = re.sub(r'\[page\s+\d+\]', '', text)

    # Remove PTS reference markers like [M. i. 1. 5
    text = re.sub(r'\[M\.\s*[ivx]+\.\s*\d+\.\s*\d+', '', text)

    # Remove content straddling notices
    text = re.sub(r'\[.*?content straddling.*?\]', '', text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)

    return text.strip()


def extract_suttas_from_volume(filepath, start_sutta, end_sutta):
    """Extract individual suttas from a volume file."""
    print(f"Processing {filepath.name}...")

    # Get sutta info from raw HTML
    sutta_info = find_sutta_info_from_html(filepath)

    # Get text with markers
    text = extract_text_from_html(filepath)

    # Find boundaries
    boundaries = find_sutta_boundaries(text, sutta_info, start_sutta, end_sutta)

    print(f"  Found {len(boundaries)} sutta boundaries")

    results = []
    for i, (sutta_num, title, start_pos) in enumerate(boundaries):
        # End position is start of next sutta or end of text
        if i + 1 < len(boundaries):
            end_pos = boundaries[i + 1][2]
        else:
            end_pos = len(text)

        # Extract and clean text
        raw_text = text[start_pos:end_pos]
        cleaned_text = clean_sutta_text(raw_text)

        # Count words
        words = PALI_WORD_PATTERN.findall(cleaned_text)

        results.append({
            'id': f"mn{sutta_num}",
            'sutta_num': sutta_num,
            'title': title,
            'text': cleaned_text,
            'word_count': len(words),
        })

    return results


def main():
    print("=" * 60)
    print("Parsing GRETIL MN into individual suttas")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = []
    total_words = 0

    for filename, start, end in VOLUMES:
        filepath = GRETIL_DIR / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found")
            continue

        suttas = extract_suttas_from_volume(filepath, start, end)
        all_suttas.extend(suttas)

        vol_words = sum(s['word_count'] for s in suttas)
        total_words += vol_words
        print(f"  Extracted {len(suttas)} suttas, {vol_words:,} words")

    # Save individual sutta files
    for sutta in all_suttas:
        output_file = OUTPUT_DIR / f"mn{sutta['sutta_num']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

    # Check for missing suttas
    found_nums = {s['sutta_num'] for s in all_suttas}
    missing = [i for i in range(1, 153) if i not in found_nums]

    print()
    print(f"Total suttas parsed: {len(all_suttas)}")
    if missing:
        print(f"  Missing suttas: {missing}")

    # Save summary
    summary = {
        'source': 'GRETIL PTS MN Edition',
        'suttas': len(all_suttas),
        'total_words': total_words,
        'missing': missing,
    }

    with open(OUTPUT_DIR / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print(f"Summary:")
    print(f"  Suttas: {len(all_suttas)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
