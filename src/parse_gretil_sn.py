#!/usr/bin/env python3
"""
Parse GRETIL SN (Saṃyutta Nikāya) PTS edition files into individual sutta JSON files.

GRETIL SN structure:
- 5 volumes corresponding to 5 vaggas
- References like SN_1.1,1.1 = division.book,chapter.section
- division = vagga number (1-5)
- book = saṃyutta within vagga (local numbering)

Mapping to standard SN numbering:
- Vol 1 (Sagāthāvagga): SN_1.1-11 → SN 1-11
- Vol 2 (Nidānavagga): SN_2.1-10 → SN 12-21
- Vol 3 (Khandhavagga): SN_3.1-13 → SN 22-34
- Vol 4 (Saḷāyatanavagga): SN_4.1-10 → SN 35-44
- Vol 5 (Mahāvagga): SN_5.1-12 → SN 45-56
"""

import re
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed" / "sn"

# Pre-compiled patterns
# Volume 1 format A: SN_1.1,1.1. Title => division.book,chapter.section
SUTTA_REF_PATTERN_V1A = re.compile(
    r'<b>\s*SN_(\d+)\.(\d+),(\d+)\.(\d+)\.\s*([^<]+)</b>',
    re.IGNORECASE
)
# Volume 1 format B (no chapter): SN_1.5.1. Title => division.book.section (used by SN 5, 8-10)
SUTTA_REF_PATTERN_V1B = re.compile(
    r'<b>\s*SN_(\d+)\.(\d+)\.(\d+)\.\s*([^<]+)</b>',
    re.IGNORECASE
)
# Volume 2+ format: SN_2,12(1).1 (1) Title => division,globalSN(localBook).suttaNum (num) Title
# Note: Some files have control characters before the reference
# Note: Volume 5 has extra period: SN_5,45(1).1. vs SN_4,35(1).1
# Note: The (num) after sutta number is optional for some saṃyuttas
SUTTA_REF_PATTERN_V2 = re.compile(
    r'<b>[\s\x00-\x1f]*SN_(\d+),(\d+)\((\d+)\)\.(\d+)\.?\s*(?:\([^)]*\)\s*)?([^<]+)</b>',
    re.IGNORECASE
)
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Volume configuration: (filename, division_num, global_offset)
VOLUMES = [
    ("sn_vol1.html", 1, 0),    # Sagāthāvagga: local 1-11 → SN 1-11
    ("sn_vol2.html", 2, 11),   # Nidānavagga: local 1-10 → SN 12-21
    ("sn_vol3.html", 3, 21),   # Khandhavagga: local 1-13 → SN 22-34
    ("sn_vol4.html", 4, 34),   # Saḷāyatanavagga: local 1-10 → SN 35-44
    ("sn_vol5.html", 5, 44),   # Mahāvagga: local 1-12 → SN 45-56
]


