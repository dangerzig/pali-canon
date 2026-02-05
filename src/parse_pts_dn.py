#!/usr/bin/env python3
"""
Parse PTS Dīgha Nikāya text files into structured format.

Extracts:
- Sutta text with PTS page references
- Section/paragraph structure
- Prepares for comparison with SuttaCentral edition

Note: The OCR'd PTS files have page headers like:
    2 BRAHMAJALA SUTTA. [D. i. 1. 2
    48 SAMAÑÑA-PHALA-SUTTA. [D. ii. 8

The printed page number at the start is the most reliable marker.
The bracketed reference often has OCR errors.
"""

import re
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
PTS_DIR = DATA_DIR / "pts-text/sutta"
OUTPUT_DIR = DATA_DIR / "pts-parsed/dn"

# PTS DN volume files
PTS_FILES = {
    1: "06-Digha-Nikaya-1-Davids-Carpenter-1890.txt",  # DN 1-13
    2: "07-Digha-Nikaya-2-Davids-Carpenter-1903.txt",  # DN 14-23
    3: "08-Digha-Nikaya-3-Carpenter-1911.txt",         # DN 24-34
}

# Map sutta names (as they appear in headers) to sutta numbers
# Headers use various spellings due to OCR and editorial choices
# Volumes 2-3 often use hyphenated forms like "MAHĀ-PADĀNA"
SUTTA_NAME_MAP = {
    # Volume 1 (DN 1-13)
    'BRAHMAJALA': 1, 'BRAHMAJĀLA': 1,
    'SAMAÑÑAPHALA': 2, 'SAMAÑÑA-PHALA': 2, 'SAMANNA-PHALA': 2, 'SĀMAÑÑAPHALA': 2,
    'AMBATTHA': 3, 'AMBAṬṬHA': 3,
    'SONADANDA': 4, 'SOṆADAṆḌA': 4,
    'KUTADANTA': 5, 'KŪṬADANTA': 5,
    'MAHALI': 6, 'MAHĀLI': 6,
    'JALIYA': 7, 'JĀLIYA': 7,
    'KASSAPA': 8, 'KASSAPA-SIHANADA': 8, 'KASSAPA SIHANADA': 8,
    'MAHĀSĪHANĀDA': 8, 'MAHASIHANADA': 8,
    'POTTHAPADA': 9, 'POṬṬHAPĀDA': 9,
    'SUBHA': 10,
    'KEVADDHA': 11, 'KEVAṬṬA': 11, 'KEVATTA': 11,
    'LOHICCA': 12,
    'TEVIJJA': 13,

    # Volume 2 (DN 14-23) - uses "SUTTANTA" and hyphenated names
    'MAHAPADANA': 14, 'MAHĀPADĀNA': 14, 'MAHÁ-PADĀNA': 14, 'MAHĀPADĀNA': 14,
    'MAHANIDANA': 15, 'MAHĀNIDĀNA': 15, 'MAHĀ-NIDĀNA': 15, 'MAHA-XIDANA': 15,  # OCR error
    'MAHAPARINIBBANA': 16, 'MAHĀPARINIBBĀNA': 16, 'MAHĀ-PARINIBBĀNA': 16,
    'MAHASUDASSANA': 17, 'MAHĀSUDASSANA': 17, 'MAHĀ-SUDASSANA': 17,
    'JANAVASABHA': 18,
    'MAHAGOVINDA': 19, 'MAHĀGOVINDA': 19, 'MAHĀ-GOVINDA': 19,
    'MAHASAMAYA': 20, 'MAHĀSAMAYA': 20, 'MAHA-SAMAYA': 20, 'MAHĀ-SAMAYA': 20,
    'SAKKAPANHA': 21, 'SAKKAPAÑHA': 21, 'SAKKA-PANHA': 21, 'SAKKA-PAÑHA': 21,
    'SAKKA-PANA': 21, 'SAKKAPANA': 21,  # OCR error (N->A)
    'MAHASATIPATTHANA': 22, 'MAHĀSATIPAṬṬHĀNA': 22, 'MAHĀ-SATIPAṬṬHĀNA': 22,
    'SATIPATTHANA': 22, 'MAHĀ-SATIPATTHĀNA': 22,
    'PAYASI': 23, 'PĀYĀSI': 23,

    # Volume 3 (DN 24-34)
    'PATIKA': 24, 'PĀṬIKA': 24, 'PÁTIKA': 24,
    'UDUMBARIKA': 25, 'UDUMBARIKA-SIHANADA': 25,
    'CAKKAVATTI': 26, 'CAKKAVATTI-SIHANADA': 26,
    'AGGANNA': 27, 'AGGAÑÑA': 27,
    'SAMPASADANIYA': 28, 'SAMPASĀDANĪYA': 28, 'SAWPASADANIYA': 28,
    'PASADIKA': 29, 'PĀSĀDIKA': 29, 'PISAPIKA': 29, 'PASADIRA': 29,  # OCR errors
    'LAKKHANA': 30, 'LAKKHAṆA': 30,
    'SINGALA': 31, 'SIṄGĀLA': 31, 'SIGALA': 31, 'SIGĀLAKA': 31, 'SINGALAKA': 31,
    'SINGALOVADA': 31, 'SINGĀLOVĀDA': 31,  # Full name variant
    'ATANATIYA': 32, 'ĀṬĀNĀṬIYA': 32,
    'SANGITI': 33, 'SAṄGĪTI': 33, 'SANGĪTI': 33, 'BANGITI': 33,  # OCR error (S->B)
    'DASUTTARA': 34,
}

