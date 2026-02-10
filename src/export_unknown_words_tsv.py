#!/usr/bin/env python3
"""
Export enriched TSV of unknown words for DPD contribution.

Generates a TSV with:
- word: the unknown word form
- category: classification (potential_headword, metrical_variant, sandhi_ending, etc.)
- inferred_pos: POS guess from word endings
- total_count: total occurrences across entire canon
- dn_count, mn_count, sn_count, an_count, kn_count: per-collection counts
- nikaya_count: DN+MN+SN+AN combined
- text_count: number of distinct texts containing the word
- all_texts: semicolon-separated list of all text references
- sample_context: a short Pāli phrase showing the word in context
- dpd_feedback: blank column for Bodhirasa to fill in
"""

import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
OUTPUT_DIR = DATA_DIR / "unknown_words_report"

COLLECTIONS = ['dn', 'mn', 'sn', 'an', 'kn']

# POS inference rules (from export_unknown_words_detailed.py)
POS_RULES = [
    (r'(ati|eti|oti)$', 'verb (present 3sg)'),
    (r'(āmi|emi|omi)$', 'verb (present 1sg)'),
    (r'(āma|ema|oma)$', 'verb (present 1pl)'),
    (r'(anti|enti|onti)$', 'verb (present 3pl)'),
    (r'(issati|essati)$', 'verb (future 3sg)'),
    (r'(issāmi|essāmi)$', 'verb (future 1sg)'),
    (r'(ittha|ettha)$', 'verb (aorist 3sg)'),
    (r'(iṃsu|uṃ)$', 'verb (aorist 3pl)'),
    (r'(eyya|eyyaṃ)$', 'verb (optative)'),
    (r'(atu|antu|etu)$', 'verb (imperative)'),
    (r'(māna|āna)$', 'verb (present participle)'),
    (r'(ita|ina|ta)$', 'pp (past participle)'),
    (r'tabba$', 'fpp (future passive participle)'),
    (r'(tuṃ|tave)$', 'infinitive'),
    (r'assa$', 'noun (gen sg)'),
    (r'ānaṃ$', 'noun (gen pl)'),
    (r'ehi$', 'noun (inst pl)'),
    (r'esu$', 'noun (loc pl)'),
    (r'ena$', 'noun (inst sg)'),
    (r'āya$', 'noun (dat sg)'),
    (r'asmiṃ$', 'noun (loc sg)'),
    (r'amhi$', 'noun (loc sg)'),
    (r'āsu$', 'noun (loc pl, fem)'),
    (r'āhi$', 'noun (inst pl, fem)'),
    (r'tara$', 'adj (comparative)'),
    (r'tama$', 'adj (superlative)'),
    (r'ika$', 'adj (-ika suffix)'),
    (r'iya$', 'adj (-iya suffix)'),
    (r'vantu$', 'adj (possessive -vantu)'),
    (r'mantu$', 'adj (possessive -mantu)'),
    (r'vatthu$', 'noun (story title)'),
    (r'vaggo$', 'noun (chapter title)'),
    (r'sutta$', 'noun (sutta title)'),
    (r'jhāna', 'noun (jhāna compound)'),
    (r'(pi|pī|ca|vā|tu|va)$', 'particle (possible sandhi)'),
]

# Pronoun-verb fusion patterns
PRONOUN_VERB_PATTERNS = [
    r'ohama$', r'ohaṃ$', r'āmhā$', r'amhā$',
    r'āmī$', r'āmā$', r'osmi$', r'asmi$', r'amhi$',
]


def infer_pos(word):
    for pattern, pos in POS_RULES:
        if re.search(pattern, word):
            return pos
    return ''


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


def extract_context(seg_pali, word, max_len=120):
    """Extract a short context snippet around the word."""
    # Strip HTML tags
    seg_pali = re.sub(r'<[^>]+>', '', seg_pali)
    # Find the word in the Pāli text
    idx = seg_pali.lower().find(word.lower())
    if idx == -1:
        # Fallback: return truncated segment
        if len(seg_pali) <= max_len:
            return seg_pali
        return seg_pali[:max_len] + '…'

    # Get a window around the word
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
                if word and not tok.get('lemma') and not tok.get('sandhi'):
                    info = unknown_words[word]
                    info['total_count'] += 1
                    info['collection_counts'][collection] += 1

                    text_ref = f"{collection.upper()}:{text_id}"
                    info['text_refs'].add(text_ref)

                    full_ref = f"{text_ref}:{seg_id}"
                    info['full_refs'].append(full_ref)

                    # Capture first context snippet
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
    # If it contains tabs or newlines, quote it
    if '\t' in s or '\n' in s or '\r' in s:
        s = s.replace('"', '""')
        s = f'"{s}"'
    return s


def main():
    print("=" * 70)
    print("EXPORTING ENRICHED UNKNOWN WORDS TSV FOR DPD")
    print("=" * 70)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
            continue
        print(f"Processing {coll.upper()}...")
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
    nikaya_total = 0
    kn_total = 0
    for word, info in sorted_words:
        nik = sum(info['collection_counts'][c] for c in ['dn', 'mn', 'sn', 'an'])
        nikaya_total += nik
        kn_total += info['collection_counts']['kn']

    print(f"Nikāya (DN+MN+SN+AN) occurrences: {nikaya_total}")
    print(f"Khuddaka Nikāya occurrences: {kn_total}")
    print()

    # Write TSV
    headers = [
        'word',
        'category',
        'inferred_pos',
        'total_count',
        'dn_count',
        'mn_count',
        'sn_count',
        'an_count',
        'kn_count',
        'nikaya_count',
        'text_count',
        'all_texts',
        'sample_context',
        'dpd_feedback',
    ]

    tsv_file = OUTPUT_DIR / "unknown_words_for_dpd.tsv"
    with open(tsv_file, 'w', encoding='utf-8') as f:
        f.write('\t'.join(headers) + '\n')

        for word, info in sorted_words:
            cc = info['collection_counts']
            nik_count = cc['dn'] + cc['mn'] + cc['sn'] + cc['an']
            texts_sorted = sorted(info['text_refs'])

            row = [
                word,
                categorize_word(word),
                infer_pos(word),
                str(info['total_count']),
                str(cc['dn']),
                str(cc['mn']),
                str(cc['sn']),
                str(cc['an']),
                str(cc['kn']),
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
    print(f"  {'word':<30} {'cat':<20} {'total':>5} {'nik':>4} {'kn':>4} {'texts':>5}")
    print("  " + "-" * 75)
    for word, info in sorted_words[:20]:
        cc = info['collection_counts']
        nik = cc['dn'] + cc['mn'] + cc['sn'] + cc['an']
        print(f"  {word:<30} {categorize_word(word):<20} {info['total_count']:>5} {nik:>4} {cc['kn']:>4} {len(info['text_refs']):>5}")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
