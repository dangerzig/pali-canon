#!/usr/bin/env python3
"""
Parse GRETIL AN (Aṅguttara Nikāya) PTS edition files into individual sutta JSON files.

GRETIL AN structure:
- 5 volumes covering 11 nipātas
- Vol 1: Eka (1), Duka (2), Tika (3) - uses <i>I. ii. 4.]</i> format
- Vol 2: Catukka (4) - uses vagga markers and sutta starts
- Vol 3: Pañcaka (5), Chakka (6)
- Vol 4: Sattaka (7), Aṭṭhaka (8), Navaka (9)
- Vol 5: Dasaka (10), Ekādasaka (11)
"""

import re
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed" / "an"

# Pre-compiled patterns
# Vol 1 reference patterns:
# Format A: <i>I. ii. 4.]</i> (nipāta.vagga.sutta) - used for nipāta 1-2
# Format B: <i>III. 6.]</i> (nipāta.sutta) - used for nipāta 3
SUTTA_REF_PATTERN_V1_3PART = re.compile(
    r'<i>\s*([IVX]+)\.\s*([ivx]+)\.\s*(\d+)\.?\]',
    re.IGNORECASE
)
SUTTA_REF_PATTERN_V1_2PART = re.compile(
    r'<i>\s*([IVX]+)\.\s*(\d+)\.?\]',
    re.IGNORECASE
)

# Sutta start pattern for vol 2-5: "1. Evaṃ me sutaṃ" or "1. Cattāro" etc.
# Must be at start of line with small number (1-20 typically starts a sutta)
SUTTA_START_PATTERN = re.compile(
    r'^\s*1\.\s+(?:Evaṃ me sutaṃ|Cattār|Catuh|Pañc|Cha[ḷy]|Satt|Aṭṭh|Nav|Dasa|Ekādasa)',
    re.MULTILINE
)

# Nipāta markers
NIPATA_PATTERN = re.compile(
    r'(EKA|DUKA|TIKA|CATUKKA|PAÑCAKA|CHAKKA|SATTAKA|AṬṬHAKA|NAVAKA|DASAKA|EKĀDASAKA)-?NIPĀTA',
    re.IGNORECASE
)

# Vagga end markers (summary lines)
VAGGA_END_PATTERN = re.compile(
    r'vaggo\s+(?:paṭhamo|dutiyo|tatiyo|catuttho|pañcamo|chaṭṭho|sattamo|aṭṭhamo|navamo|dasamo)',
    re.IGNORECASE
)

# Pali word pattern for word counting
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Roman numeral conversion
ROMAN_TO_INT = {
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
    'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
    'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20,
    'xxi': 21, 'xxii': 22, 'xxiii': 23, 'xxiv': 24, 'xxv': 25,
}

# Nipāta name to number
NIPATA_TO_NUM = {
    'eka': 1, 'duka': 2, 'tika': 3, 'catukka': 4, 'pañcaka': 5,
    'chakka': 6, 'sattaka': 7, 'aṭṭhaka': 8, 'navaka': 9,
    'dasaka': 10, 'ekādasaka': 11,
}

# Volume configuration: (filename, nipātas covered, use_v1_format)
VOLUMES = [
    ("an_vol1.html", [1, 2, 3], True),
    ("an_vol2.html", [4], False),
    ("an_vol3.html", [5, 6], False),
    ("an_vol4.html", [7, 8, 9], False),
    ("an_vol5.html", [10, 11], False),
]


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    return ROMAN_TO_INT.get(roman.lower(), 0)


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


