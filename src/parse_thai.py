#!/usr/bin/env python3
"""
Parse the Thai Royal Edition (Syām Raṭṭha) from E-Tipitaka SQLite database.

Extracts Pāli text in Thai script, transliterates to Roman script,
and saves as JSON files matching our standard parsed format.

Source: E-Tipitaka pali.sqlite (45-volume Syām Raṭṭha edition)
"""

import json
import re
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
THAI_DB = DATA_DIR / "thai-raw" / "pali.sqlite"
OUTPUT_DIR = DATA_DIR / "thai-parsed"

# ============================================================
# Thai → Roman Pāli Transliteration
# ============================================================

# Consonants: each Thai character maps to one Roman consonant/cluster
THAI_CONSONANTS = {
    '\u0E01': 'k',    # ก
    '\u0E02': 'kh',   # ข
    '\u0E04': 'g',    # ค
    '\u0E06': 'gh',   # ฆ
    '\u0E07': 'ṅ',    # ง
    '\u0E08': 'c',    # จ
    '\u0E09': 'ch',   # ฉ
    '\u0E0A': 'j',    # ช
    '\u0E0C': 'jh',   # ฌ
    '\u0E0D': 'ñ',    # ญ
    '\u0E0F': 'ṭ',    # ฏ
    '\u0E10': 'ṭh',   # ฐ
    '\u0E11': 'ḍ',    # ฑ
    '\u0E12': 'ḍh',   # ฒ
    '\u0E13': 'ṇ',    # ณ
    '\u0E15': 't',    # ต
    '\u0E16': 'th',   # ถ
    '\u0E17': 'd',    # ท
    '\u0E18': 'dh',   # ธ
    '\u0E19': 'n',    # น
    '\u0E1B': 'p',    # ป
    '\u0E1C': 'ph',   # ผ
    '\u0E1E': 'b',    # พ
    '\u0E20': 'bh',   # ภ
    '\u0E21': 'm',    # ม
    '\u0E22': 'y',    # ย
    '\u0E23': 'r',    # ร
    '\u0E25': 'l',    # ล
    '\u0E2C': 'ḷ',    # ฬ
    '\u0E27': 'v',    # ว
    '\u0E2A': 's',    # ส
    '\u0E2B': 'h',    # ห
}

VOWEL_CARRIER = '\u0E2D'  # อ — used at word-initial for vowels

# Dependent vowel signs (combining, appear after consonant in Unicode stream)
VOWEL_SIGNS_AFTER = {
    '\u0E32': 'ā',    # า
    '\u0E34': 'i',    # ิ
    '\u0E35': 'ī',    # ี
    '\u0E38': 'u',    # ุ
    '\u0E39': 'ū',    # ู
}

# Vowel signs that appear BEFORE the consonant in Thai script
VOWEL_SIGNS_BEFORE = {
    '\u0E40': 'e',    # เ
    '\u0E42': 'o',    # โ
}

PHINTHU = '\u0E3A'    # ◌ฺ — virama, suppresses inherent 'a'
NIKKHAHIT = '\u0E4D'  # ◌ํ — niggahīta/anusvāra → ṃ

# Combined iṃ ligature
SARA_UE = '\u0E36'    # ึ — represents iṃ in Pāli context

# Tone marks (not used in Pāli, strip if found)
TONE_MARKS = {'\u0E48', '\u0E49', '\u0E4A', '\u0E4B'}

# Thanthakhat (silent marker, strip)
THANTHAKHAT = '\u0E4C'  # ์

# Thai digits
THAI_DIGITS = {
    '๐': '0', '๑': '1', '๒': '2', '๓': '3', '๔': '4',
    '๕': '5', '๖': '6', '๗': '7', '๘': '8', '๙': '9',
}

# PUA normalization (font-specific glyphs)
PUA_MAP = {
    '\uF70F': '\u0E0D',  # → ญ
    '\uF700': '\u0E10',  # → ฐ
}