# Sutta info: number -> (title, volume, start_page, end_page)
# Page numbers are PTS page numbers (D i = volume 1, D ii = volume 2, D iii = volume 3)
DN_SUTTAS = {
    1: ("Brahmajāla", 1, 1, 46),
    2: ("Sāmaññaphala", 1, 47, 86),
    3: ("Ambaṭṭha", 1, 87, 110),
    4: ("Soṇadaṇḍa", 1, 111, 126),
    5: ("Kūṭadanta", 1, 127, 149),
    6: ("Mahāli", 1, 150, 158),
    7: ("Jāliya", 1, 159, 160),      # Very short sutta
    8: ("Mahāsīhanāda", 1, 161, 177),  # Also called Kassapa-Sīhanāda
    9: ("Poṭṭhapāda", 1, 178, 203),
    10: ("Subha", 1, 204, 210),
    11: ("Kevaṭṭa", 1, 211, 223),
    12: ("Lohicca", 1, 224, 234),
    13: ("Tevijja", 1, 235, 252),
    14: ("Mahāpadāna", 2, 1, 54),
    15: ("Mahānidāna", 2, 55, 71),
    16: ("Mahāparinibbāna", 2, 72, 168),
    17: ("Mahāsudassana", 2, 169, 199),
    18: ("Janavasabha", 2, 200, 219),
    19: ("Mahāgovinda", 2, 220, 252),
    20: ("Mahāsamaya", 2, 253, 262),
    21: ("Sakkapañha", 2, 263, 289),
    22: ("Mahāsatipaṭṭhāna", 2, 290, 315),
    23: ("Pāyāsi", 2, 316, 357),
    24: ("Pāṭika", 3, 1, 35),
    25: ("Udumbarika", 3, 36, 79),
    26: ("Cakkavatti", 3, 80, 98),
    27: ("Aggañña", 3, 99, 116),
    28: ("Sampasādanīya", 3, 117, 141),
    29: ("Pāsādika", 3, 142, 179),
    30: ("Lakkhaṇa", 3, 180, 193),
    31: ("Siṅgāla", 3, 194, 206),
    32: ("Āṭānāṭiya", 3, 207, 224),
    33: ("Saṅgīti", 3, 225, 271),
    34: ("Dasuttara", 3, 272, 294),
}


