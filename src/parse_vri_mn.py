#!/usr/bin/env python3
"""
Parse VRI Majjhima Nikāya raw files into individual sutta JSON files.

VRI MN is in 3 volume files:
- s0201m.mul.txt (Mūlapaṇṇāsa, MN 1-50)
- s0202m.mul.txt (Majjhimapaṇṇāsa, MN 51-100)
- s0203m.mul.txt (Uparipaṇṇāsa, MN 101-152)

Each sutta is marked by:
- Start: "N. Namesuttaṃ" (e.g., "1. Mūlapariyāyasuttaṃ")
- End: "Namesuttaṃ niṭṭhitaṃ Nth." (e.g., "Mūlapariyāyasuttaṃ niṭṭhitaṃ paṭhamaṃ.")
"""

import re
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_RAW_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed" / "mn"

# Volume files and their sutta ranges
VOLUMES = [
    ("s0201m.mul.txt", 1, 50),    # Mūlapaṇṇāsa
    ("s0202m.mul.txt", 51, 100),  # Majjhimapaṇṇāsa
    ("s0203m.mul.txt", 101, 152), # Uparipaṇṇāsa
]


def count_words(text: str) -> int:
    """Count Pāli words in text."""
    words = re.findall(r'[a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+', text)
    return len(words)


def parse_volume(filename: str, start_sutta: int, end_sutta: int) -> dict:
    """Parse a VRI volume file into individual suttas."""
    filepath = VRI_RAW_DIR / filename

    if not filepath.exists():
        print(f"  Warning: {filename} not found")
        return {}

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    suttas = {}

    # Pattern for sutta start: "N. Namesuttaṃ" at start of line
    # The number resets in each volume, so we track absolute sutta number
    sutta_start_pattern = re.compile(
        r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶa-zāīūṭḍṇṅñṃḷ]+sutta[ṃm])\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    # Find all sutta starts
    matches = list(sutta_start_pattern.finditer(content))

    if not matches:
        print(f"  Warning: No sutta markers found in {filename}")
        return {}

    print(f"  Found {len(matches)} sutta markers in {filename}")

    for i, match in enumerate(matches):
        local_num = int(match.group(1))
        sutta_name = match.group(2)

        # Calculate absolute sutta number
        # In Mūlapaṇṇāsa, local 1 = MN 1
        # In Majjhimapaṇṇāsa, local 1 = MN 51
        # In Uparipaṇṇāsa, local 1 = MN 101
        if start_sutta == 1:
            absolute_num = local_num
        elif start_sutta == 51:
            absolute_num = 50 + local_num
        else:  # start_sutta == 101
            absolute_num = 100 + local_num

        if absolute_num < start_sutta or absolute_num > end_sutta:
            continue

        # Extract text from this match to the next (or end)
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)

        sutta_text = content[start_pos:end_pos].strip()

        # Remove the ending marker (e.g., "Namesuttaṃ niṭṭhitaṃ...")
        end_marker = re.search(
            r'\n[A-ZĀĪŪṬḌṆṄÑṂḶa-zāīūṭḍṇṅñṃḷ]+sutta[ṃm]\s+niṭṭhita[ṃm].*$',
            sutta_text,
            re.IGNORECASE
        )
        if end_marker:
            sutta_text = sutta_text[:end_marker.start()].strip()

        # Also remove vagga summaries and other trailing metadata
        vagga_marker = re.search(r'\n[A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo\s+(niṭṭhito|paṭhamo|dutiyo)', sutta_text, re.IGNORECASE)
        if vagga_marker:
            sutta_text = sutta_text[:vagga_marker.start()].strip()

        suttas[absolute_num] = {
            'id': f'mn{absolute_num}',
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

    for filename, start, end in VOLUMES:
        print(f"\nProcessing {filename} (MN {start}-{end})...")
        suttas = parse_volume(filename, start, end)
        all_suttas.update(suttas)

    print(f"\nTotal suttas parsed: {len(all_suttas)}")

    # Save individual sutta files
    total_words = 0
    for sutta_num in sorted(all_suttas.keys()):
        sutta = all_suttas[sutta_num]
        output_file = OUTPUT_DIR / f"mn{sutta_num}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

        total_words += sutta['word_count']
        print(f"  mn{sutta_num}: {sutta['word_count']:,} words")

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