# All characters we recognize
ALL_CONSONANTS = set(THAI_CONSONANTS.keys()) | {VOWEL_CARRIER}
ALL_VOWEL_SIGNS = set(VOWEL_SIGNS_AFTER.keys()) | set(VOWEL_SIGNS_BEFORE.keys())


def normalize_thai(text):
    """Pre-process Thai text before transliteration."""
    # Replace PUA characters
    for pua, standard in PUA_MAP.items():
        text = text.replace(pua, standard)
    # Normalize ฎ → ฏ (common typo)
    text = text.replace('\u0E0E', '\u0E0F')
    # Decompose sara ue (ึ) → sara i + nikkhahit (ิ + ํ)
    text = text.replace(SARA_UE, '\u0E34\u0E4D')
    # Strip tone marks
    for tm in TONE_MARKS:
        text = text.replace(tm, '')
    # Strip thanthakhat
    text = text.replace(THANTHAKHAT, '')
    return text


def transliterate_thai_to_roman(text):
    """Transliterate Thai-script Pāli to Roman script with diacritics."""
    text = normalize_thai(text)
    result = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Pre-positioned vowel (เ, โ): appears before consonant in Thai
        if ch in VOWEL_SIGNS_BEFORE:
            vowel = VOWEL_SIGNS_BEFORE[ch]
            i += 1
            # Next should be a consonant (or vowel carrier)
            if i < n and (text[i] in ALL_CONSONANTS):
                cons_char = text[i]
                if cons_char == VOWEL_CARRIER:
                    # เอ = e, โอ = o (just the vowel)
                    result.append(vowel)
                    i += 1
                elif cons_char in THAI_CONSONANTS:
                    cons = THAI_CONSONANTS[cons_char]
                    i += 1
                    # Check for phinthu after this consonant (consonant cluster)
                    # e.g., เกฺ would be unusual but handle it
                    if i < n and text[i] == PHINTHU:
                        result.append(cons)
                        i += 1
                        # The vowel applies to the next consonant
                        # Push vowel back for later
                        result.append(vowel)
                    else:
                        result.append(cons + vowel)
                else:
                    result.append(vowel)
            else:
                result.append(vowel)
            continue

        # Vowel carrier (อ)
        if ch == VOWEL_CARRIER:
            i += 1
            # Check what follows
            if i < n and text[i] in VOWEL_SIGNS_AFTER:
                result.append(VOWEL_SIGNS_AFTER[text[i]])
                i += 1
                # Check for nikkhahit after vowel
                if i < n and text[i] == NIKKHAHIT:
                    result.append('ṃ')
                    i += 1
            elif i < n and text[i] == NIKKHAHIT:
                result.append('aṃ')
                i += 1
            else:
                result.append('a')
            continue

        # Regular consonant
        if ch in THAI_CONSONANTS:
            cons = THAI_CONSONANTS[ch]
            i += 1

            # Check what follows the consonant
            if i < n and text[i] == PHINTHU:
                # Virama: consonant has no inherent vowel
                result.append(cons)
                i += 1
            elif i < n and text[i] in VOWEL_SIGNS_AFTER:
                vowel = VOWEL_SIGNS_AFTER[text[i]]
                result.append(cons + vowel)
                i += 1
                # Check for nikkhahit after vowel sign
                if i < n and text[i] == NIKKHAHIT:
                    result.append('ṃ')
                    i += 1
            elif i < n and text[i] == NIKKHAHIT:
                # Consonant + nikkhahit: inherent 'a' + ṃ
                result.append(cons + 'aṃ')
                i += 1
            else:
                # Consonant with inherent 'a'
                result.append(cons + 'a')
            continue

        # Thai digits
        if ch in THAI_DIGITS:
            result.append(THAI_DIGITS[ch])
            i += 1
            continue

        # Thai punctuation
        if ch == '\u0E2F':  # ฯ paiyannoi
            result.append('.')
            i += 1
            continue
        if ch == '\u0E5A':  # ๚ angkhankhu
            result.append('.')
            i += 1
            continue
        if ch == '\u0E5B':  # ๛ khomut
            i += 1
            continue

        # Pass through spaces, newlines, ASCII, punctuation as-is
        result.append(ch)
        i += 1

    return ''.join(result)


