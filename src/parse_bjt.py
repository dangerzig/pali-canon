#!/usr/bin/env python3
"""
Parse BJT (Buddha Jayanti Tripitaka) SLTP editions.

Reads HTML files downloaded from Access to Insight's SLTP collection
(Sutta Pitaka) and agamarama.com (Vinaya, Abhidhamma) and outputs
cleaned JSON files matching the GRETIL parsed format.

Covers:
- Vinaya Pitaka: 5 volumes (Suttavibhanga I/II, Mahavagga, Cullavagga, Parivara)
- Sutta Pitaka: DN (3 vols), MN (3 vols), SN (5 vols), AN (5 vols)
- Khuddaka Nikaya: 23 texts (single and multi-volume)
- Abhidhamma Pitaka: 9 texts (Dhs, Vibh, Dhatuk, Kv I/II, Yam I/II, Patth I/II)
"""

import re
import json
import html as html_module
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BJT_DIR = DATA_DIR / "bjt-raw"
OUTPUT_DIR = DATA_DIR / "bjt-parsed"

# Manuscript abbreviation keywords found in BJT footnotes.
# These identify variant readings from different manuscript traditions.
MS_KEYWORDS = [
    # Myanmar/Burmese manuscripts
    'machasaṃ', 'machasa', 'ma cha sa', 'ma cha saṃ', 'machasan',
    # Sinhalese manuscripts
    'sīmu', 'si mu', 'sī mu', 'sitri', 'sitira', 'sītira',
    'sī.', ', sī ', ', si.', ', si ',
    # Thai manuscripts
    ', the.', ', the ', 'syā',
    # Editions
    '[pts]', '[p t s', '[pts.', '[i.]', '[i]', '[ii.]', '[ii]',
    # General terms
    'katthaci', 'katthavi', 'kesuci', 'kesuvi', 'kesūci',
    'bahusu', 'bahūsu',
    'sabbattha',
    'bausasa', 'bau.', 'lau.',
    # Manuscript/textual notes
    'potthakesu', 'potthake',
    'aṭṭhakathā',
    'na dissati', 'na dissanti',
]

# KN single-file texts: bjt_prefix -> (output_name, display_title)
KN_SINGLE = {
    'Khp': ('khuddakapatha', 'Khuddakapāṭha'),
    'Dhp': ('dhammapada', 'Dhammapada'),
    'Ud':  ('udana', 'Udāna'),
    'It':  ('itivuttaka', 'Itivuttaka'),
    'Sn':  ('suttanipata', 'Suttanipāta'),
    'Vv':  ('vimanavatthu', 'Vimānavatthu'),
    'Pv':  ('petavatthu', 'Petavatthu'),
    'Th':  ('theragatha', 'Theragāthā'),
    'Thi': ('therigatha', 'Therīgāthā'),
    'Bv':  ('buddhavamsa', 'Buddhavaṃsa'),
    'Cp':  ('cariyapitaka', 'Cariyāpiṭaka'),
}


# ==================== Text Cleaning Pipeline ====================

def extract_content_chunk(html_content: str) -> str:
    """Extract text between COPYRIGHTED_TEXT_CHUNK markers."""
    start_marker = 'COPYRIGHTED_TEXT_CHUNK'
    end_marker = 'END OF COPYRIGHTED TEXT CHUNK'

    start_idx = html_content.find(start_marker)
    if start_idx == -1:
        return html_content  # fallback: use entire content

    # Move past the closing > of the start tag
    start_idx = html_content.find('>', start_idx)
    if start_idx == -1:
        return html_content
    start_idx += 1

    end_idx = html_content.find(end_marker)
    if end_idx == -1:
        end_idx = len(html_content)
    else:
        # Back up to the <!-- before the end marker
        end_idx = html_content.rfind('<', 0, end_idx)

    return html_content[start_idx:end_idx]


