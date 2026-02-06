#!/usr/bin/env python3
"""
Parse VRI AN (Aṅguttara Nikāya) files into individual sutta JSON files.

VRI AN structure (available data):
- Nipāta 1 (Ekakanipāta): s0401m.mul.txt
- Nipāta 2 (Dukanipāta): s0402m1-3.mul.txt
- Nipāta 3 (Tikanipāta): s0403m1-3.mul.txt
- Nipāta 4 (Catukkanipāta): s0404m1-4.mul.txt

Note: Nipātas 5-11 are not available in the VRI raw data.

Suttas are numbered: AN {nipāta}.{sutta_number}
e.g., AN 1.1, AN 2.1, AN 3.1, etc.
"""

import re
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed" / "an"

# Pre-compiled patterns
NIPATA_PATTERN = re.compile(
    r'^([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+nipātapāḷi)\s*$',
    re.MULTILINE
)
VAGGA_PATTERN = re.compile(
    r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo)\s*$',
    re.MULTILINE
)
# Sutta start: "N . " at the beginning of a line
SUTTA_START_PATTERN = re.compile(r'^(\d+)\s+\.\s+', re.MULTILINE)
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)

# Nipāta name to number mapping
NIPATA_MAP = {
    'ekakanipātapāḷi': 1,
    'dukanipātapāḷi': 2,
    'tikanipātapāḷi': 3,
    'catukkanipātapāḷi': 4,
    'pañcakanipātapāḷi': 5,
    'chakkanipātapāḷi': 6,
    'sattakanipātapāḷi': 7,
    'aṭṭhakanipātapāḷi': 8,
    'navakanipātapāḷi': 9,
    'dasakanipātapāḷi': 10,
    'ekādasakanipātapāḷi': 11,
}

# Volume files configuration: (files, nipāta_number)
VOLUMES = [
    (["s0401m.mul.txt"], 1),
    (["s0402m1.mul.txt", "s0402m2.mul.txt", "s0402m3.mul.txt"], 2),
    (["s0403m1.mul.txt", "s0403m2.mul.txt", "s0403m3.mul.txt"], 3),
    (["s0404m1.mul.txt", "s0404m2.mul.txt", "s0404m3.mul.txt", "s0404m4.mul.txt"], 4),
]


def clean_text(text: str) -> str:
    """Clean VRI text."""
    # Remove section numbers like "1 . " at start
    text = re.sub(r'^\d+\s+\.\s+', '', text)
    # Remove vagga markers
    text = re.sub(r'^[A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷ]+vaggo.*$', '', text, flags=re.MULTILINE)
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    return text.strip()


def parse_volume_files(filepaths: list, nipata: int) -> list[dict]:
    """Parse VRI AN volume files for a single nipāta into individual suttas.

    Args:
        filepaths: List of file paths for this nipāta
        nipata: Nipāta number (1-11)
    """
    # Concatenate all files for this nipāta
    full_text = ""
    for filepath in filepaths:
        if filepath.exists():
            full_text += filepath.read_text(encoding='utf-8') + "\n"

    if not full_text:
        return []

    # Find all sutta starts
    sutta_matches = list(SUTTA_START_PATTERN.finditer(full_text))

    if not sutta_matches:
        return []

    results = []
    sutta_count = 0

    for i, match in enumerate(sutta_matches):
        sutta_num_local = int(match.group(1))
        content_start = match.end()

        # Find end (next sutta or end of text)
        if i + 1 < len(sutta_matches):
            content_end = sutta_matches[i + 1].start()
        else:
            content_end = len(full_text)

        # Extract and clean text
        raw_text = full_text[content_start:content_end]
        cleaned_text = clean_text(raw_text)

        # Skip if too short (likely a vagga summary)
        words = PALI_WORD_PATTERN.findall(cleaned_text)
        if len(words) < 5:
            continue

        sutta_count += 1
        sutta_id = f"an{nipata}.{sutta_count}"

        results.append({
            'id': sutta_id,
            'nipata': nipata,
            'local_num': sutta_num_local,
            'text': cleaned_text,
            'word_count': len(words),
        })

    return results


def main():
    print("=" * 60)
    print("Parsing VRI Aṅguttara Nikāya")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_suttas = []
    nipata_counts = {}

    for files, nipata in VOLUMES:
        filepaths = [VRI_DIR / f for f in files]
        existing = [f for f in filepaths if f.exists()]

        if not existing:
            print(f"\n  Warning: No files found for nipāta {nipata}")
            continue

        print(f"\nProcessing nipāta {nipata} ({len(existing)} files)...")
        suttas = parse_volume_files(existing, nipata)

        nipata_counts[nipata] = len(suttas)
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
        'source': 'VRI CST AN Edition (partial)',
        'suttas': len(all_suttas),
        'nipatas': len(nipata_counts),
        'nipatas_available': list(nipata_counts.keys()),
        'nipatas_missing': [n for n in range(1, 12) if n not in nipata_counts],
        'total_words': total_words,
        'nipata_counts': nipata_counts,
    }

    with open(OUTPUT_DIR / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print(f"Summary:")
    print(f"  Suttas: {len(all_suttas)}")
    print(f"  Nipātas: {len(nipata_counts)} (1-{max(nipata_counts.keys()) if nipata_counts else 0})")
    print(f"  Total words: {total_words:,}")
    print(f"  Output: {OUTPUT_DIR}")
    if summary['nipatas_missing']:
        print(f"  Note: Nipātas {summary['nipatas_missing']} not available in VRI raw data")


if __name__ == "__main__":
    main()
