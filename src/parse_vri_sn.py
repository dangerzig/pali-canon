#!/usr/bin/env python3
"""
Parse VRI SN (Saṃyutta Nikāya) files into individual sutta JSON files.

VRI SN structure:
- 5 volumes (s0301m-s0305m)
- 56 saṃyuttas organized by vagga
- ~2,889 suttas with IDs like sn1.1, sn1.2, etc.

Each volume uses LOCAL numbering (1, 2, 3...) for saṃyuttas, which must be
converted to GLOBAL numbering using volume offsets.
"""

import re
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed" / "sn"

# Pre-compiled patterns - more flexible to handle trailing whitespace
SAMYUTTA_PATTERN = re.compile(
    r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+saṃyuttaṃ)\s*$',
    re.MULTILINE
)
VAGGA_PATTERN = re.compile(r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo)\s*$', re.MULTILINE)
# Individual sutta: "1. Namesuttaṃ"
SUTTA_TITLE_PATTERN = re.compile(r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+suttaṃ)\s*$', re.MULTILINE)
# Grouped suttas (peyyāla): "1-12. Namesuttadvādasakaṃ" or "1-10. Namesuttadasakaṃ" etc.
GROUPED_SUTTA_PATTERN = re.compile(
    r'^(\d+)-(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+sutta[a-zāīūṭḍṇṅñṃḷ]*)\s*$',
    re.MULTILINE
)
SUTTA_START_PATTERN = re.compile(r'^(\d+)\s+\.\s+', re.MULTILINE)
# Grouped content start: "651-662 ." for ranges
GROUPED_START_PATTERN = re.compile(r'^(\d+)-(\d+)\s+\.\s+', re.MULTILINE)
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Volume configuration: (filename, global_offset)
# Local saṃyutta number + offset = Global saṃyutta number
VOLUMES = [
    ("s0301m.mul.txt", 0),   # Sagāthāvagga: local 1-11 → SN 1-11
    ("s0302m.mul.txt", 11),  # Nidānavagga: local 1-10 → SN 12-21
    ("s0303m.mul.txt", 21),  # Khandhavagga: local 1-13 → SN 22-34
    ("s0304m.mul.txt", 34),  # Saḷāyatanavagga: local 1-10 → SN 35-44
    ("s0305m.mul.txt", 44),  # Mahāvagga: local 1-12 → SN 45-56
]


