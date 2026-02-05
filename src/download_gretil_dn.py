#!/usr/bin/env python3
"""
Download and process GRETIL Dīgha Nikāya PTS edition.

The GRETIL (Göttingen Register of Electronic Texts in Indian Languages) hosts
properly digitized versions of the PTS Dīgha Nikāya. These were transcribed
by the Dhammakaya Foundation and are licensed CC BY-SA 4.0.

Source: https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/
"""

import re
import json
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"
OUTPUT_DIR = DATA_DIR / "gretil-parsed/dn"

GRETIL_URLS = {
    1: "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn1pu.htm",
    2: "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn2pu.htm",
    3: "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn3pu.htm",
}

# Sutta names and volumes - for matching Roman numeral markers
# Format: sutta_num -> (volume, roman_numeral, sutta_name_pattern)
# Note: Vol 2 & 3 use "Suttanta" not "Sutta", and Roman numerals continue from vol 1
DN_SUTTAS = {
    1: (1, "i", "Brahmajāla"),
    2: (1, "ii", "Sāmañña-?Phala"),
    3: (1, "iii", "Ambaṭṭha"),
    4: (1, "iv", "Soṇadaṇḍa"),
    5: (1, "v", "Kūṭadanta"),
    6: (1, "vi", "Mahāli"),
    7: (1, "vii", "Jāliya"),
    8: (1, "viii", "Kassapa"),
    9: (1, "ix", "Poṭṭhapāda"),
    10: (1, "x", "Subha"),
    11: (1, "xi", "Kevaṭṭa|Kevaddha"),
    12: (1, "xii", "Lohicca"),
    13: (1, "xiii", "Tevijja"),
    14: (2, "xiv", "Mahā-?padāna"),
    15: (2, "xv", "Mahā-?[Nn]idāna"),
    16: (2, "xvi", "Mahā-?[Pp]arinibbāna"),
    17: (2, "xvii", "Mahā-?[Ss]udassana"),
    18: (2, "xviii", "Janavasabha"),
    19: (2, "xix", "Mahā-?[Gg]ovinda"),
    20: (2, "xx", "Mahā-?[Ss]amaya"),
    21: (2, "xxi", "Sakka-?[Pp]añha"),
    22: (2, "xxii", "Mahā-?[Ss]atipaṭṭhāna"),
    23: (2, "xxiii", "Pāyāsi"),
    24: (3, "xxiv", "Pāṭika|Pāthika"),
    25: (3, "xxv", "Udumbarika"),
    26: (3, "xxvi", "Cakka-?vatti"),
    27: (3, "xxvii", "Aggañña"),
    28: (3, "xxviii", "Sampasādanīya"),
    29: (3, "xxix", "Pāsādika"),
    30: (3, "xxx", "Lakkhaṇa"),
    31: (3, "xxxi", "Siṅgāl(a|ov)āda"),
    32: (3, "xxxii", "Āṭānāṭiya"),
    33: (3, "xxxiii", "Saṅgīti"),
    34: (3, "xxxiv", "Dasa-?uttara"),
}


class GRETILHTMLParser(HTMLParser):
    """Extract text from GRETIL HTML."""

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


def download_volume(vol_num: int) -> str:
    """Download GRETIL volume and return text."""
    url = GRETIL_URLS[vol_num]
    cache_file = GRETIL_DIR / f"dn_vol{vol_num}.html"

    if cache_file.exists():
        print(f"  Using cached volume {vol_num}")
        html = cache_file.read_text(encoding='utf-8')
    else:
        print(f"  Downloading volume {vol_num} from GRETIL...")
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
        cache_file.write_text(html, encoding='utf-8')

    # Parse HTML
    parser = GRETILHTMLParser()
    parser.feed(html)
    return parser.get_text()


def extract_page_refs(text: str) -> list:
    """Extract PTS page references from text."""
    # Pattern: [page NNN] or [D. i. N. N
    page_pattern = r'\[page\s+(\d+)\]'
    ref_pattern = r'\[D\.\s+([ivx]+)\.\s+\d+\.\s+(\d+)'

    pages = re.findall(page_pattern, text)
    refs = re.findall(ref_pattern, text)

    return {
        'page_markers': len(pages),
        'pts_refs': len(refs)
    }