def clean_html(text: str) -> str:
    """Remove HTML tags and clean text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Convert HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_volume(filepath: Path, division: int, samyutta_offset: int) -> list[dict]:
    """Parse a GRETIL SN volume file into individual suttas.

    Args:
        filepath: Path to the GRETIL HTML file
        division: Division number (1-5)
        samyutta_offset: Offset to convert local saṃyutta to global
    """
    text = filepath.read_text(encoding='utf-8')

    # Collect matches from all patterns
    matches_v1a = list(SUTTA_REF_PATTERN_V1A.finditer(text))
    matches_v1b = list(SUTTA_REF_PATTERN_V1B.finditer(text))
    matches_v2 = list(SUTTA_REF_PATTERN_V2.finditer(text))

    # Combine all matches with their format type, sorted by position
    all_matches = []
    for m in matches_v1a:
        all_matches.append((m.start(), 'v1a', m))
    for m in matches_v1b:
        all_matches.append((m.start(), 'v1b', m))
    for m in matches_v2:
        all_matches.append((m.start(), 'v2', m))
    all_matches.sort(key=lambda x: x[0])

    if not all_matches:
        print(f"    Warning: No sutta references found in {filepath.name}")
        return []

    results = []
    sutta_counts = {}  # Track sutta numbers per global saṃyutta

    for i, (pos, fmt, match) in enumerate(all_matches):
        if fmt == 'v1a':
            # Volume 1 format A: SN_1.1,1.1 => division.localBook,chapter.section
            div = int(match.group(1))
            book = int(match.group(2))  # Local saṃyutta number
            chapter = int(match.group(3))
            section = int(match.group(4))
            title = match.group(5).strip()
            global_samyutta = book + samyutta_offset
            pts_ref = f"SN_{div}.{book},{chapter}.{section}"
        elif fmt == 'v1b':
            # Volume 1 format B (no chapter): SN_1.5.1 => division.localBook.section
            div = int(match.group(1))
            book = int(match.group(2))  # Local saṃyutta number
            section = int(match.group(3))
            title = match.group(4).strip()
            global_samyutta = book + samyutta_offset
            pts_ref = f"SN_{div}.{book}.{section}"
        else:  # v2
            # Volume 2+: SN_2,12(1).1 => division,globalSN(localBook).suttaNum
            div = int(match.group(1))
            global_sn = int(match.group(2))  # Already global!
            local_book = int(match.group(3))
            section = int(match.group(4))
            title = match.group(5).strip()
            global_samyutta = global_sn  # Already global
            pts_ref = f"SN_{div},{global_sn}({local_book}).{section}"

        # Clean up title (remove trailing punctuation, numbers)
        title = re.sub(r'[\d\s.]+$', '', title).strip()

        # Initialize counter for this saṃyutta
        if global_samyutta not in sutta_counts:
            sutta_counts[global_samyutta] = 0

        sutta_counts[global_samyutta] += 1
        sutta_num = sutta_counts[global_samyutta]

        # Build sutta ID
        sutta_id = f"sn{global_samyutta}.{sutta_num}"

        # Find content (from this marker to next marker)
        content_start = match.end()
        if i + 1 < len(all_matches):
            content_end = all_matches[i + 1][0]
        else:
            content_end = len(text)

        raw_text = text[content_start:content_end]
        cleaned_text = clean_html(raw_text)

        # Count words
        words = PALI_WORD_PATTERN.findall(cleaned_text)

        results.append({
            'id': sutta_id,
            'samyutta': global_samyutta,
            'title': title,
            'pts_ref': pts_ref,
            'text': cleaned_text,
            'word_count': len(words),
        })

    return results


def main():
    print("=" * 60)
    print("Parsing GRETIL Saṃyutta Nikāya (PTS edition)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = []
    samyutta_counts = {}

    for filename, division, offset in VOLUMES:
        filepath = GRETIL_DIR / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found")
            continue

        print(f"\nProcessing {filename} (division={division}, offset={offset})...")
        suttas = parse_volume(filepath, division, offset)

        # Track counts by saṃyutta
        for s in suttas:
            sam = s['samyutta']
            samyutta_counts[sam] = samyutta_counts.get(sam, 0) + 1

        all_suttas.extend(suttas)
        print(f"  Found {len(suttas)} suttas")

    # Save individual sutta files
    for sutta in all_suttas:
        safe_id = sutta['id'].replace('.', '_')
        output_file = OUTPUT_DIR / f"{safe_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

    # Calculate totals
    total_words = sum(s['word_count'] for s in all_suttas)

    # Save summary
    summary = {
        'source': 'GRETIL PTS SN Edition',
        'suttas': len(all_suttas),
        'samyuttas': len(samyutta_counts),
        'total_words': total_words,
        'samyutta_counts': samyutta_counts,
    }

    with open(OUTPUT_DIR / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print(f"Summary:")
    print(f"  Suttas: {len(all_suttas)}")
    print(f"  Saṃyuttas: {len(samyutta_counts)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