def tokenize_pali(text):
    """Count Pāli words in romanized text."""
    return re.findall(r'[a-zāīūṭḍṇṅñṃḷ]+', text.lower())


# ============================================================
# Volume → Text Mapping (45-volume Royal Thai scheme)
#
# The Royal Thai (Syām Raṭṭha) edition uses a 45-volume layout
# that differs from both the PTS and CST/VRI numbering:
#   Vols  1-8:  Vinaya (8 volumes)
#   Vols  9-11: DN (3 volumes)
#   Vols 12-14: MN (3 volumes)
#   Vols 15-19: SN (5 volumes)
#   Vols 20-24: AN (5 volumes, some nipātas combined)
#   Vols 25-33: KN (9 volumes, some texts combined)
#   Vols 34-45: Abhidhamma (12 volumes)
# ============================================================

# Vinaya: volumes 1-8
VINAYA_VOLUMES = {
    'suttavibhanga1': [1, 2],   # Mahāvibhaṅga pts 1-2
    'suttavibhanga2': [3],      # Bhikkhunīvibhaṅga
    'mahavagga': [4, 5],        # Mahāvagga pts 1-2
    'cullavagga': [6, 7],       # Cūḷavagga pts 1-2
    'parivara': [8],            # Parivāra
}

# DN: volumes 9-11
DN_VOLUMES = {
    'dn_vol1': [9],    # Sīlakkhandhavagga
    'dn_vol2': [10],   # Mahāvagga
    'dn_vol3': [11],   # Pāthikavagga
}

# MN: volumes 12-14
MN_VOLUMES = {
    'mn_vol1': [12],   # Mūlapaṇṇāsa
    'mn_vol2': [13],   # Majjhimapaṇṇāsa
    'mn_vol3': [14],   # Uparipaṇṇāsa
}

# SN: volumes 15-19
SN_VOLUMES = {
    'sn_vol1': [15],   # Sagāthāvagga
    'sn_vol2': [16],   # Nidānavagga
    'sn_vol3': [17],   # Khandhavagga
    'sn_vol4': [18],   # Saḷāyatanavagga
    'sn_vol5': [19],   # Mahāvagga
}

# AN: volumes 20-24 (some nipātas combined into single volumes)
AN_VOLUMES = {
    'an_vol1': [20],   # Eka+Duka+Tikanipāta
    'an_vol2': [21],   # Catukkanipāta
    'an_vol3': [22],   # Pañcakanipāta
    'an_vol4': [23],   # Chakka+Sattakanipāta
    'an_vol5': [24],   # Aṭṭhaka+Navaka+Dasaka+Ekādasakanipāta
}

# KN: volumes 25-33 (some texts combined)
KN_VOLUMES = {
    'kn_minor': [25],        # Khuddakapāṭha + Dhp + Ud + Iti + Snp
    'kn_verse': [26],        # Vimānavatthu + Pv + Thag + Thig
    'ja': [27, 28],          # Jātaka pts 1-2
    'mnd': [29],             # Mahāniddesa
    'cnd': [30],             # Cūḷaniddesa
    'ps': [31],              # Paṭisambhidāmagga
    'ap': [32, 33],          # Apadāna pts 1-2 (+ Bv + Cp in vol 33)
}

# Abhidhamma: volumes 34-45
ABHIDHAMMA_VOLUMES = {
    'dhammasangani': [34],             # Dhammasaṅgaṇī
    'vibhanga': [35],                  # Vibhaṅga
    'dhatukatha_puggalapannatti': [36], # Dhātukathā + Puggalapaññatti
    'kathavatthu': [37],               # Kathāvatthu
    'yamaka': [38, 39],                # Yamaka pts 1-2
    'patthana': [40, 41, 42, 43, 44, 45],  # Paṭṭhāna pts 1-6
}