def strip_html(text: str) -> str:
    """Decode HTML entities and strip tags, converting <br> to newlines."""
    text = html_module.unescape(text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def remove_formatting_codes(text: str) -> str:
    """Remove BJT-specific formatting codes like [\\q NNN/], [\\x NNN/], etc."""
    text = re.sub(r'\[\\[a-z]\s+[^\]]*?\]', '', text)
    return text


def remove_page_markers(text: str) -> str:
    """Remove all [PTS ...] and [BJT ...] bracketed markers."""
    # Catch-all for PTS/BJT markers (page, volume, edition refs, etc.)
    text = re.sub(r'\[(?:PTS|BJT)\s*[^\]]*\]', '', text)
    return text


def is_footnote_line(line: str) -> bool:
    """Determine if a line is a footnote rather than sutta text.

    Footnotes start with N. and contain manuscript abbreviation keywords.
    Dash separator lines are also classified as footnotes.
    Sanskrit parallel verses (in Dhammapada) are detected by ś/ṣ characters.
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Dash separator lines (e.g., "- - - - - - - - -" or "----------")
    dashes = stripped.replace(' ', '').replace('\t', '')
    if dashes and all(c == '-' for c in dashes) and len(dashes) >= 5:
        return True

    # Asterisk lines (editorial notes, separators)
    if stripped == '* * *':
        return True
    if stripped.startswith('*(') or stripped.startswith('*.'):
        return True

    # Sanskrit parallel verses (Dhammapada): contain ś or ṣ
    if 'ś' in stripped or 'ṣ' in stripped:
        return True
    # Sanskrit source references
    if 'ūlasarvāstivādi' in stripped.lower():
        return True

    # Lines starting with N. or N- (footnote pattern, with or without space)
    if not re.match(r'^\d+[\.\-]', stripped):
        return False

    lower = stripped.lower()

    # Check for manuscript abbreviation keywords
    if any(kw in lower for kw in MS_KEYWORDS):
        return True

    # Multi-footnote lines: "1.reading. 2.reading" (with or without spaces)
    if re.search(r'\d+[\.\-]\s?[A-ZĀ-Ž].*\d+[\.\-]\s?[A-ZĀ-Ž]', stripped):
        if len(stripped) < 300:
            return True

    return False


def remove_inline_footnote_refs(text: str) -> str:
    """Remove trailing footnote reference digits from Pali words.

    E.g., 'anubaddhā1' -> 'anubaddhā', 'ubbilāvino2' -> 'ubbilāvino'
    Does NOT affect section numbers like '1. Evaṃ me sutaṃ'.
    """
    # Match a Pali letter followed by digits at a word boundary
    text = re.sub(
        r'([a-zāīūṭḍṇṅñṃḷ])\d+(?=[\s\.,;:\?\!\-\n\'\"\)]|$)',
        r'\1',
        text,
        flags=re.IGNORECASE,
    )
    return text


def remove_inline_footnotes(text: str) -> str:
    """Remove footnote fragments embedded within text lines.

    Catches patterns like:
    - "Suttaṃ, machasaṃ." (variant title note)
    - "1.Anācārī, machasaṃ. 2.Ṭheto,syā." (numbered inline footnotes)
    """
    # MS abbreviation alternation for regex
    ms_alt = (
        r'machasaṃ|machasa|ma cha saṃ|ma cha sa|'
        r'sīmu|si mu|sī mu|sitri|sitira|sītira|'
        r'katthaci|kesuci|kesuvi|bahūsu|bahusu|sabbattha|'
        r'syā|bausasa|bau\.|aṭṭhakathā'
    )

    # Remove numbered inline footnote clusters: "N.word,ms. N.word,ms."
    text = re.sub(
        r'\d+\.[\w\u0080-\u024F\u1E00-\u1EFF]+\s*[,\.]\s*'
        r'(?:' + ms_alt + r')\s*\.?\s*',
        '', text, flags=re.IGNORECASE,
    )
    # Remove standalone ", ms_abbreviation." after words
    text = re.sub(
        r',\s*(?:' + ms_alt + r')\s*\.',
        '.', text, flags=re.IGNORECASE,
    )
    return text


def remove_variant_apparatus(text: str) -> str:
    """Remove multi-edition variant reading entries (found in AN_I).

    AN_I contains inline variant entries like:
      N [BJTS] = word [ChS]= word [PTS] = word [Thai] = word [Kambodian] =
    These are interspersed with actual sutta text and need to be
    removed while preserving the sutta text around them.
    """
    if '[BJTS]' not in text:
        return text

    # Remove variant entry lines: "N [BJTS] = word [ChS]= word ..."
    # These start with a number and contain edition markers
    text = re.sub(
        r'\d+\s*\[BJTS\]\s*=\s*[^\n]*',
        '', text,
    )
    # Remove any remaining edition markers
    text = re.sub(r'\[BJTS\]', '', text)
    text = re.sub(r'\[ChS\]\s*=?\s*\w*', '', text)
    text = re.sub(r'\[Thai\]\s*=?\s*\w*', '', text)
    text = re.sub(r'\[Kambodian\]\s*=?\s*\w*', '', text)
    text = re.sub(r'\[MS\]\s*\.?\s*\w*', '', text)
    # Remove + and - markers used for additions/deletions
    text = re.sub(r'\s*\+\s*', ' ', text)
    return text


def clean_bjt_text(html_content: str) -> str:
    """Master cleaning function: HTML -> clean Pali text."""
    # Step 1: Extract content chunk
    text = extract_content_chunk(html_content)

    # Step 2-3: Decode entities and strip HTML
    text = strip_html(text)

    # Step 4: Remove variant apparatus (AN_I has a huge one)
    text = remove_variant_apparatus(text)

    # Step 5: Remove formatting codes
    text = remove_formatting_codes(text)

    # Step 6: Remove page/volume markers
    text = remove_page_markers(text)

    # Step 7: Remove footnote lines
    lines = text.split('\n')
    lines = [line for line in lines if not is_footnote_line(line)]
    text = '\n'.join(lines)

    # Step 8: Remove inline footnote fragments within text
    text = remove_inline_footnotes(text)

    # Step 9: Remove inline footnote reference numbers
    text = remove_inline_footnote_refs(text)

    # Step 10: Normalize whitespace
    text = text.replace('\u00a0', ' ')  # &nbsp; -> space
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)

    return text.strip()


# ==================== File Parsing ====================

def parse_file(filepath: Path, collection: str, name: str) -> dict | None:
    """Parse a single BJT HTML file and return cleaned data."""
    if not filepath.exists():
        return None

    html_content = filepath.read_text(encoding='utf-8', errors='ignore')
    text = clean_bjt_text(html_content)

    return {
        'collection': collection,
        'name': name,
        'source_file': filepath.name,
        'text': text,
        'word_count': len(text.split()),
    }


# ==================== Nikaya Parsers ====================

ROMAN_NUMERALS = [
    ('I', 1), ('II', 2), ('III', 3), ('IV', 4), ('V', 5), ('VI', 6),
]


def parse_volumes(code: str, label: str, num_volumes: int) -> dict:
    """Parse a multi-volume nikaya (DN, MN, SN, or AN)."""
    print(f"\n{code.upper()} ({label}):")
    output_dir = OUTPUT_DIR / code
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for roman, vol_num in ROMAN_NUMERALS[:num_volumes]:
        filepath = BJT_DIR / f"{code.upper()}_{roman}_utf8.html"
        data = parse_file(filepath, code, f'vol{vol_num}')
        if data:
            data['volume'] = vol_num
            output_file = output_dir / f"{code}_vol{vol_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Vol {vol_num}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  Vol {vol_num}: FILE NOT FOUND")

    summary = {
        'nikaya': code.upper(),
        'source': 'BJT',
        'volumes': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Total: {total_words:,} words")
    return summary


def parse_kn() -> dict:
    """Parse Khuddaka Nikaya texts."""
    print("\n" + "=" * 60)
    print("KHUDDAKA NIKAYA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "kn"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    # Single-file texts
    for prefix, (output_name, title) in KN_SINGLE.items():
        filepath = BJT_DIR / f"{prefix}_utf8.html"
        data = parse_file(filepath, 'kn', output_name)
        if data:
            data['title'] = title
            output_file = output_dir / f"{output_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND")

    # Jataka (6 volumes)
    for roman, vol_num in ROMAN_NUMERALS[:6]:
        filepath = BJT_DIR / f"J_{roman}_utf8.html"
        title = f'Jātaka Vol {vol_num}'
        data = parse_file(filepath, 'kn', f'jataka{vol_num}')
        if data:
            data['title'] = title
            output_file = output_dir / f"jataka{vol_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    # Niddesa: Nidd_I -> mahaniddesa, Nidd_II -> cullaniddesa
    for roman, name, title in [('I', 'mahaniddesa', 'Mahāniddesa'),
                                ('II', 'cullaniddesa', 'Cūḷaniddesa')]:
        filepath = BJT_DIR / f"Nidd_{roman}_utf8.html"
        data = parse_file(filepath, 'kn', name)
        if data:
            data['title'] = title
            output_file = output_dir / f"{name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    # Patisambhidamagga (2 volumes)
    for roman, vol_num in [('I', 1), ('II', 2)]:
        filepath = BJT_DIR / f"Patis_{roman}_utf8.html"
        title = f'Paṭisambhidāmagga Vol {vol_num}'
        data = parse_file(filepath, 'kn', f'patisambhidamagga{vol_num}')
        if data:
            data['title'] = title
            output_file = output_dir / f"patisambhidamagga{vol_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    # Apadana (2 volumes)
    for roman, vol_num in [('I', 1), ('II', 2)]:
        filepath = BJT_DIR / f"Ap_{roman}_utf8.html"
        title = f'Apadāna Vol {vol_num}'
        data = parse_file(filepath, 'kn', f'apadana{vol_num}')
        if data:
            data['title'] = title
            output_file = output_dir / f"apadana{vol_num}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']

    summary = {
        'nikaya': 'Khuddaka',
        'source': 'BJT',
        'texts': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


# ==================== Vinaya Parser ====================

# BJT Vinaya volumes -> GRETIL text names
VINAYA_VOLUMES = [
    ('I', 'suttavibhanga1', 'Suttavibhaṅga I (Pārājika)'),
    ('II', 'suttavibhanga2', 'Suttavibhaṅga II (Pācittiya)'),
    ('III', 'parivara', 'Parivāra'),
    ('IV', 'mahavagga', 'Mahāvagga'),
    ('V', 'cullavagga', 'Cūḷavagga'),
]


def parse_vinaya() -> dict:
    """Parse Vinaya Pitaka BJT files."""
    print("\n" + "=" * 60)
    print("VINAYA PITAKA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "vinaya"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for roman, name, title in VINAYA_VOLUMES:
        filepath = BJT_DIR / f"vinaya/Vin_{roman}_utf8.html"
        data = parse_file(filepath, 'vinaya', name)
        if data:
            data['title'] = title
            output_file = output_dir / f"{name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND")

    summary = {
        'pitaka': 'Vinaya',
        'source': 'BJT',
        'texts': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


# ==================== Abhidhamma Parser ====================

# BJT Abhidhamma files -> GRETIL text names
ABHIDHAMMA_FILES = [
    ('Dhs', 'dhammasangani', 'Dhammasaṅgaṇī'),
    ('Vibh', 'vibhanga', 'Vibhaṅga'),
    ('Dhatuk', 'dhatukatha', 'Dhātukathā'),
    ('Kv_I', 'kathavatthu1', 'Kathāvatthu I'),
    ('Kv_II', 'kathavatthu2', 'Kathāvatthu II'),
    ('Yam_I', 'yamaka1', 'Yamaka I'),
    ('Yam_II', 'yamaka2', 'Yamaka II'),
    ('Patth_I', 'patthana1', 'Paṭṭhāna I'),
    ('Patth_II', 'patthana2', 'Paṭṭhāna II'),
]


def parse_abhidhamma() -> dict:
    """Parse Abhidhamma Pitaka BJT files."""
    print("\n" + "=" * 60)
    print("ABHIDHAMMA PITAKA")
    print("=" * 60)

    output_dir = OUTPUT_DIR / "abhidhamma"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_words = 0

    for bjt_name, output_name, title in ABHIDHAMMA_FILES:
        filepath = BJT_DIR / f"abhidhamma/{bjt_name}_utf8.html"
        data = parse_file(filepath, 'abhidhamma', output_name)
        if data:
            data['title'] = title
            output_file = output_dir / f"{output_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {title}: {data['word_count']:,} words")
            results.append(data)
            total_words += data['word_count']
        else:
            print(f"  {title}: FILE NOT FOUND")

    summary = {
        'pitaka': 'Abhidhamma',
        'source': 'BJT',
        'texts': len(results),
        'total_words': total_words,
    }
    with open(output_dir / "_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  TOTAL: {total_words:,} words")
    return summary


# ==================== Main ====================

def main():
    print("=" * 60)
    print("PARSING BJT (BUDDHA JAYANTI TIPITAKA)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    import sys
    results = {}

    # Determine which piṭakas to parse
    targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {'vinaya', 'sutta', 'abhidhamma'}

    # Vinaya Pitaka
    if 'vinaya' in targets:
        results['vinaya'] = parse_vinaya()

    # Sutta Pitaka
    if 'sutta' in targets:
        print("\n" + "=" * 60)
        print("SUTTA PITAKA")
        print("=" * 60)

        results['dn'] = parse_volumes('dn', 'Dīgha Nikāya', 3)
        results['mn'] = parse_volumes('mn', 'Majjhima Nikāya', 3)
        results['sn'] = parse_volumes('sn', 'Saṃyutta Nikāya', 5)
        results['an'] = parse_volumes('an', 'Aṅguttara Nikāya', 5)
        results['kn'] = parse_kn()

    # Abhidhamma Pitaka
    if 'abhidhamma' in targets:
        results['abhidhamma'] = parse_abhidhamma()

    # Calculate totals
    total_words = sum(r.get('total_words', 0) for r in results.values())

    print("\n" + "=" * 60)
    print("BJT PARSING SUMMARY")
    print("=" * 60)
    for key, r in results.items():
        label = key.upper()
        print(f"  {label:15s}: {r.get('total_words', 0):>10,} words")
    print(f"{'─' * 35}")
    print(f"  TOTAL: {total_words:>8,} words")

    return results


if __name__ == "__main__":
    main()
