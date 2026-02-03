#!/usr/bin/env python3
"""
Extract proper names from the Dictionary of Pāli Proper Names (DPPN).

Parses HTML files downloaded from aimwell.org/DPPN and creates
a structured JSON file of all proper names for use in lemmatization.
"""

import json
import re
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "data"
DPPN_DIR = DATA_DIR / "dppn"
OUTPUT_FILE = DPPN_DIR / "proper_names.json"


class TitleExtractor(HTMLParser):
    """Extract title from HTML."""

    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def normalize_name(name: str) -> str:
    """Normalize a proper name for matching."""
    # Lowercase
    name = name.lower()
    # Standardize niggahīta
    name = name.replace('ṁ', 'ṃ')
    # Remove numbers and parenthetical notes
    name = re.sub(r'\s*\d+\s*$', '', name)
    name = re.sub(r'\s*\([^)]*\)\s*', '', name)
    return name.strip()


def extract_name_from_file(filepath: Path) -> dict:
    """Extract proper name entry from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        parser = TitleExtractor()
        parser.feed(content)
        title = parser.title.strip()

        if not title or title in ('Index', 'Help', 'Abbreviations'):
            return None

        # Determine category from filename patterns
        filename = filepath.stem.lower()
        category = "unknown"

        if '_thera' in filename or '_theri' in filename:
            category = "person"
        elif '_sutta' in filename:
            category = "text"
        elif '_jataka' in filename:
            category = "text"
        elif '_nikaya' in filename or '_pitaka' in filename:
            category = "text"
        elif '_vagga' in filename:
            category = "text"
        elif '_vihara' in filename or '_cetiya' in filename:
            category = "place"
        elif any(x in filename for x in ['_river', 'nagara', 'pura', 'gama']):
            category = "place"
        else:
            # Check content for clues
            content_lower = content.lower()
            if 'was a monk' in content_lower or 'was a nun' in content_lower:
                category = "person"
            elif 'was a king' in content_lower or 'was a brahmin' in content_lower:
                category = "person"
            elif 'is a sutta' in content_lower or 'is a discourse' in content_lower:
                category = "text"
            elif 'is a place' in content_lower or 'is a city' in content_lower:
                category = "place"
            else:
                category = "person"  # Default for DPPN

        return {
            "name": title,
            "normalized": normalize_name(title),
            "category": category,
            "source_file": filepath.name
        }

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


def main():
    print("Extracting proper names from DPPN...")

    # Get all HTML files except index/navigation files
    skip_files = {'index.html', 'help.html', 'a.html', 'b.html', 'c.html',
                  'd.html', 'e.html', 'g.html', 'h.html', 'i.html', 'j.html',
                  'k.html', 'l.html', 'm.html', 'n.html', 'o.html', 'p.html',
                  'r.html', 's.html', 't.html', 'u.html', 'v.html', 'y.html'}

    html_files = sorted([f for f in DPPN_DIR.glob("*.html")
                         if f.name not in skip_files])

    print(f"Found {len(html_files)} entry files")

    entries = []
    name_variants = {}  # normalized -> list of original forms

    for i, filepath in enumerate(html_files):
        if (i + 1) % 500 == 0:
            print(f"  Processing {i+1}/{len(html_files)}...")

        entry = extract_name_from_file(filepath)
        if entry:
            entries.append(entry)

            # Track variants
            norm = entry["normalized"]
            if norm not in name_variants:
                name_variants[norm] = []
            if entry["name"] not in name_variants[norm]:
                name_variants[norm].append(entry["name"])

    # Create output structure
    output = {
        "source": "Dictionary of Pāli Proper Names (G.P. Malalasekera)",
        "url": "https://www.aimwell.org/DPPN/",
        "total_entries": len(entries),
        "unique_names": len(name_variants),
        "categories": {
            "person": len([e for e in entries if e["category"] == "person"]),
            "place": len([e for e in entries if e["category"] == "place"]),
            "text": len([e for e in entries if e["category"] == "text"]),
            "unknown": len([e for e in entries if e["category"] == "unknown"]),
        },
        "entries": entries,
        # Quick lookup table: normalized name -> category
        "lookup": {e["normalized"]: e["category"] for e in entries}
    }

    # Save output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Extracted {len(entries)} proper name entries")
    print(f"Unique normalized names: {len(name_variants)}")
    print(f"\nCategories:")
    print(f"  Persons: {output['categories']['person']}")
    print(f"  Places:  {output['categories']['place']}")
    print(f"  Texts:   {output['categories']['text']}")
    print(f"  Unknown: {output['categories']['unknown']}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