def extract_text_from_volumes(db_path, volumes):
    """Extract and transliterate text from specified volumes."""
    conn = sqlite3.connect(db_path)
    all_text = []

    for vol in volumes:
        vol_str = f'{vol:02d}'
        cursor = conn.execute(
            "SELECT content FROM main WHERE volume = ? ORDER BY CAST(page AS INTEGER)",
            (vol_str,)
        )
        rows = cursor.fetchall()
        if not rows:
            print(f"WARNING: No data found for volume {vol_str}")
        for row in rows:
            content = row[0]
            if content:
                # Clean formatting artifacts
                content = content.replace('\t', ' ')
                content = re.sub(r'\s+', ' ', content)
                all_text.append(content.strip())

    conn.close()

    # Join all pages and transliterate
    thai_text = ' '.join(all_text)
    roman_text = transliterate_thai_to_roman(thai_text)

    return thai_text, roman_text


def process_collection(name, volume_map, db_path, output_dir):
    """Process a collection (vinaya, dn, etc.) and save JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    total_words = 0
    results = {}

    for text_name, volumes in volume_map.items():
        print(f"  {text_name} (vol {volumes})...", end=' ', flush=True)

        thai_text, roman_text = extract_text_from_volumes(db_path, volumes)
        words = tokenize_pali(roman_text)
        word_count = len(words)
        total_words += word_count

        output = {
            'source': 'thai',
            'edition': 'Syām Raṭṭha (Royal Thai Edition)',
            'text_id': text_name,
            'volumes': volumes,
            'text': roman_text,
            'word_count': word_count,
        }

        output_file = output_dir / f"{text_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False)

        results[text_name] = word_count
        print(f"{word_count:,} words")

    return results, total_words


def main():
    if not THAI_DB.exists():
        print(f"Database not found: {THAI_DB}")
        print("Copy pali.sqlite from E-Tipitaka to data/thai-raw/pali.sqlite")
        return

    print("=" * 60)
    print("Parsing Thai Royal Edition (Syām Raṭṭha)")
    print("=" * 60)
    print()

    grand_total = 0

    # Vinaya
    print("VINAYA PIṬAKA")
    vinaya_dir = OUTPUT_DIR / "vinaya"
    results, total = process_collection("vinaya", VINAYA_VOLUMES, THAI_DB, vinaya_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # DN
    print("DĪGHA NIKĀYA")
    dn_dir = OUTPUT_DIR / "dn"
    results, total = process_collection("dn", DN_VOLUMES, THAI_DB, dn_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # MN
    print("MAJJHIMA NIKĀYA")
    mn_dir = OUTPUT_DIR / "mn"
    results, total = process_collection("mn", MN_VOLUMES, THAI_DB, mn_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # SN
    print("SAṂYUTTA NIKĀYA")
    sn_dir = OUTPUT_DIR / "sn"
    results, total = process_collection("sn", SN_VOLUMES, THAI_DB, sn_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # AN
    print("AṄGUTTARA NIKĀYA")
    an_dir = OUTPUT_DIR / "an"
    results, total = process_collection("an", AN_VOLUMES, THAI_DB, an_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # KN
    print("KHUDDAKA NIKĀYA")
    kn_dir = OUTPUT_DIR / "kn"
    results, total = process_collection("kn", KN_VOLUMES, THAI_DB, kn_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    # Abhidhamma
    print("ABHIDHAMMA PIṬAKA")
    abh_dir = OUTPUT_DIR / "abhidhamma"
    results, total = process_collection("abhidhamma", ABHIDHAMMA_VOLUMES, THAI_DB, abh_dir)
    print(f"  Total: {total:,} words\n")
    grand_total += total

    print("=" * 60)
    print(f"GRAND TOTAL: {grand_total:,} words")
    print("=" * 60)


if __name__ == '__main__':
    main()
