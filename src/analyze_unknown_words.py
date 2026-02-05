#!/usr/bin/env python3
"""
Analyze unknown words from lemmatization to prepare a useful report for DPD.

Categories:
1. Likely OCR/encoding errors (single chars, odd patterns)
2. Metrical variants (metrically lengthened forms)
3. Pronoun-verb fusions (ahaṃ/amhi fused with verbs)
4. Long compounds (may need sandhi decomposition)
5. Case-ending variants
6. Potential new headwords
"""

import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"

# Common metrical lengthening patterns
METRICAL_PATTERNS = [
    (r'ā$', 'a'),  # final -ā → -a
    (r'ī$', 'i'),  # final -ī → -i
    (r'ū$', 'u'),  # final -ū → -u
]

# Pronoun-verb fusion patterns
PRONOUN_VERB_PATTERNS = [
    r'ohama$',      # -o + ahaṃ
    r'ohaṃ$',
    r'āmhā$',       # 1st person plural
    r'amhā$',
    r'āmī$',        # 1st person singular metrical
    r'āmā$',        # 1st person plural metrical
    r'osmi$',       # -o + asmi
    r'asmi$',
    r'amhi$',
]

# Common sandhi junction patterns
SANDHI_PATTERNS = [
    r'ṃc',   # -ṃ + ca
    r'ñc',   # -ṃ + ca (assimilated)
    r'mp',   # -ṃ + pa
    r'mb',   # -ṃ + ba
    r'nt',   # -n + ta
    r'nd',   # -n + da
]


def categorize_word(word):
    """Categorize an unknown word."""

    # Single character or very short - likely OCR error
    if len(word) <= 2:
        return 'ocr_error'

    # Check for pronoun-verb fusion
    for pattern in PRONOUN_VERB_PATTERNS:
        if re.search(pattern, word):
            return 'pronoun_verb_fusion'

    # Very long word - likely undecomposed compound
    if len(word) > 25:
        return 'long_compound'

    # Check for metrical lengthening at end
    if word[-1] in 'āīū' and len(word) > 4:
        return 'metrical_variant'

    # Check for sandhi with final -n or -ṃ patterns
    if word.endswith('n') or word.endswith('ṃ'):
        return 'sandhi_ending'

    # Likely jhāna compound (very common in meditation texts)
    if 'jhāna' in word:
        return 'jhana_compound'

    # Check for -vatthu suffix (story titles in Jātaka/Apadāna)
    if word.endswith('vatthu'):
        return 'story_title'

    # Otherwise potential new headword
    return 'potential_headword'


def main():
    print("=" * 70)
    print("ANALYSIS OF UNKNOWN WORDS FOR DPD CONTRIBUTION")
    print("=" * 70)
    print()

    # Load stats
    with open(DATA_DIR / "lemmatized/_stats.json") as f:
        stats = json.load(f)

    unknown = stats.get('unknown_words', [])

    print(f"Total unique unknown words: {len(unknown)}")
    print(f"(These represent {stats['words_not_found']:,} total occurrences)")
    print()

    # Categorize
    categories = defaultdict(list)
    for word, count in unknown:
        cat = categorize_word(word)
        categories[cat].append((word, count))

    # Print summary
    print("CATEGORY BREAKDOWN:")
    print("-" * 40)
    for cat, words in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(words)} words")
    print()

    # Detailed output by category
    output = {
        'summary': {
            'total_unknown': len(unknown),
            'total_occurrences': stats['words_not_found'],
            'categories': {cat: len(words) for cat, words in categories.items()}
        },
        'categories': {}
    }

    # OCR errors - probably not useful
    print("=" * 70)
    print("OCR/ENCODING ERRORS (not useful for DPD)")
    print("=" * 70)
    for word, count in categories.get('ocr_error', [])[:20]:
        print(f"  {word}")
    output['categories']['ocr_error'] = categories.get('ocr_error', [])
    print()

    # Pronoun-verb fusions - DPD may want to add these
    print("=" * 70)
    print("PRONOUN-VERB FUSIONS (common pattern, may be useful)")
    print("=" * 70)
    for word, count in categories.get('pronoun_verb_fusion', []):
        print(f"  {word}")
    output['categories']['pronoun_verb_fusion'] = categories.get('pronoun_verb_fusion', [])
    print()

    # Metrical variants
    print("=" * 70)
    print("METRICAL VARIANTS (lengthened vowels)")
    print("=" * 70)
    for word, count in categories.get('metrical_variant', [])[:30]:
        print(f"  {word}")
    output['categories']['metrical_variant'] = categories.get('metrical_variant', [])
    print()

    # Long compounds
    print("=" * 70)
    print("LONG COMPOUNDS (may need sandhi analysis)")
    print("=" * 70)
    for word, count in categories.get('long_compound', []):
        print(f"  {word}")
    output['categories']['long_compound'] = categories.get('long_compound', [])
    print()

    # Jhāna compounds
    print("=" * 70)
    print("JHĀNA COMPOUNDS")
    print("=" * 70)
    for word, count in categories.get('jhana_compound', []):
        print(f"  {word}")
    output['categories']['jhana_compound'] = categories.get('jhana_compound', [])
    print()

    # Story titles
    print("=" * 70)
    print("STORY TITLES (Jātaka/Apadāna)")
    print("=" * 70)
    for word, count in categories.get('story_title', []):
        print(f"  {word}")
    output['categories']['story_title'] = categories.get('story_title', [])
    print()

    # Potential new headwords - most interesting for DPD
    print("=" * 70)
    print("POTENTIAL NEW HEADWORDS (most useful for DPD)")
    print("=" * 70)
    potential = categories.get('potential_headword', [])
    for word, count in potential[:50]:
        print(f"  {word}")
    if len(potential) > 50:
        print(f"  ... and {len(potential) - 50} more")
    output['categories']['potential_headword'] = potential
    print()

    # Sandhi endings
    print("=" * 70)
    print("SANDHI ENDINGS (-n/-ṃ)")
    print("=" * 70)
    for word, count in categories.get('sandhi_ending', [])[:30]:
        print(f"  {word}")
    output['categories']['sandhi_ending'] = categories.get('sandhi_ending', [])
    print()

    # Save full analysis
    output_file = DATA_DIR / "dpd_unknown_words_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"Full analysis saved to: {output_file}")
    print()
    print("RECOMMENDATION:")
    print("The 'potential_headword' category contains words most likely")
    print("to be genuinely missing from DPD and worth reporting.")
    print()
    print("Contact: digitalpalidictionary@gmail.com")
    print("Or use the feedback form on dpdict.net")


if __name__ == "__main__":
    main()