def parse_volume_v1(filepath: Path) -> list[dict]:
    """Parse volume 1 using reference formats.

    Handles two formats:
    - 3-part: <i>I. ii. 4.]</i> (nipāta.vagga.sutta) for nipātas 1-2
    - 2-part: <i>III. 6.]</i> (nipāta.sutta) for nipāta 3
    """
    text = filepath.read_text(encoding='utf-8')

    # Collect all matches from both patterns with their positions
    all_matches = []

    # 3-part matches (nipāta.vagga.sutta)
    for match in SUTTA_REF_PATTERN_V1_3PART.finditer(text):
        nipata_roman = match.group(1)
        vagga_roman = match.group(2)
        sutta_num = int(match.group(3))
        nipata = roman_to_int(nipata_roman)
        vagga = roman_to_int(vagga_roman)
        if nipata > 0 and vagga > 0:
            all_matches.append({
                'pos': match.start(),
                'end': match.end(),
                'nipata': nipata,
                'nipata_roman': nipata_roman,
                'vagga': vagga,
                'vagga_roman': vagga_roman,
                'sutta_num': sutta_num,
            })

    # 2-part matches (nipāta.sutta) - only for nipāta 3 (III)
    for match in SUTTA_REF_PATTERN_V1_2PART.finditer(text):
        nipata_roman = match.group(1)
        sutta_num = int(match.group(2))
        nipata = roman_to_int(nipata_roman)
        # Only use 2-part for nipāta 3 (tika-nipāta)
        if nipata == 3:
            # Check this position isn't already covered by a 3-part match
            pos = match.start()
            if not any(m['pos'] == pos for m in all_matches):
                all_matches.append({
                    'pos': pos,
                    'end': match.end(),
                    'nipata': nipata,
                    'nipata_roman': nipata_roman,
                    'vagga': None,
                    'vagga_roman': None,
                    'sutta_num': sutta_num,
                })

    # Sort by position
    all_matches.sort(key=lambda m: m['pos'])

    if not all_matches:
        return []

    results = []
    sutta_counts = {}

    for i, match in enumerate(all_matches):
        nipata = match['nipata']

        if nipata not in sutta_counts:
            sutta_counts[nipata] = 0
        sutta_counts[nipata] += 1

        sutta_id = f"an{nipata}.{sutta_counts[nipata]}"

        # Build PTS reference
        if match['vagga_roman']:
            pts_ref = f"AN_{match['nipata_roman']}.{match['vagga_roman']}.{match['sutta_num']}"
        else:
            pts_ref = f"AN_{match['nipata_roman']}.{match['sutta_num']}"

        content_start = match['end']
        if i + 1 < len(all_matches):
            content_end = all_matches[i + 1]['pos']
        else:
            content_end = len(text)

        raw_text = text[content_start:content_end]
        cleaned_text = clean_html(raw_text)

        words = PALI_WORD_PATTERN.findall(cleaned_text)
        if len(words) < 5:
            sutta_counts[nipata] -= 1
            continue

        results.append({
            'id': sutta_id,
            'nipata': nipata,
            'vagga': match['vagga'],
            'sutta_in_vagga': match['sutta_num'],
            'pts_ref': pts_ref,
            'text': cleaned_text,
            'word_count': len(words),
        })

    return results


