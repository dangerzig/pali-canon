#!/usr/bin/env python3
"""
Export detailed list of unknown words with:
- Word form
- Suggested POS (if determinable)
- All locations in the canon
- Frequency count
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
OUTPUT_DIR = DATA_DIR / "unknown_words_report"


# POS inference rules based on word endings
POS_RULES = [
    # Verbs
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

    # Nouns - masculine
    (r'assa$', 'noun (gen sg, masc -a stem)'),
    (r'ānaṃ$', 'noun (gen pl)'),
    (r'ehi$', 'noun (inst pl)'),
    (r'esu$', 'noun (loc pl)'),
    (r'ena$', 'noun (inst sg, masc -a stem)'),
    (r'āya$', 'noun (dat sg)'),
    (r'asmiṃ$', 'noun (loc sg, masc -a stem)'),
    (r'amhi$', 'noun (loc sg, masc -a stem)'),

    # Nouns - feminine
    (r'āya$', 'noun (dat/gen sg, fem -ā stem)'),
    (r'āsu$', 'noun (loc pl, fem)'),
    (r'āhi$', 'noun (inst pl, fem)'),

    # Adjectives
    (r'tara$', 'adj (comparative)'),
    (r'tama$', 'adj (superlative)'),
    (r'ika$', 'adj (-ika suffix)'),
    (r'iya$', 'adj (-iya suffix)'),
    (r'vantu$', 'adj (possessive -vantu)'),
    (r'mantu$', 'adj (possessive -mantu)'),

    # Compounds ending in common elements
    (r'vatthu$', 'noun (story title)'),
    (r'vaggo$', 'noun (chapter title)'),
    (r'sutta$', 'noun (sutta title)'),
    (r'jhāna', 'noun (jhāna compound)'),

    # Indeclinables
    (r'(pi|pī|ca|vā|tu|va)$', 'particle (possible sandhi)'),
]


def infer_pos(word):
    """Try to infer POS from word ending."""
    for pattern, pos in POS_RULES:
        if re.search(pattern, word):
            return pos
    return 'unknown'


def get_human_readable_location(seg_id):
    """Convert segment ID to human-readable location."""
    # Examples: dn1:1.1, mn1:1.1, sn1.1:1.1, an1.1:1.1, dhp1:1
    parts = seg_id.split(':')
    if len(parts) >= 1:
        text_id = parts[0]
        # Extract collection and number
        match = re.match(r'([a-z]+)(\d+)', text_id)
        if match:
            coll = match.group(1).upper()
            num = match.group(2)
            return f"{coll} {num}"
    return seg_id


def process_segments(segments, collection, file_id, unknown_words):
    """Process segments and collect unknown words."""
    for seg in segments:
        seg_id = seg.get('id', '')
        for tok in seg.get('tokens', []):
            word = tok.get('word', '')
            # Check if word is unknown (no lemma and no sandhi)
            if word and not tok.get('lemma') and not tok.get('sandhi'):
                location = f"{collection.upper()}:{file_id}:{seg_id}"
                unknown_words[word]['locations'].append(location)
                unknown_words[word]['count'] += 1


def main():
    print("=" * 70)
    print("EXPORTING DETAILED UNKNOWN WORDS LIST")
    print("=" * 70)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all unknown words with locations
    unknown_words = defaultdict(lambda: {'locations': [], 'count': 0})

    collections = ['dn', 'mn', 'sn', 'an', 'kn']

    for coll in collections:
        print(f"Processing {coll.upper()}...")
        coll_dir = LEMMATIZED_DIR / coll

        if not coll_dir.exists():
            continue

        for fpath in sorted(coll_dir.glob("*.json")):
            if fpath.name.startswith('_'):
                continue

            data = json.loads(fpath.read_text())
            file_id = fpath.stem

            # Handle different structures
            if 'segments' in data:
                process_segments(data['segments'], coll, file_id, unknown_words)
            elif 'suttas' in data:
                for sutta in data['suttas']:
                    sutta_id = sutta.get('id', file_id)
                    process_segments(sutta.get('segments', []), coll, sutta_id, unknown_words)
            elif 'items' in data:
                for item in data['items']:
                    item_id = item.get('id', file_id)
                    process_segments(item.get('segments', []), coll, item_id, unknown_words)

    print()
    print(f"Total unknown unique words: {len(unknown_words)}")

    # Sort by frequency
    sorted_words = sorted(unknown_words.items(), key=lambda x: -x[1]['count'])

    # Generate human-readable report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("UNKNOWN WORDS FROM PĀLI CANON LEMMATIZATION")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"Source: SuttaCentral corpus lemmatized with DPD v0.3.20260202")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Total unknown unique words: {len(unknown_words)}")
    report_lines.append(f"Total occurrences: {sum(w['count'] for w in unknown_words.values())}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("")

    # Group by inferred POS
    by_pos = defaultdict(list)
    for word, info in sorted_words:
        pos = infer_pos(word)
        by_pos[pos].append((word, info))

    # Output by POS category
    for pos in sorted(by_pos.keys()):
        words = by_pos[pos]
        report_lines.append(f"## {pos.upper()} ({len(words)} words)")
        report_lines.append("")

        for word, info in words[:100]:  # Limit to 100 per category
            count = info['count']
            # Get unique text locations (not full segment IDs)
            text_locs = set()
            for loc in info['locations'][:10]:  # Sample locations
                parts = loc.split(':')
                if len(parts) >= 2:
                    text_locs.add(f"{parts[0]}:{parts[1]}")

            locs_str = ', '.join(sorted(text_locs)[:5])
            if len(text_locs) > 5:
                locs_str += f" (+{len(text_locs)-5} more)"

            report_lines.append(f"  {word}")
            report_lines.append(f"    Occurrences: {count}")
            report_lines.append(f"    Found in: {locs_str}")
            report_lines.append("")

        if len(words) > 100:
            report_lines.append(f"  ... and {len(words) - 100} more words in this category")
            report_lines.append("")

        report_lines.append("")

    # Write human-readable report
    report_file = OUTPUT_DIR / "unknown_words_detailed.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"Human-readable report: {report_file}")

    # Write CSV for easy import
    csv_lines = ["word,inferred_pos,count,sample_locations"]
    for word, info in sorted_words:
        pos = infer_pos(word)
        count = info['count']
        # Get sample locations
        sample_locs = []
        seen_texts = set()
        for loc in info['locations']:
            parts = loc.split(':')
            if len(parts) >= 2:
                text_key = f"{parts[0]}:{parts[1]}"
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    sample_locs.append(text_key)
                    if len(sample_locs) >= 5:
                        break

        locs_str = '; '.join(sample_locs)
        # Escape for CSV
        word_escaped = word.replace('"', '""')
        locs_escaped = locs_str.replace('"', '""')
        csv_lines.append(f'"{word_escaped}","{pos}",{count},"{locs_escaped}"')

    csv_file = OUTPUT_DIR / "unknown_words.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(csv_lines))
    print(f"CSV export: {csv_file}")

    # Write JSON for programmatic use
    json_data = {
        'generated': datetime.now().isoformat(),
        'source': 'SuttaCentral corpus',
        'dpd_version': '0.3.20260202',
        'total_unique': len(unknown_words),
        'total_occurrences': sum(w['count'] for w in unknown_words.values()),
        'words': []
    }

    for word, info in sorted_words:
        # Get unique text references
        text_refs = set()
        for loc in info['locations']:
            parts = loc.split(':')
            if len(parts) >= 2:
                text_refs.add(f"{parts[0]}:{parts[1]}")

        json_data['words'].append({
            'word': word,
            'inferred_pos': infer_pos(word),
            'count': info['count'],
            'texts': sorted(text_refs)[:20],  # Limit to 20 text refs
            'text_count': len(text_refs)
        })

    json_file = OUTPUT_DIR / "unknown_words_detailed.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"JSON export: {json_file}")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
