#!/usr/bin/env python3
"""
Export enriched TSV of unknown words for DPD contribution.

Generates a TSV with:
- word: the unknown word form
- category: classification (potential_headword, metrical_variant, sandhi_ending, etc.)
- inferred_pos: POS guess from word endings
- suggested_lemma: closest DPD headword found via normalization heuristics
- suggested_meaning: meaning of the suggested lemma
- suggested_method: how we found the suggestion (metrical, sandhi_strip, prefix, etc.)
- total_count: total occurrences across entire canon
- per-collection counts (dn, mn, sn, an, kn, vinaya, abhidhamma)
- nikaya_count: DN+MN+SN+AN combined
- text_count: number of distinct texts containing the word
- all_texts: semicolon-separated list of all text references
- sample_context: a short Pāli phrase showing the word in context
- dpd_feedback: blank column for Bodhirasa to fill in
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

# Allow importing sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from export_unknown_words_detailed import POS_RULES, infer_pos
from dpd_lookup import DPD

DATA_DIR = Path(__file__).parent.parent / "data"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
WORK_DIR = Path(__file__).parent.parent / "work"

COLLECTIONS = ['dn', 'mn', 'sn', 'an', 'kn', 'vinaya', 'abhidhamma']

# Pronoun-verb fusion patterns
PRONOUN_VERB_PATTERNS = [
    r'ohama$', r'ohaṃ$', r'āmhā$', r'amhā$',
    r'āmī$', r'āmā$', r'osmi$', r'asmi$', r'amhi$',
]

# Metrical lengthening: long → short final vowel
METRICAL_MAP = {'ā': 'a', 'ī': 'i', 'ū': 'u'}

# Common sandhi suffixes to try stripping
SANDHI_SUFFIXES = [
    ('ti', 'quotation marker -ti'),
    ('tī', 'quotation marker -tī'),
    ('pi', 'particle -pi'),
    ('pī', 'particle -pī'),
    ('ca', 'particle -ca'),
    ('va', 'particle -va'),
    ('vā', 'particle -vā'),
    ('ssa', 'genitive -ssa'),
    ('ṃ', 'niggahīta -ṃ'),
    ('n', 'sandhi -n'),
]

# English words that sometimes leak through from source metadata
ENGLISH_SKIP = {
    'chapter', 'section', 'the', 'of', 'and', 'on', 'in', 'is', 'to',
    'for', 'display', 'title', 'only', 'not', 'available',
}


def categorize_word(word):
    if len(word) <= 2:
        return 'ocr_error'
    for pattern in PRONOUN_VERB_PATTERNS:
        if re.search(pattern, word):
            return 'pronoun_verb_fusion'
    if len(word) > 25:
        return 'long_compound'
    if word[-1] in 'āīū' and len(word) > 4:
        return 'metrical_variant'
    if word.endswith('n') or word.endswith('ṃ'):
        return 'sandhi_ending'
    if 'jhāna' in word:
        return 'jhana_compound'
    if word.endswith('vatthu'):
        return 'story_title'
    return 'potential_headword'


def suggest_lemma(word, dpd):
    """
    Try various normalizations to find a plausible DPD match.
    Returns (lemma, meaning, method) or ('', '', '').
    """
    # 1. Try metrical normalization (shorten final vowel)
    if len(word) > 3 and word[-1] in METRICAL_MAP:
        normalized = word[:-1] + METRICAL_MAP[word[-1]]
        result = dpd.lookup(normalized)
        if result.entries:
            e = result.entries[0]
            return e.lemma, e.meaning, f'metrical: {normalized}'
        # Also try the shortened form as a lookup
        if result.deconstructor:
            return '', ' + '.join(result.deconstructor), f'metrical+sandhi: {normalized}'

    # 2. Try stripping common sandhi suffixes
    for suffix, desc in SANDHI_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            base = word[:-len(suffix)]
            result = dpd.lookup(base)
            if result.entries:
                e = result.entries[0]
                return e.lemma, e.meaning, f'strip {desc}: {base}'
            if result.deconstructor:
                return '', ' + '.join(result.deconstructor), f'strip {desc}+sandhi: {base}'
            # Try with metrical normalization on the base too
            if len(base) > 3 and base[-1] in METRICAL_MAP:
                base2 = base[:-1] + METRICAL_MAP[base[-1]]
                result2 = dpd.lookup(base2)
                if result2.entries:
                    e = result2.entries[0]
                    return e.lemma, e.meaning, f'strip {desc}+metrical: {base2}'

    # 3. Try DPD deconstructor on the raw word
    result = dpd.lookup(word)
    if result.deconstructor:
        return '', ' + '.join(result.deconstructor), 'deconstructor'

    # 4. Try prefix search for longest matching headword
    #    (useful for compounds: the first element is often a known word)
    if len(word) > 6:
        # Try splitting at various points
        for split_pos in range(len(word) - 3, 2, -1):
            prefix = word[:split_pos]
            result = dpd.lookup(prefix)
            if result.entries:
                e = result.entries[0]
                remainder = word[split_pos:]
                return e.lemma, e.meaning, f'prefix {prefix} + {remainder}'
                break

    return '', '', ''


def extract_context(seg_pali, word, max_len=120):
    """Extract a short context snippet around the word."""
    # Strip HTML tags
    seg_pali = re.sub(r'<[^>]+>', '', seg_pali)
    # Find the word in the Pāli text
    idx = seg_pali.lower().find(word.lower())
    if idx == -1:
        if len(seg_pali) <= max_len:
            return seg_pali
        return seg_pali[:max_len] + '…'

    start = max(0, idx - 30)
    end = min(len(seg_pali), idx + len(word) + 30)

    snippet = seg_pali[start:end].strip()
    if start > 0:
        snippet = '…' + snippet
    if end < len(seg_pali):
        snippet = snippet + '…'
    return snippet


def process_file(fpath, collection, unknown_words):
    """Process a lemmatized JSON file, collecting unknown words with context."""
    data = json.loads(fpath.read_text())
    file_id = fpath.stem

    def process_segments(segments, text_id):
        for seg in segments:
            seg_id = seg.get('id', '')
            seg_pali = seg.get('pali', '')
            for tok in seg.get('tokens', []):
                word = tok.get('word', '')
                if word and not tok.get('lemma') and not tok.get('sandhi') and word.lower() not in ENGLISH_SKIP:
                    info = unknown_words[word]
                    info['total_count'] += 1
                    info['collection_counts'][collection] += 1

                    text_ref = f"{collection.upper()}:{text_id}"
                    info['text_refs'].add(text_ref)

                    full_ref = f"{text_ref}:{seg_id}"
                    info['full_refs'].append(full_ref)

                    if not info['context'] and seg_pali:
                        info['context'] = extract_context(seg_pali, word)

    if 'segments' in data:
        process_segments(data['segments'], file_id)
    elif 'suttas' in data:
        for sutta in data['suttas']:
            sutta_id = sutta.get('id', file_id)
            process_segments(sutta.get('segments', []), sutta_id)
    elif 'items' in data:
        for item in data['items']:
            item_id = item.get('id', file_id)
            process_segments(item.get('segments', []), item_id)


def tsv_escape(val):
    """Escape a value for TSV output."""
    s = str(val)
    if '\t' in s or '\n' in s or '\r' in s:
        s = s.replace('"', '""')
        s = f'"{s}"'
    return s


def main():
    print("=" * 70)
    print("EXPORTING ENRICHED UNKNOWN WORDS TSV FOR DPD")
    print("=" * 70)
    print()

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all unknown words
    unknown_words = defaultdict(lambda: {
        'total_count': 0,
        'collection_counts': defaultdict(int),
        'text_refs': set(),
        'full_refs': [],
        'context': '',
    })

    for coll in COLLECTIONS:
        coll_dir = LEMMATIZED_DIR / coll
        if not coll_dir.exists():
            print(f"  {coll.upper()}: not found, skipping")
            continue
        n_files = len(list(coll_dir.glob("*.json")))
        print(f"Processing {coll.upper()} ({n_files} files)...")
        for fpath in sorted(coll_dir.glob("*.json")):
            if fpath.name.startswith('_'):
                continue
            process_file(fpath, coll, unknown_words)

    print()
    print(f"Total unique unknown words: {len(unknown_words)}")
    total_occ = sum(info['total_count'] for info in unknown_words.values())
    print(f"Total occurrences: {total_occ}")

    # Sort by frequency descending, then alphabetically
    sorted_words = sorted(
        unknown_words.items(),
        key=lambda x: (-x[1]['total_count'], x[0])
    )

    # Collection breakdown summary
    for coll in COLLECTIONS:
        total = sum(info['collection_counts'][coll] for _, info in sorted_words)
        if total > 0:
            unique = sum(1 for _, info in sorted_words if info['collection_counts'][coll] > 0)
            print(f"  {coll.upper()}: {total} occurrences ({unique} unique)")

    nikaya_total = sum(
        sum(info['collection_counts'][c] for c in ['dn', 'mn', 'sn', 'an'])
        for _, info in sorted_words
    )
    print(f"  Nikāya total (DN+MN+SN+AN): {nikaya_total}")
    print()

    # Suggest lemmas using DPD
    print("Looking up suggested lemmas in DPD...")
    dpd = DPD()
    suggestions = {}
    found_count = 0
    for i, (word, info) in enumerate(sorted_words):
        lemma, meaning, method = suggest_lemma(word, dpd)
        suggestions[word] = (lemma, meaning, method)
        if lemma or meaning:
            found_count += 1
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(sorted_words)} processed...")
    dpd.close()
    print(f"  Suggestions found for {found_count}/{len(sorted_words)} words")
    print()

    # Write TSV
    headers = [
        'word',
        'category',
        'inferred_pos',
        'suggested_lemma',
        'suggested_meaning',
        'suggestion_method',
        'total_count',
        'dn_count',
        'mn_count',
        'sn_count',
        'an_count',
        'kn_count',
        'vin_count',
        'abh_count',
        'nikaya_count',
        'text_count',
        'all_texts',
        'sample_context',
        'dpd_feedback',
    ]

    tsv_file = WORK_DIR / "unknown_words_for_dpd.tsv"
    with open(tsv_file, 'w', encoding='utf-8') as f:
        f.write('\t'.join(headers) + '\n')

        for word, info in sorted_words:
            cc = info['collection_counts']
            nik_count = cc['dn'] + cc['mn'] + cc['sn'] + cc['an']
            texts_sorted = sorted(info['text_refs'])
            lemma, meaning, method = suggestions[word]

            row = [
                word,
                categorize_word(word),
                infer_pos(word),
                lemma,
                meaning,
                method,
                str(info['total_count']),
                str(cc['dn']),
                str(cc['mn']),
                str(cc['sn']),
                str(cc['an']),
                str(cc['kn']),
                str(cc['vinaya']),
                str(cc['abhidhamma']),
                str(nik_count),
                str(len(info['text_refs'])),
                '; '.join(texts_sorted),
                info['context'],
                '',  # blank for Bodhirasa
            ]

            f.write('\t'.join(tsv_escape(v) for v in row) + '\n')

    print(f"TSV written to: {tsv_file}")
    print(f"  {len(sorted_words)} rows")

    # Print top 20 for spot-check
    print()
    print("Top 20 by frequency:")
    print(f"  {'word':<30} {'cat':<18} {'total':>5} {'suggestion':<40}")
    print("  " + "-" * 90)
    for word, info in sorted_words[:20]:
        lemma, meaning, method = suggestions[word]
        suggestion = f"{lemma}: {meaning[:30]}" if lemma else (meaning[:40] if meaning else "")
        print(f"  {word:<30} {categorize_word(word):<18} {info['total_count']:>5} {suggestion:<40}")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