def parse_volume(filepath: Path, samyutta_offset: int = 0) -> list[dict]:
    """Parse a VRI SN volume file into individual suttas.

    Args:
        filepath: Path to the VRI volume file
        samyutta_offset: Offset to add to local saṃyutta numbers to get global numbers

    Handles both individual suttas ("1. Namesuttaṃ") and grouped/peyyāla suttas
    ("1-12. Namesuttadvādasakaṃ") which are common in SN's repetitive sections.
    """
    text = filepath.read_text(encoding='utf-8')

    # Find all structural markers
    samyutta_matches = list(SAMYUTTA_PATTERN.finditer(text))
    individual_matches = list(SUTTA_TITLE_PATTERN.finditer(text))
    grouped_matches = list(GROUPED_SUTTA_PATTERN.finditer(text))
    sutta_start_matches = list(SUTTA_START_PATTERN.finditer(text))
    grouped_start_matches = list(GROUPED_START_PATTERN.finditer(text))

    # Combine individual and grouped matches, sorted by position
    # Each entry: (position, type, match)
    all_sutta_matches = []
    for m in individual_matches:
        all_sutta_matches.append((m.start(), 'individual', m))
    for m in grouped_matches:
        all_sutta_matches.append((m.start(), 'grouped', m))
    all_sutta_matches.sort(key=lambda x: x[0])

    results = []
    current_samyutta_local = 0
    current_samyutta_global = 0
    current_samyutta_name = ""

    # Track sutta number within each saṃyutta (using global numbers)
    sutta_counts = {}  # global_samyutta_num -> count

    # Process each sutta (individual or grouped)
    for i, (title_pos, match_type, title_match) in enumerate(all_sutta_matches):
        if match_type == 'individual':
            sutta_num_in_vagga = int(title_match.group(1))
            sutta_title = title_match.group(2)
            sutta_range = None
        else:  # grouped
            sutta_num_start = int(title_match.group(1))
            sutta_num_end = int(title_match.group(2))
            sutta_num_in_vagga = sutta_num_start
            sutta_title = title_match.group(3)
            sutta_range = (sutta_num_start, sutta_num_end)

        # Determine which saṃyutta this belongs to
        for sm in samyutta_matches:
            if sm.start() < title_pos:
                current_samyutta_local = int(sm.group(1))
                current_samyutta_global = current_samyutta_local + samyutta_offset
                current_samyutta_name = sm.group(2)
            else:
                break

        # Initialize counter for this saṃyutta
        if current_samyutta_global not in sutta_counts:
            sutta_counts[current_samyutta_global] = 0

        sutta_counts[current_samyutta_global] += 1
        sutta_num_in_samyutta = sutta_counts[current_samyutta_global]

        # Build sutta ID (e.g., sn1.1, sn12.23)
        # For grouped suttas, use the starting number in the ID
        sutta_id = f"sn{current_samyutta_global}.{sutta_num_in_samyutta}"

        # Find the content start
        content_start = None
        if match_type == 'grouped':
            # Look for grouped start pattern "N-M . "
            for start_match in grouped_start_matches:
                if start_match.start() > title_pos:
                    content_start = start_match.end()
                    break
        if content_start is None:
            # Fall back to individual pattern "N . "
            for start_match in sutta_start_matches:
                if start_match.start() > title_pos:
                    if int(start_match.group(1)) == sutta_num_in_vagga:
                        content_start = start_match.end()
                        break

        if content_start is None:
            content_start = title_match.end()

        # Find the end (next sutta title or next saṃyutta or end of text)
        content_end = len(text)

        # Check for next sutta (individual or grouped)
        if i + 1 < len(all_sutta_matches):
            content_end = min(content_end, all_sutta_matches[i + 1][0])

        # Check for next saṃyutta
        for sm in samyutta_matches:
            if sm.start() > title_pos and sm.start() < content_end:
                content_end = sm.start()
                break

        # Extract and clean text
        raw_text = text[content_start:content_end]
        cleaned_text = clean_text(raw_text)

        # Count words
        words = PALI_WORD_PATTERN.findall(cleaned_text)

        result = {
            'id': sutta_id,
            'samyutta': current_samyutta_global,
            'samyutta_name': current_samyutta_name,
            'title': sutta_title,
            'text': cleaned_text,
            'word_count': len(words),
        }
        if sutta_range:
            result['sutta_range'] = sutta_range
            result['sutta_count'] = sutta_range[1] - sutta_range[0] + 1

        results.append(result)

    return results


def clean_text(text: str) -> str:
    """Clean VRI text."""
    # Remove section numbers like "1 . " at start
    text = re.sub(r'^\d+\s+\.\s+', '', text)

    # Remove vagga end markers
    text = re.sub(r'^[A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo.*$', '', text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)

    return text.strip()


def main():
    print("=" * 60)
    print("Parsing VRI Saṃyutta Nikāya")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = []
    samyutta_counts = {}

    for filename, offset in VOLUMES:
        filepath = VRI_DIR / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found")
            continue

        print(f"\nProcessing {filename} (offset={offset})...")
        suttas = parse_volume(filepath, samyutta_offset=offset)

        # Track counts by saṃyutta
        for s in suttas:
            sam = s['samyutta']
            samyutta_counts[sam] = samyutta_counts.get(sam, 0) + 1

        all_suttas.extend(suttas)
        print(f"  Found {len(suttas)} suttas")

    # Save individual sutta files
    for sutta in all_suttas:
        # Convert sn1.1 to sn1_1 for filename
        safe_id = sutta['id'].replace('.', '_')
        output_file = OUTPUT_DIR / f"{safe_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

    # Summary
    print()
    print(f"Total suttas parsed: {len(all_suttas)}")
    print(f"Saṃyuttas found: {len(samyutta_counts)}")

    # Show breakdown
    total_words = sum(s['word_count'] for s in all_suttas)

    # Save summary
    summary = {
        'source': 'VRI CST SN Edition',
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