def find_page_headers(content: str) -> list:
    """
    Find all page headers in the content.

    Headers look like:
        2 BRAHMAJALA SUTTA. [D. i. 1. 2
        48 SAMAÑÑA-PHALA-SUTTA. [D. ii. 8
        2 MAHAPADANA-SUTTANTA. [D. xiv. 1. 2.

    Returns list of dicts with: line_num, pos, printed_page, sutta_name, sutta_num
    """
    headers = []

    # Pattern: start of line, number, sutta name ending in SUTTA/SUTTANTA/BUTTA/BUTTANTA (OCR)
    # Using a flexible pattern to handle OCR variations
    # Volume 1 uses "SUTTA", volumes 2-3 use "SUTTANTA"
    # Note: sutta names can have spaces (e.g., "KASSAPA SIHANADA SUTTA")
    pattern = r'^(\d+)\s+([A-ZĀĪŪṬḌṆṄÑṂḶPŚ][A-ZĀĪŪṬḌṆṄÑṂḶPŚA-zāīūṭḍṇṅñṃḷ\s\-]+?)[\s\-]*(SUTTA|SUTTANTA|BUTTA|BUTTANTA|SÜTTA|SÜTTANTA)\.?\s*(?:\[D\..*)?$'

    lines = content.split('\n')
    for i, line in enumerate(lines):
        match = re.match(pattern, line.strip())
        if match:
            printed_page = int(match.group(1))
            raw_name = match.group(2).upper()

            # Try to identify the sutta
            sutta_num = identify_sutta_from_name(raw_name)

            # Calculate position in content
            pos = sum(len(l) + 1 for l in lines[:i])

            headers.append({
                'line_num': i,
                'pos': pos,
                'printed_page': printed_page,
                'sutta_name': match.group(2),
                'sutta_num': sutta_num,
                'raw_line': line.strip()
            })

    return headers


def normalize_name(name: str) -> str:
    """Normalize a sutta name for matching."""
    # Remove hyphens, spaces, and convert to uppercase
    name = name.upper().replace('-', '').replace(' ', '').strip()
    # Normalize diacritics
    replacements = [
        ('Ā', 'A'), ('Ī', 'I'), ('Ū', 'U'),
        ('Ṭ', 'T'), ('Ḍ', 'D'), ('Ṇ', 'N'),
        ('Ṅ', 'N'), ('Ñ', 'N'), ('Ṃ', 'M'),
        ('Ḷ', 'L'), ('Á', 'A'), ('Í', 'I'),
        ('Ś', 'S'), ('Ṁ', 'M'),
    ]
    for old, new in replacements:
        name = name.replace(old, new)
    return name


def identify_sutta_from_name(raw_name: str) -> int:
    """Identify sutta number from a header name."""
    normalized_raw = normalize_name(raw_name)

    # First try exact match on normalized names
    for name, num in SUTTA_NAME_MAP.items():
        normalized_name = normalize_name(name)
        if normalized_name == normalized_raw:
            return num

    # Then try substring matching
    for name, num in SUTTA_NAME_MAP.items():
        normalized_name = normalize_name(name)
        # Check if either contains the other
        if normalized_name in normalized_raw or normalized_raw in normalized_name:
            return num

    return None