def parse_volume_v2(filepath: Path, nipatas: list[int]) -> list[dict]:
    """Parse volumes 2-5 using nipāta markers and sutta starts.

    Different nipātas use different formats:
    - Some use "1. Evaṃ me sutaṃ" to start each sutta
    - Some use Roman numeral section markers (I., II., III., etc.)
    - Some use the nipāta number word (e.g., "1. Cattāro" for catukka)
    """
    text = filepath.read_text(encoding='utf-8')

    results = []

    # Find nipāta boundaries
    nipata_matches = list(NIPATA_PATTERN.finditer(text))

    for nip_idx, nip_match in enumerate(nipata_matches):
        nipata_name = nip_match.group(1).lower()
        nipata = NIPATA_TO_NUM.get(nipata_name, 0)

        if nipata == 0 or nipata not in nipatas:
            continue

        # Find the range for this nipāta
        nip_start = nip_match.end()
        if nip_idx + 1 < len(nipata_matches):
            nip_end = nipata_matches[nip_idx + 1].start()
        else:
            nip_end = len(text)

        nipata_text = text[nip_start:nip_end]

        # Find all sutta starts in this nipāta
        sutta_starts = []

        # Method 1: Roman numeral section markers (I., II., III., etc.)
        # These appear on their own line or as section headers
        roman_pattern = re.compile(
            r'^\s*([IVXL]+)\.\s*$|'  # Just "I." on its own line
            r'(?:<BR>|<br>)\s*([IVXL]+)\.\s*(?:<BR>|<br>)',  # Between BR tags
            re.MULTILINE | re.IGNORECASE
        )
        for m in roman_pattern.finditer(nipata_text):
            sutta_starts.append(m.start())

        # Method 2: "1. Evaṃ me sutaṃ" - traditional sutta opening
        for m in re.finditer(r'^\s*1\.\s+Evaṃ me sutaṃ', nipata_text, re.MULTILINE):
            # Avoid duplicates (might already be captured by Roman numeral)
            pos = m.start()
            if not any(abs(pos - s) < 100 for s in sutta_starts):
                sutta_starts.append(pos)

        # Method 3: nipāta number word starts
        # e.g., "1. Cattāro" for catukka, "1. Pañc" for pañcaka
        nipata_word_starts = {
            4: r'Catt[aā]',
            5: r'Pañc',
            6: r'Cha[ḷy]',
            7: r'Satt',
            8: r'Aṭṭh',
            9: r'Nav',
            10: r'Dasa',
            11: r'Ekādasa',
        }

        if nipata in nipata_word_starts:
            pattern = rf'^\s*1\.\s+{nipata_word_starts[nipata]}'
            for m in re.finditer(pattern, nipata_text, re.MULTILINE):
                pos = m.start()
                if not any(abs(pos - s) < 100 for s in sutta_starts):
                    sutta_starts.append(pos)

        sutta_starts.sort()

        if not sutta_starts:
            # Fallback: split by vagga end markers
            vagga_ends = [m.end() for m in VAGGA_END_PATTERN.finditer(nipata_text)]
            if vagga_ends:
                sutta_starts = [0] + vagga_ends[:-1]

        # Extract suttas
        for i, start in enumerate(sutta_starts):
            if i + 1 < len(sutta_starts):
                end = sutta_starts[i + 1]
            else:
                end = len(nipata_text)

            raw_text = nipata_text[start:end]
            cleaned_text = clean_html(raw_text)

            words = PALI_WORD_PATTERN.findall(cleaned_text)
            if len(words) < 10:  # Skip very short entries
                continue

            sutta_num = len(results) + 1  # Will renumber later
            results.append({
                'id': f"an{nipata}.{sutta_num}",
                'nipata': nipata,
                'text': cleaned_text,
                'word_count': len(words),
            })

    return results


def main():
    print("=" * 60)
    print("Parsing GRETIL Aṅguttara Nikāya (PTS edition)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = []
    nipata_counts = {}

    for filename, nipatas, use_v1 in VOLUMES:
        filepath = GRETIL_DIR / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found")
            continue

        print(f"\nProcessing {filename} (nipātas {nipatas})...")

        if use_v1:
            suttas = parse_volume_v1(filepath)
        else:
            suttas = parse_volume_v2(filepath, nipatas)

        # Track counts by nipāta
        for s in suttas:
            nip = s['nipata']
            nipata_counts[nip] = nipata_counts.get(nip, 0) + 1

        all_suttas.extend(suttas)
        print(f"  Found {len(suttas)} suttas")

    # Renumber suttas within each nipāta for consistency
    nipata_sutta_num = {}
    for sutta in all_suttas:
        nip = sutta['nipata']
        if nip not in nipata_sutta_num:
            nipata_sutta_num[nip] = 0
        nipata_sutta_num[nip] += 1
        sutta['id'] = f"an{nip}.{nipata_sutta_num[nip]}"

    # Update nipata counts
    nipata_counts = nipata_sutta_num.copy()

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
        'source': 'GRETIL PTS AN Edition',
        'suttas': len(all_suttas),
        'nipatas': len(nipata_counts),
        'total_words': total_words,
        'nipata_counts': {str(k): v for k, v in sorted(nipata_counts.items())},
    }

    with open(OUTPUT_DIR / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print(f"Summary:")
    print(f"  Suttas: {len(all_suttas)}")
    print(f"  Nipātas: {len(nipata_counts)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Output: {OUTPUT_DIR}")
    print()
    print("Suttas per nipāta:")
    for nip in sorted(nipata_counts.keys()):
        print(f"  AN {nip}: {nipata_counts[nip]} suttas")


if __name__ == "__main__":
    main()