def clean_gretil_text(text: str) -> str:
    """Clean GRETIL text while preserving structure."""
    # Remove page markers but keep section numbers
    text = re.sub(r'\[page\s+\d+\]', '', text)

    # Remove header lines (italicized page headers)
    text = re.sub(r'^.*D\.\s+[ivx]+\.\s+\d+\.\s+\d+.*$', '', text, flags=re.MULTILINE)

    # Remove notes about content straddling page breaks
    text = re.sub(r'\[.*?content straddling.*?\]', '', text, flags=re.IGNORECASE)

    # Remove section labels like "Cūla-Sīlaṃ niṭṭhitaṃ"
    text = re.sub(r'^\s*[A-Z][a-zāīūṭḍṇṅñṃḷ-]+-[Ss]īlaṃ niṭṭhitaṃ\.?\s*$', '', text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def extract_sutta(text: str, sutta_num: int, vol_text: dict) -> dict:
    """Extract a single sutta from volume text."""
    vol, roman, name_pattern = DN_SUTTAS[sutta_num]
    vol_content = vol_text.get(vol, '')

    # Find sutta marker: [i. Brahmajāla Sutta.] or [xiv. Mahāpadāna-Suttanta.] or similar
    # The marker format is: [roman. Name Sutta(nta).]
    start_pattern = rf'\[{roman}\.\s+{name_pattern}[^\]]*Sutta(?:nta)?[^\]]*\]'
    start_match = re.search(start_pattern, vol_content, re.IGNORECASE)

    if not start_match:
        # Try without the bracket
        start_pattern = rf'{roman}\.\s+{name_pattern}[^\n]*Sutta(?:nta)?'
        start_match = re.search(start_pattern, vol_content, re.IGNORECASE)

    if not start_match:
        return None

    start_pos = start_match.end()

    # Find next sutta marker
    next_sutta = sutta_num + 1
    if next_sutta in DN_SUTTAS and DN_SUTTAS[next_sutta][0] == vol:
        next_vol, next_roman, next_name = DN_SUTTAS[next_sutta]
        end_pattern = rf'\[{next_roman}\.\s+{next_name}[^\]]*Sutta(?:nta)?[^\]]*\]'
        end_match = re.search(end_pattern, vol_content[start_pos:], re.IGNORECASE)
        if end_match:
            end_pos = start_pos + end_match.start()
        else:
            # Try vagga end or volume end
            end_pos = len(vol_content)
    else:
        end_pos = len(vol_content)

    sutta_text = vol_content[start_pos:end_pos]
    cleaned = clean_gretil_text(sutta_text)

    return {
        'sutta': sutta_num,
        'volume': vol,
        'text': cleaned,
        'chars': len(cleaned),
        'words': len(re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', cleaned.lower()))
    }


def tokenize(text: str) -> list:
    """Tokenize Pāli text."""
    text = text.lower().replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')
    return re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', text)


def analyze_quality(sutta_data: dict, sc_data: dict) -> dict:
    """Compare GRETIL sutta to SC canonical."""
    gretil_words = tokenize(sutta_data['text'])
    sc_text = ' '.join(seg.get('pali', '') for seg in sc_data.get('segments', []))
    sc_words = tokenize(sc_text)

    gretil_set = set(gretil_words)
    sc_set = set(sc_words)

    common = gretil_set & sc_set
    gretil_only = gretil_set - sc_set
    sc_only = sc_set - gretil_set

    return {
        'gretil_word_count': len(gretil_words),
        'sc_word_count': len(sc_words),
        'ratio': round(len(gretil_words) / len(sc_words), 2) if sc_words else 0,
        'common_forms': len(common),
        'gretil_only': len(gretil_only),
        'sc_only': len(sc_only),
        'overlap_pct': round(len(common) / len(gretil_set | sc_set) * 100, 1) if gretil_set | sc_set else 0
    }


def main():
    print("=" * 70)
    print("Downloading and Processing GRETIL DN PTS Edition")
    print("=" * 70)
    print()

    # Ensure directories exist
    GRETIL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Download all volumes
    print("Downloading volumes...")
    vol_text = {}
    for vol_num in [1, 2, 3]:
        vol_text[vol_num] = download_volume(vol_num)
        refs = extract_page_refs(vol_text[vol_num])
        print(f"    Vol {vol_num}: {len(vol_text[vol_num]):,} chars, "
              f"{refs['page_markers']} page markers, {refs['pts_refs']} PTS refs")

    print()
    print("Extracting suttas...")

    results = []
    sc_dir = DATA_DIR / "canonical/dn"

    for sutta_num in range(1, 35):
        sutta_data = extract_sutta(vol_text[DN_SUTTAS[sutta_num][0]], sutta_num, vol_text)

        if sutta_data:
            # Load SC canonical for comparison
            sc_file = sc_dir / f"dn{sutta_num}.json"
            if sc_file.exists():
                sc_data = json.loads(sc_file.read_text())
                quality = analyze_quality(sutta_data, sc_data)
            else:
                quality = {}

            # Determine quality indicator
            ratio = quality.get('ratio', 0)
            overlap = quality.get('overlap_pct', 0)

            if 0.85 <= ratio <= 1.15 and overlap >= 90:
                indicator = "✓"
            elif 0.7 <= ratio <= 1.3 and overlap >= 80:
                indicator = "~"
            else:
                indicator = "✗"

            print(f"  DN {sutta_num:2d}: {sutta_data['words']:>6,} words, "
                  f"ratio={ratio:.2f}, overlap={overlap:.1f}% {indicator}")

            # Save sutta
            output_file = OUTPUT_DIR / f"dn{sutta_num}.json"
            output_data = {
                'sutta': sutta_num,
                'source': 'GRETIL PTS Edition',
                'volume': sutta_data['volume'],
                'text': sutta_data['text'],
                'quality': quality
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            results.append({
                'sutta': sutta_num,
                **quality
            })
        else:
            print(f"  DN {sutta_num:2d}: Failed to extract")

    # Summary
    print()
    print("-" * 70)
    print("Summary:")

    good = [r for r in results if 0.85 <= r.get('ratio', 0) <= 1.15]
    moderate = [r for r in results if 0.7 <= r.get('ratio', 0) <= 1.3 and r not in good]

    print(f"  Good quality (ratio 0.85-1.15):  {len(good):2d} suttas")
    print(f"  Moderate quality (ratio 0.7-1.3): {len(moderate):2d} suttas")

    avg_ratio = sum(r.get('ratio', 0) for r in results) / len(results)
    avg_overlap = sum(r.get('overlap_pct', 0) for r in results) / len(results)

    print(f"  Average word ratio: {avg_ratio:.2f}")
    print(f"  Average vocabulary overlap: {avg_overlap:.1f}%")

    # Save summary
    summary_file = OUTPUT_DIR / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'GRETIL PTS DN Edition',
            'url': 'https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/',
            'license': 'CC BY-SA 4.0',
            'average_ratio': round(avg_ratio, 2),
            'average_overlap': round(avg_overlap, 1),
            'suttas': results
        }, f, indent=2)

    print()
    print(f"Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
