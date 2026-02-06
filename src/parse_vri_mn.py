#!/usr/bin/env python3
"""
Parse VRI Majjhima Nikāya raw files into individual sutta JSON files.

VRI MN is in 3 volume files:
- s0201m.mul.txt (Mūlapaṇṇāsa, MN 1-50, vaggas 1-5)
- s0202m.mul.txt (Majjhimapaṇṇāsa, MN 51-100, vaggas 6-10)
- s0203m.mul.txt (Uparipaṇṇāsa, MN 101-152, vaggas 11-15)

Each vagga contains 10 suttas numbered 1-10 locally.
Sutta markers: "N. Namesuttaṃ" (e.g., "1. Mūlapariyāyasuttaṃ")
Vagga markers: "N. Namevaggo" (e.g., "1. Mūlapariyāyavaggo")
"""

import re
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_RAW_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed" / "mn"

# Volume files with vagga offset (vaggas 1-5, 6-10, 11-15)
VOLUMES = [
    ("s0201m.mul.txt", 0),   # Mūlapaṇṇāsa: vaggas 1-5 (offset 0)
    ("s0202m.mul.txt", 5),   # Majjhimapaṇṇāsa: vaggas 6-10 (offset 5)
    ("s0203m.mul.txt", 10),  # Uparipaṇṇāsa: vaggas 11-15 (offset 10)
]

# Pre-compiled patterns
PALI_WORD_PATTERN = re.compile(r'[a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+')
VAGGA_PATTERN = re.compile(r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶa-zāīūṭḍṇṅñṃḷ]+vaggo)\s*$', re.MULTILINE | re.IGNORECASE)
SUTTA_PATTERN = re.compile(r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶa-zāīūṭḍṇṅñṃḷ]+sutta[ṃm])\s*$', re.MULTILINE | re.IGNORECASE)
SUTTA_END_PATTERN = re.compile(r'\n[A-ZĀĪŪṬḌṆṄÑṂḶa-zāīūṭḍṇṅñṃḷ]+sutta[ṃm]\s+niṭṭhita[ṃm].*$', re.IGNORECASE)
VAGGA_END_PATTERN = re.compile(r'\n[A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo\s+(niṭṭhito|paṭhamo|dutiyo)', re.IGNORECASE)


def count_words(text: str) -> int:
    """Count Pāli words in text."""
    return len(PALI_WORD_PATTERN.findall(text))


def parse_volume(filename: str, vagga_offset: int) -> dict:
    """Parse a VRI volume file into individual suttas.

    Args:
        filename: VRI raw file name
        vagga_offset: Number of vaggas before this volume (0, 5, or 10)

    Returns:
        Dict mapping absolute sutta number to sutta data
    """
    filepath = VRI_RAW_DIR / filename

    if not filepath.exists():
        print(f"  Warning: {filename} not found")
        return {}

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Find all vagga markers to track vagga boundaries
    vagga_matches = list(VAGGA_PATTERN.finditer(content))

    # Find all sutta markers
    sutta_matches = list(SUTTA_PATTERN.finditer(content))

    if not sutta_matches:
        print(f"  Warning: No sutta markers found in {filename}")
        return {}

    print(f"  Found {len(vagga_matches)} vagga markers, {len(sutta_matches)} sutta markers")

    # Build vagga position map: position -> vagga_num (1-indexed within volume)
    vagga_positions = [(m.start(), int(m.group(1))) for m in vagga_matches]

    suttas = {}

    for i, match in enumerate(sutta_matches):
        local_sutta_num = int(match.group(1))  # 1-10 within vagga
        sutta_name = match.group(2)
        match_pos = match.start()

        # Find which vagga this sutta belongs to
        current_vagga = 1  # Default to first vagga
        for vpos, vnum in vagga_positions:
            if vpos < match_pos:
                current_vagga = vnum
            else:
                break

        # Calculate absolute sutta number
        # vagga_offset: vaggas before this volume (0, 5, 10)
        # current_vagga: vagga number within volume (1-5)
        # local_sutta_num: sutta number within vagga (usually 1-10)
        absolute_vagga = vagga_offset + current_vagga
        absolute_sutta = (absolute_vagga - 1) * 10 + local_sutta_num

        # Handle Uparipaṇṇāsa special case (MN 101-152 has 52 suttas, not 50)
        # Vagga 4 (Vibhaṅgavaggo) has 12 suttas instead of 10
        if vagga_offset == 10:
            # Uparipaṇṇāsa structure:
            # Vagga 1-3: 10 suttas each (MN 101-130)
            # Vagga 4: 12 suttas (MN 131-142)
            # Vagga 5: 10 suttas (MN 143-152)
            if current_vagga <= 3:
                absolute_sutta = 100 + (current_vagga - 1) * 10 + local_sutta_num
            elif current_vagga == 4:
                absolute_sutta = 130 + local_sutta_num  # MN 131-142
            else:  # current_vagga == 5
                absolute_sutta = 142 + local_sutta_num  # MN 143-152

        # Extract text from this match to the next sutta (or end of file)
        start_pos = match.end()
        if i + 1 < len(sutta_matches):
            end_pos = sutta_matches[i + 1].start()
        else:
            end_pos = len(content)

        sutta_text = content[start_pos:end_pos].strip()

        # Remove the ending marker (e.g., "Namesuttaṃ niṭṭhitaṃ...")
        end_marker = SUTTA_END_PATTERN.search(sutta_text)
        if end_marker:
            sutta_text = sutta_text[:end_marker.start()].strip()

        # Remove vagga summaries and other trailing metadata
        vagga_marker = VAGGA_END_PATTERN.search(sutta_text)
        if vagga_marker:
            sutta_text = sutta_text[:vagga_marker.start()].strip()

        suttas[absolute_sutta] = {
            'id': f'mn{absolute_sutta}',
            'title': sutta_name,
            'text': sutta_text,
            'word_count': count_words(sutta_text)
        }

    return suttas


def main():
    print("=" * 60)
    print("Parsing VRI Majjhima Nikāya")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = {}

    for filename, vagga_offset in VOLUMES:
        print(f"\nProcessing {filename}...")
        suttas = parse_volume(filename, vagga_offset)
        all_suttas.update(suttas)

    print(f"\nTotal suttas parsed: {len(all_suttas)}")

    # Check for missing suttas
    expected = set(range(1, 153))
    found = set(all_suttas.keys())
    missing = expected - found
    if missing:
        print(f"  Missing suttas: {sorted(missing)}")

    # Save individual sutta files
    total_words = 0
    for sutta_num in sorted(all_suttas.keys()):
        sutta = all_suttas[sutta_num]
        output_file = OUTPUT_DIR / f"mn{sutta_num}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

        total_words += sutta['word_count']

    # Save summary
    summary = {
        'collection': 'mn',
        'name': 'Majjhima Nikāya',
        'source': 'VRI CST',
        'sutta_count': len(all_suttas),
        'total_words': total_words,
        'suttas': {f'mn{n}': all_suttas[n]['word_count'] for n in sorted(all_suttas.keys())}
    }

    with open(OUTPUT_DIR / '_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSummary:")
    print(f"  Suttas: {len(all_suttas)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
