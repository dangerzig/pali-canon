#!/usr/bin/env python3
"""
Parse VRI (Vipassana Research Institute) Chaṭṭha Saṅgāyana text files.

VRI format:
- Plain text with proper Unicode
- Section numbers: "1 .", "2 .", etc.
- Sutta titles: "1. Brahmajālasuttaṃ"
- Section headers: "Cūḷasīlaṃ", "Majjhimasīlaṃ"

Files:
- s0101m.mul.txt = DN Sīlakkhandhavagga (DN 1-13)
- s0102m.mul.txt = DN Mahāvagga (DN 14-23)
- s0103m.mul.txt = DN Pāthikavagga (DN 24-34)
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
VRI_DIR = DATA_DIR / "vri-raw"
OUTPUT_DIR = DATA_DIR / "vri-parsed"


# DN sutta names for matching
DN_SUTTA_NAMES = {
    1: "Brahmajālasutta",
    2: "Sāmaññaphalasutta",
    3: "Ambaṭṭhasutta",
    4: "Soṇadaṇḍasutta",
    5: "Kūṭadantasutta",
    6: "Mahālisutta",
    7: "Jāliyasutta",
    8: "Mahāsīhanādasutta",  # Also called Kassapa-sīhanāda
    9: "Poṭṭhapādasutta",
    10: "Subhasutta",
    11: "Kevaṭṭasutta",  # Also Kevaddha
    12: "Lohiccasutta",
    13: "Tevijjasutta",
    14: "Mahāpadānasutta",
    15: "Mahānidānasutta",
    16: "Mahāparinibbānasutta",
    17: "Mahāsudassanasutta",
    18: "Janavasabhasutta",
    19: "Mahāgovindasutta",
    20: "Mahāsamayasutta",
    21: "Sakkapañhasutta",
    22: "Mahāsatipaṭṭhānasutta",
    23: "Pāyāsisutta",
    24: "Pāṭikasutta",  # Also Pāthika
    25: "Udumbarikasutta",  # Also Udumbarika-sīhanāda
    26: "Cakkavattisutta",  # Also Cakkavatti-sīhanāda
    27: "Aggaññasutta",
    28: "Sampasādanīyasutta",
    29: "Pāsādikasutta",
    30: "Lakkhaṇasutta",
    31: "Siṅgālasutta",  # Also Siṅgālovāda
    32: "Āṭānāṭiyasutta",
    33: "Saṅgītisutta",
    34: "Dasuttarasutta",
}


def find_sutta_boundaries(text: str) -> list:
    """Find sutta title markers in VRI text."""
    boundaries = []

    # Pattern: number followed by sutta name ending in 'suttaṃ' or 'sutta'
    # e.g., "1. Brahmajālasuttaṃ" or "14. Mahāpadānasuttaṃ"
    pattern = r'^(\d+)\.\s+([A-ZĀĪŪṬḌṆṄÑṂḶ][a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+sutta[ṃm]?)\s*$'

    for match in re.finditer(pattern, text, re.MULTILINE):
        sutta_num = int(match.group(1))
        name = match.group(2)
        boundaries.append({
            'pos': match.start(),
            'end': match.end(),
            'sutta_num': sutta_num,
            'name': name
        })

    return boundaries


def extract_section_numbers(text: str) -> list:
    """Extract section numbers from VRI text."""
    sections = []

    # Pattern: "N ." at start of line (VRI style)
    pattern = r'^(\d+)\s+\.\s+'

    for match in re.finditer(pattern, text, re.MULTILINE):
        sections.append({
            'num': int(match.group(1)),
            'pos': match.start()
        })

    return sections


def clean_vri_text(text: str) -> str:
    """Clean VRI text."""
    # Remove BOM
    text = text.lstrip('\ufeff')

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def parse_vri_file(file_path: Path) -> dict:
    """Parse a VRI mūla text file."""
    print(f"Parsing {file_path.name}...")

    text = file_path.read_text(encoding='utf-8')
    text = clean_vri_text(text)

    # Find sutta boundaries
    boundaries = find_sutta_boundaries(text)
    sections = extract_section_numbers(text)

    print(f"  Found {len(boundaries)} sutta boundaries")
    print(f"  Found {len(sections)} section markers")

    return {
        'file': file_path.name,
        'text': text,
        'text_length': len(text),
        'sutta_boundaries': boundaries,
        'section_markers': sections
    }


def extract_sutta(file_data: dict, sutta_num: int) -> Optional[dict]:
    """Extract a single sutta from parsed file data."""
    boundaries = file_data['sutta_boundaries']

    sutta_start = None
    sutta_end = None
    sutta_name = None

    for i, b in enumerate(boundaries):
        if b['sutta_num'] == sutta_num:
            sutta_start = b['pos']
            sutta_name = b['name']
            # Find end
            if i + 1 < len(boundaries):
                sutta_end = boundaries[i + 1]['pos']
            break

    if sutta_start is None:
        return None

    if sutta_end is None:
        sutta_end = len(file_data['text'])

    # Extract text
    sutta_text = file_data['text'][sutta_start:sutta_end].strip()

    # Get sections within this sutta
    sections = []
    for s in file_data['section_markers']:
        if sutta_start <= s['pos'] < sutta_end:
            # Adjust position relative to sutta start
            sections.append({
                'num': s['num'],
                'pos': s['pos'] - sutta_start
            })

    return {
        'sutta': sutta_num,
        'name': sutta_name,
        'text': sutta_text,
        'sections': sections,
        'word_count': len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', sutta_text.lower()))
    }


def main():
    print("=" * 70)
    print("Parsing VRI DN Files")
    print("=" * 70)
    print()

    # Ensure output directory exists
    dn_output = OUTPUT_DIR / "dn"
    dn_output.mkdir(parents=True, exist_ok=True)

    # VRI DN files - note: VRI uses local numbering within each file
    # File (local_range, global_offset) - global_sutta = local_num + offset
    vri_files = {
        # s0101m: local 1-13 = DN 1-13 (offset 0)
        (1, 13, 0): VRI_DIR / "s0101m.mul.txt",
        # s0102m: local 1-10 = DN 14-23 (offset 13)
        (1, 10, 13): VRI_DIR / "s0102m.mul.txt",
        # s0103m: local 1-11 = DN 24-34 (offset 23)
        (1, 11, 23): VRI_DIR / "s0103m.mul.txt",
    }

    # Parse all files
    file_data = {}
    for (local_start, local_end, offset), path in vri_files.items():
        if path.exists():
            file_data[(local_start, local_end, offset)] = parse_vri_file(path)
        else:
            print(f"Warning: {path} not found")

    print()
    print("Extracting suttas...")

    results = []
    for sutta_num in range(1, 35):
        # Find which file contains this sutta (global sutta number)
        for (local_start, local_end, offset), data in file_data.items():
            global_start = local_start + offset
            global_end = local_end + offset
            if global_start <= sutta_num <= global_end:
                # Convert global sutta number to local number for extraction
                local_sutta_num = sutta_num - offset
                sutta = extract_sutta(data, local_sutta_num)
                if sutta:
                    # Update sutta number in result to global
                    sutta['sutta'] = sutta_num
                    print(f"  DN {sutta_num:2d}: {sutta['word_count']:>6,} words, "
                          f"{len(sutta['sections'])} sections")

                    # Save
                    output_file = dn_output / f"dn{sutta_num}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(sutta, f, indent=2, ensure_ascii=False)

                    results.append({
                        'sutta': sutta_num,
                        'name': sutta['name'],
                        'words': sutta['word_count'],
                        'sections': len(sutta['sections'])
                    })
                else:
                    print(f"  DN {sutta_num:2d}: Not found in {data['file']}")
                break

    # Save summary
    summary_file = dn_output / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'VRI Chaṭṭha Saṅgāyana',
            'suttas': results,
            'total_words': sum(r['words'] for r in results)
        }, f, indent=2, ensure_ascii=False)

    print()
    print(f"Total: {sum(r['words'] for r in results):,} words across {len(results)} suttas")
    print(f"Output saved to: {dn_output}")


if __name__ == "__main__":
    main()