def clean_text(text: str) -> str:
    """Clean OCR artifacts, critical apparatus, and normalize text."""

    # Remove page headers (e.g., "2 BRAHMAJALA SUTTA. [D. i. 1. 2")
    # Handle both SUTTA (vol 1) and SUTTANTA (vols 2-3) formats
    text = re.sub(
        r'^\d+\s+[\'\|\s]*[A-ZĀĪŪṬḌṆṄÑṂḶPŚ][A-Za-zĀĪŪṬḌṆṄÑṂḶāīūṭḍṇṅñṃḷ\s\-]+[\s\-]*(?:SUTTA|SUTTANTA|BUTTA|BUTTANTA)\.?\s*(?:\[D\..*)?$',
        '', text, flags=re.MULTILINE
    )

    # Remove bottom-of-page references like "D. i. 1. 7] OF PRAISE AND BLAME. 3"
    text = re.sub(r'^D\.\s*[ivxl]+\..*\]\s+[A-Z][A-Z\s\-\']+\.?\s+\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove footnote blocks - lines starting with number followed by manuscript sigla
    # Pattern: "6 B" chattito." or "7 St mama ca..." or "1 Comp. A. ii. 57" etc.
    text = re.sub(
        r'^\d+\s*(?:B[""\^]?|S[tioåeè°""\^]?|K|M|G|Comp\.?|See|Omit|Add|Read|Så|Sè|BB|MSS\.?|§\*?)[^\n]{0,250}$',
        '', text, flags=re.MULTILINE | re.IGNORECASE
    )

    # Remove continued footnote lines (variant readings with semicolons)
    text = re.sub(r'^[a-zāīūṃṅñṇḷṭḍ][a-zāīūṃṅñṇḷṭḍ\-]*\s+[A-Z].*;\s*[A-Z][^\n]*$', '', text, flags=re.MULTILINE)

    # Remove "Comp." cross-references
    text = re.sub(r'^\d*\s*Comp\.?\s+[A-Z]\..*$', '', text, flags=re.MULTILINE)

    # Remove "See p. X" references
    text = re.sub(r'\s*See\s+p\.\s*\d+\.?', '', text, flags=re.IGNORECASE)

    # Remove inline superscript-style footnote markers (numbers before punctuation)
    text = re.sub(r'\s*[\d]+\s*(?=[,\.\?\!\;\:])', '', text)

    # Remove standalone footnote numbers between words
    text = re.sub(r'(?<=[a-zāīūṃṅñṇḷṭḍ])\s+\d+\s+(?=[A-ZĀĪŪṂṄÑṆḶṬḌ\'"])', ' ', text)

    # Remove lines that are just manuscript sigla or short apparatus
    text = re.sub(r'^\s*[BSKM][""\^]?\s*[^\n]{0,30}$', '', text, flags=re.MULTILINE)

    # Remove apparatus continuation fragments
    text = re.sub(r'^(?:tabbam|makkhito|etc|omit|om\.?|add\.?)\.\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # Remove stray OCR artifacts (single letters/symbols on their own lines)
    text = re.sub(r'^[\s]*[A-Za-z"\'=\-\*\|\^]{1,3}[\s]*$', '', text, flags=re.MULTILINE)

    # Remove PTS reference markers that got separated (like "[ D. xxi. 2. 9.")
    text = re.sub(r'\[\s*D\.\s*[ivxl]+\.\s*\d+\.?\s*\d*\.?\s*\]?', '', text, flags=re.IGNORECASE)

    # Remove multiple consecutive newlines
    text = re.sub(r'\n[\s]*\n+', '\n', text)

    # Normalize whitespace within lines
    text = re.sub(r'[ \t]+', ' ', text)

    # Fix common OCR errors
    text = text.replace('Bali', 'Pāli')
    text = text.replace(' , ', ', ')
    text = text.replace(' . ', '. ')

    # Fix ligature issues
    text = text.replace('ﬁ', 'fi')
    text = text.replace('ﬂ', 'fl')

    # Remove trailing whitespace on lines
    text = re.sub(r' +\n', '\n', text)

    return text.strip()


def normalize_pali(text: str) -> str:
    """Normalize Pāli orthography."""
    # Standardize niggahīta
    text = text.replace('ṁ', 'ṃ')
    text = text.replace('ŋ', 'ṃ')

    # Common OCR fixes for diacritics
    # (These may need adjustment based on actual OCR patterns)

    return text


def extract_page_refs(text: str) -> list:
    """Extract PTS page references from text.

    More flexible pattern that handles OCR variations and missing closing brackets.
    """
    refs = []
    # Pattern handles: [D. i. 1. 2  or [D.i.1.8 or [D. i L 12
    # Note: no closing bracket required, allows OCR errors in volume/numbers
    pattern = r'\[D\.?\s*(i+|ii+|I+|II+)[\.\s]+(\d+)(?:[\.\s,]+(\d+))?'
    for match in re.finditer(pattern, text, re.IGNORECASE):
        vol_str = match.group(1).lower()
        vol = len(vol_str)  # i=1, ii=2, iii=3
        page = int(match.group(2))
        section = int(match.group(3)) if match.group(3) else None
        refs.append({
            'vol': vol,
            'page': page,
            'section': section,
            'pos': match.start()
        })
    return refs


def extract_sutta_refs(text: str) -> list:
    """Extract PTS sutta references from text.

    In PTS DN, references like [D. vi. 4] mean sutta vi (6), section 4.
    The roman numeral is the sutta number, not the volume.
    """
    refs = []
    # Pattern: [D. vi. 4] or [D. viii. 8. etc.
    # Roman numerals i-xxxiv for suttas 1-34
    pattern = r'\[D\.?\s*(i{1,3}|iv|v|vi{1,3}|ix|x{1,3}i{0,3}|xi{1,3}v?|xv|xvi{1,3}|xix|xx|xxi{1,3}|xxiv|xxv|xxvi{1,3}|xxix|xxx|xxxi{1,3}|xxxiv)[\.\s]+(\d+)'

    roman_to_int = {
        'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8,
        'ix': 9, 'x': 10, 'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
        'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20, 'xxi': 21,
        'xxii': 22, 'xxiii': 23, 'xxiv': 24, 'xxv': 25, 'xxvi': 26, 'xxvii': 27,
        'xxviii': 28, 'xxix': 29, 'xxx': 30, 'xxxi': 31, 'xxxii': 32, 'xxxiii': 33,
        'xxxiv': 34
    }

    for match in re.finditer(pattern, text, re.IGNORECASE):
        roman = match.group(1).lower()
        section = int(match.group(2))
        sutta_num = roman_to_int.get(roman, 0)
        if sutta_num > 0:
            refs.append({
                'sutta': sutta_num,
                'section': section,
                'pos': match.start()
            })
    return refs


def parse_volume(vol_num: int) -> dict:
    """Parse a PTS volume file."""
    filepath = PTS_DIR / PTS_FILES[vol_num]

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find page headers to understand structure
    headers = find_page_headers(content)

    # Find where actual text begins - look for first valid page header
    text_start = 0
    for h in headers:
        if h['sutta_num'] is not None:
            # Go back a bit from the header to capture text before it
            text_start = max(0, h['pos'] - 500)
            break

    if text_start > 0:
        content = content[text_start:]
        # Recalculate headers after trimming
        headers = find_page_headers(content)

    return {
        'volume': vol_num,
        'content': content,
        'headers': headers,
        'page_refs': extract_page_refs(content)
    }


def extract_sutta_by_headers(vol_data: dict, sutta_num: int,
                              start_page: int, end_page: int) -> dict:
    """
    Extract a sutta using page headers for boundary detection.

    Uses sutta_num identification from header names as the primary method.
    """
    content = vol_data['content']
    headers = vol_data['headers']
    vol_num = vol_data['volume']
    vol_roman = 'i' * vol_num

    # Sort headers by position
    sorted_headers = sorted(headers, key=lambda h: h['pos'])

    # Find headers that match this sutta number
    sutta_headers = [h for h in sorted_headers if h['sutta_num'] == sutta_num]

    if not sutta_headers:
        # Fallback: try page number matching
        max_reasonable_page = 400
        sutta_headers = [h for h in sorted_headers
                        if start_page <= h['printed_page'] <= end_page
                        and h['printed_page'] <= max_reasonable_page]

    # Determine start position
    start_pos = 0
    if sutta_headers:
        sutta_headers = sorted(sutta_headers, key=lambda h: h['pos'])
        first_header = sutta_headers[0]
        start_pos = first_header['pos']

        # Find the header just before this one
        prev_headers = [h for h in sorted_headers if h['pos'] < start_pos]
        if prev_headers:
            prev_header = prev_headers[-1]
            line_end = content.find('\n', prev_header['pos'])
            if line_end != -1:
                start_pos = line_end + 1

    # Determine end position
    end_pos = len(content)

    if sutta_headers:
        last_header = sutta_headers[-1]
        next_headers = [h for h in sorted_headers
                       if h['pos'] > last_header['pos']
                       and h['sutta_num'] is not None
                       and h['sutta_num'] != sutta_num]
        if next_headers:
            end_pos = next_headers[0]['pos']

    # Fallback if no headers found
    if start_pos == 0:
        title = DN_SUTTAS[sutta_num][0].upper()
        title_match = re.search(rf'{re.escape(title)}', content, re.IGNORECASE)
        start_pos = title_match.start() if title_match else 0

    # Sanity check
    if end_pos <= start_pos:
        end_pos = len(content)

    sutta_text = content[start_pos:end_pos]

    # Clean the text
    sutta_text = clean_text(sutta_text)
    sutta_text = normalize_pali(sutta_text)

    return {
        'id': f'dn{sutta_num}',
        'title': DN_SUTTAS[sutta_num][0],
        'pts_ref': f'D {vol_roman} {start_page}-{end_page}',
        'volume': vol_num,
        'text': sutta_text,
        'char_count': len(sutta_text),
        'pages_found': len(sutta_headers)
    }


def segment_sutta(sutta: dict) -> list:
    """Split sutta into segments based on paragraph/section markers."""
    text = sutta['text']
    segments = []

    # Split on section numbers (e.g., "1." or "1, 1.")
    # or on sentence boundaries for now
    parts = re.split(r'(?<=\.)\s+(?=\d+[\.,]?\s)', text)

    if len(parts) <= 1:
        # Fallback: split on sentences
        parts = re.split(r'(?<=[.!?])\s+', text)

    for i, part in enumerate(parts):
        part = part.strip()
        if part:
            segments.append({
                'id': f"{sutta['id']}:pts.{i+1}",
                'pali': part
            })

    return segments


def main():
    print("=" * 60)
    print("Parsing PTS Dīgha Nikāya")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load volumes
    volumes = {}
    for vol_num in [1, 2, 3]:
        print(f"\nLoading Volume {vol_num}...")
        volumes[vol_num] = parse_volume(vol_num)
        print(f"  Content length: {len(volumes[vol_num]['content']):,} chars")
        print(f"  Page headers found: {len(volumes[vol_num]['headers'])}")
        print(f"  Page refs found: {len(volumes[vol_num]['page_refs'])}")

        # Show sample headers for debugging
        if volumes[vol_num]['headers']:
            print(f"  Sample headers:")
            for h in volumes[vol_num]['headers'][:3]:
                print(f"    p.{h['printed_page']}: {h['sutta_name']} (DN {h['sutta_num']})")

    # Extract each sutta
    print("\n" + "-" * 60)
    print("Extracting suttas...")

    all_suttas = []
    for sutta_num in range(1, 35):
        title, vol, start_page, end_page = DN_SUTTAS[sutta_num]

        sutta = extract_sutta_by_headers(
            volumes[vol],
            sutta_num, start_page, end_page
        )

        # Segment the sutta
        segments = segment_sutta(sutta)
        sutta['segments'] = segments
        sutta['segment_count'] = len(segments)

        all_suttas.append(sutta)

        pages_info = f", {sutta.get('pages_found', 0)} hdrs"
        print(f"  DN {sutta_num:2d}: {title:20s} ({sutta['char_count']:,} chars, {len(segments)} seg{pages_info})")

        # Remove internal debug info from output
        if 'pages_found' in sutta:
            del sutta['pages_found']

        # Save individual sutta file
        output_file = OUTPUT_DIR / f"dn{sutta_num}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

    # Save index
    index = {
        'source': 'Pali Text Society editions',
        'volumes': {
            1: 'Dīgha Nikāya Vol. I (Rhys Davids & Carpenter, 1890)',
            2: 'Dīgha Nikāya Vol. II (Rhys Davids & Carpenter, 1903)',
            3: 'Dīgha Nikāya Vol. III (Carpenter, 1911)',
        },
        'suttas': [
            {
                'id': s['id'],
                'title': s['title'],
                'pts_ref': s['pts_ref'],
                'chars': s['char_count'],
                'segments': s['segment_count']
            }
            for s in all_suttas
        ],
        'total_chars': sum(s['char_count'] for s in all_suttas),
        'total_segments': sum(s['segment_count'] for s in all_suttas)
    }

    with open(OUTPUT_DIR / '_index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Total characters: {index['total_chars']:,}")
    print(f"Total segments: {index['total_segments']}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
