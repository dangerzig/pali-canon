#!/usr/bin/env python3
"""
Parse GRETIL PTS HTML files to extract text with PTS page/section references.

GRETIL format:
- [page NNN] - printed page numbers
- [D. i. N. M - PTS reference (volume, page, section)
- Text flows continuously with <BR> tags

Output: JSON with text segments mapped to PTS references.
"""

import re
import json
from pathlib import Path
from html.parser import HTMLParser
from dataclasses import dataclass, asdict
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed"


@dataclass
class PTSRef:
    """PTS reference: D i 1.5 = Dīgha volume i, page 1, section 5"""
    collection: str  # D, M, S, A
    volume: str      # Roman numeral (i, ii, iii)
    page: int
    section: int

    def __str__(self):
        return f"{self.collection} {self.volume} {self.page}.{self.section}"

    def to_dict(self):
        return {
            'collection': self.collection,
            'volume': self.volume,
            'page': self.page,
            'section': self.section,
            'ref': str(self)
        }


@dataclass
class TextBlock:
    """A block of text with its PTS reference range."""
    text: str
    pts_start: Optional[PTSRef]
    pts_end: Optional[PTSRef]
    printed_page: int


class GRETILParser(HTMLParser):
    """Parse GRETIL HTML and extract text with markers."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_body = False
        self.skip_tags = {'style', 'script', 'table'}
        self.current_skip = None

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if tag in self.skip_tags:
            self.current_skip = tag
        if tag == 'br' and self.in_body and not self.current_skip:
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        if tag == self.current_skip:
            self.current_skip = None

    def handle_data(self, data):
        if self.in_body and not self.current_skip:
            self.text_parts.append(data)

    def get_text(self):
        return ''.join(self.text_parts)


def parse_pts_ref(ref_str: str) -> Optional[PTSRef]:
    """Parse a PTS reference string like 'D. i. 1. 8' or 'D. i. 2. 15'."""
    # Pattern: D. i. PAGE. SECTION (sometimes without trailing bracket)
    match = re.match(r'\[?([DMSA])\.\s*([ivx]+)\.\s*(\d+)\.\s*(\d+)', ref_str, re.IGNORECASE)
    if match:
        return PTSRef(
            collection=match.group(1).upper(),
            volume=match.group(2).lower(),
            page=int(match.group(3)),
            section=int(match.group(4))
        )
    return None


def extract_markers(text: str) -> list:
    """Extract page markers and PTS references from text."""
    markers = []

    # Find page markers: [page NNN]
    for match in re.finditer(r'\[page\s+(\d+)\]', text):
        markers.append({
            'type': 'page',
            'pos': match.start(),
            'end': match.end(),
            'page': int(match.group(1))
        })

    # Find PTS references: [D. i. N. M
    for match in re.finditer(r'\[([DMSA])\.\s*([ivx]+)\.\s*(\d+)\.\s*(\d+)', text, re.IGNORECASE):
        pts = PTSRef(
            collection=match.group(1).upper(),
            volume=match.group(2).lower(),
            page=int(match.group(3)),
            section=int(match.group(4))
        )
        markers.append({
            'type': 'pts',
            'pos': match.start(),
            'end': match.end(),
            'pts': pts
        })

    # Sort by position
    markers.sort(key=lambda m: m['pos'])
    return markers


def extract_sutta_boundaries(text: str) -> list:
    """Find sutta title markers to identify boundaries."""
    # Pattern: [i. Sutta Name] or [xiv. Suttanta Name] or just "i. Sutta Name]"
    boundaries = []

    # Roman numeral followed by sutta name - bracket may be missing at start
    for match in re.finditer(r'\[?([ivx]+)\.\s+([^\]]+?)\s*Sutta(?:nta)?\s*\.?\s*\]', text, re.IGNORECASE):
        roman = match.group(1).lower()
        name = match.group(2).strip()
        # Convert roman to number
        roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7,
                     'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12, 'xiii': 13,
                     'xiv': 14, 'xv': 15, 'xvi': 16, 'xvii': 17, 'xviii': 18,
                     'xix': 19, 'xx': 20, 'xxi': 21, 'xxii': 22, 'xxiii': 23,
                     'xxiv': 24, 'xxv': 25, 'xxvi': 26, 'xxvii': 27, 'xxviii': 28,
                     'xxix': 29, 'xxx': 30, 'xxxi': 31, 'xxxii': 32, 'xxxiii': 33,
                     'xxxiv': 34}
        sutta_num = roman_map.get(roman, 0)

        boundaries.append({
            'pos': match.start(),
            'end': match.end(),
            'sutta_num': sutta_num,
            'name': name,
            'marker': match.group(0)
        })

    return boundaries


def clean_text(text: str) -> str:
    """Clean GRETIL text while preserving structure."""
    # Remove page markers
    text = re.sub(r'\[page\s+\d+\]', '', text)

    # Remove header lines (page number + sutta name + PTS ref)
    text = re.sub(r'^\d+\s+[A-ZĀĪŪṬḌṆṄÑṂḶ][A-ZĀĪŪṬḌṆṄÑṂḶA-zāīūṭḍṇṅñṃḷ\s\-]+\.?\s*\[D\..*$',
                  '', text, flags=re.MULTILINE)

    # Remove content straddling notices
    text = re.sub(r'\[.*?content straddling.*?\]', '', text, flags=re.IGNORECASE)

    # Remove sutta title markers but keep for reference
    # text = re.sub(r'\[[ivx]+\.\s+[^\]]+Sutta[^\]]*\]', '', text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def parse_volume(html_path: Path, volume_num: int) -> dict:
    """Parse a GRETIL HTML volume file."""
    print(f"Parsing {html_path.name}...")

    # Parse HTML
    html = html_path.read_text(encoding='utf-8')
    parser = GRETILParser()
    parser.feed(html)
    raw_text = parser.get_text()

    # Extract markers
    markers = extract_markers(raw_text)
    sutta_boundaries = extract_sutta_boundaries(raw_text)

    print(f"  Found {len([m for m in markers if m['type'] == 'page'])} page markers")
    print(f"  Found {len([m for m in markers if m['type'] == 'pts'])} PTS refs")
    print(f"  Found {len(sutta_boundaries)} sutta boundaries")

    # Build page-to-position map
    page_map = []
    for m in markers:
        if m['type'] == 'page':
            page_map.append({
                'printed_page': m['page'],
                'pos': m['pos']
            })

    # Build PTS ref map
    pts_map = []
    for m in markers:
        if m['type'] == 'pts':
            pts_map.append({
                'ref': m['pts'].to_dict(),
                'pos': m['pos']
            })

    return {
        'volume': volume_num,
        'file': html_path.name,
        'raw_text': raw_text,
        'text_length': len(raw_text),
        'page_map': page_map,
        'pts_map': pts_map,
        'sutta_boundaries': sutta_boundaries
    }


def extract_sutta_from_volume(vol_data: dict, sutta_num: int, next_sutta_num: Optional[int]) -> dict:
    """Extract a single sutta from volume data."""
    # Find this sutta's boundary
    boundaries = vol_data['sutta_boundaries']

    sutta_start = None
    sutta_end = None
    sutta_name = None

    for i, b in enumerate(boundaries):
        if b['sutta_num'] == sutta_num:
            sutta_start = b['end']  # Start after the marker
            sutta_name = b['name']
            # Find end - either next boundary or end of volume
            if i + 1 < len(boundaries):
                sutta_end = boundaries[i + 1]['pos']
            break
        elif next_sutta_num and b['sutta_num'] == next_sutta_num:
            sutta_end = b['pos']  # End at next sutta's marker
            break

    if sutta_start is None:
        return None

    if sutta_end is None:
        sutta_end = len(vol_data['raw_text'])

    # Extract text
    raw_sutta = vol_data['raw_text'][sutta_start:sutta_end]
    cleaned = clean_text(raw_sutta)

    # Find PTS refs within this sutta
    pts_refs = []
    for pts in vol_data['pts_map']:
        if sutta_start <= pts['pos'] < sutta_end:
            pts_refs.append(pts['ref'])

    # Find page range
    pages = []
    for pm in vol_data['page_map']:
        if sutta_start <= pm['pos'] < sutta_end:
            pages.append(pm['printed_page'])

    # Determine PTS page range
    if pts_refs:
        pts_start = pts_refs[0]
        pts_end = pts_refs[-1]
        pts_range = f"{pts_start['collection']} {pts_start['volume']} {pts_start['page']}-{pts_end['page']}"
    else:
        pts_range = None

    return {
        'sutta': sutta_num,
        'name': sutta_name,
        'volume': vol_data['volume'],
        'text': cleaned,
        'pts_range': pts_range,
        'pts_refs': pts_refs,
        'printed_pages': [min(pages), max(pages)] if pages else None,
        'word_count': len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', cleaned.lower()))
    }


def tokenize_with_positions(text: str) -> list:
    """Tokenize text and track character positions."""
    tokens = []
    for match in re.finditer(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+', text):
        tokens.append({
            'word': match.group(0).lower(),
            'start': match.start(),
            'end': match.end(),
            'original': match.group(0)
        })
    return tokens


def main():
    print("=" * 70)
    print("Parsing GRETIL PTS DN Volumes")
    print("=" * 70)
    print()

    # Ensure output directory exists
    dn_output = OUTPUT_DIR / "dn"
    dn_output.mkdir(parents=True, exist_ok=True)

    # Parse all three volumes
    volumes = {}
    vol_files = [
        (1, GRETIL_DIR / "dn_vol1.html"),
        (2, GRETIL_DIR / "dn_vol2.html"),
        (3, GRETIL_DIR / "dn_vol3.html"),
    ]

    for vol_num, vol_path in vol_files:
        if vol_path.exists():
            volumes[vol_num] = parse_volume(vol_path, vol_num)
        else:
            print(f"Warning: {vol_path} not found")

    # DN sutta to volume mapping
    dn_vol_map = {
        **{i: 1 for i in range(1, 14)},   # DN 1-13 in Vol 1
        **{i: 2 for i in range(14, 24)},  # DN 14-23 in Vol 2
        **{i: 3 for i in range(24, 35)},  # DN 24-34 in Vol 3
    }

    print()
    print("Extracting suttas...")

    results = []
    for sutta_num in range(1, 35):
        vol_num = dn_vol_map[sutta_num]
        next_sutta = sutta_num + 1 if sutta_num < 34 else None

        if vol_num in volumes:
            # Handle cross-volume boundaries
            if next_sutta and dn_vol_map.get(next_sutta) != vol_num:
                next_sutta = None  # End of volume

            sutta_data = extract_sutta_from_volume(volumes[vol_num], sutta_num, next_sutta)

            if sutta_data:
                print(f"  DN {sutta_num:2d}: {sutta_data['word_count']:>6,} words, "
                      f"PTS {sutta_data['pts_range'] or 'N/A'}")

                # Save individual sutta
                output_file = dn_output / f"dn{sutta_num}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(sutta_data, f, indent=2, ensure_ascii=False)

                results.append({
                    'sutta': sutta_num,
                    'name': sutta_data['name'],
                    'words': sutta_data['word_count'],
                    'pts_range': sutta_data['pts_range']
                })
            else:
                print(f"  DN {sutta_num:2d}: Failed to extract")
        else:
            print(f"  DN {sutta_num:2d}: Volume {vol_num} not loaded")

    # Save summary
    summary_file = dn_output / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'GRETIL PTS DN Edition',
            'volumes_parsed': list(volumes.keys()),
            'suttas': results,
            'total_words': sum(r['words'] for r in results)
        }, f, indent=2, ensure_ascii=False)

    print()
    print(f"Total: {sum(r['words'] for r in results):,} words across {len(results)} suttas")
    print(f"Output saved to: {dn_output}")


if __name__ == "__main__":
    main()
