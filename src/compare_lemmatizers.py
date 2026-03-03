#!/usr/bin/env python3
"""Compare old and enhanced lemmatization pipelines.

Runs both DEFAULT_STRATEGIES and ENHANCED_STRATEGIES on a collection,
then reports differences: newly resolved words, different decompositions,
and regressions.

Usage:
    python src/compare_lemmatizers.py abhidhamma
    python src/compare_lemmatizers.py dn
    python src/compare_lemmatizers.py dn mn --output work/comparison.tsv
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent))

from lemmatize_canon import (
    Lemmatizer, DEFAULT_STRATEGIES, ENHANCED_STRATEGIES,
    CANONICAL_DIR, TokenInfo,
)


def collect_unique_words(collection: str, lemmatizer: Lemmatizer) -> set[str]:
    """Collect all unique words from a collection's canonical files."""
    input_dir = CANONICAL_DIR / collection
    files = sorted([f for f in input_dir.glob("*.json") if not f.name.startswith("_")])
    words = set()

    for input_path in files:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        segments = []
        if "segments" in data:
            segments = data["segments"]
        elif "suttas" in data:
            for sutta in data["suttas"]:
                segments.extend(sutta.get("segments", []))
        elif "items" in data:
            for item in data["items"]:
                segments.extend(item.get("segments", []))

        for segment in segments:
            pali_text = segment.get("pali", "")
            tokens = lemmatizer.tokenize(pali_text)
            words.update(tokens)

    return words


def token_summary(token: TokenInfo) -> str:
    """Summarize a token's result as a compact string."""
    if token.sandhi:
        return "sandhi:" + "+".join(str(s) for s in token.sandhi)
    elif token.lemma:
        return f"lemma:{token.lemma}"
    else:
        return "unknown"


def compare_collections(collections: list[str], output_path: str = None):
    """Run comparison between old and enhanced pipelines."""
    with Lemmatizer() as lemmatizer:
        # Collect unique words
        all_words = set()
        for collection in collections:
            print(f"Collecting words from {collection.upper()}...")
            words = collect_unique_words(collection, lemmatizer)
            print(f"  {len(words):,} unique words")
            all_words.update(words)

        print(f"\nTotal unique words across collections: {len(all_words):,}")
        print(f"\nRunning old pipeline...")

        lemmatizer._active_strategies = DEFAULT_STRATEGIES
        old_results = {}
        for word in sorted(all_words):
            lemmatizer.cache.clear()
            token = lemmatizer.lookup_word(word, strategies=DEFAULT_STRATEGIES)
            old_results[word] = token

        # Reset stats and cache
        lemmatizer.cache.clear()
        lemmatizer._valid_word_cache.clear()

        print("Running enhanced pipeline...")
        lemmatizer._active_strategies = ENHANCED_STRATEGIES
        new_results = {}
        for word in sorted(all_words):
            lemmatizer.cache.clear()
            token = lemmatizer.lookup_word(word, strategies=ENHANCED_STRATEGIES)
            new_results[word] = token

    # Compare results
    newly_resolved = []
    different_decomposition = []
    regressions = []
    unchanged = 0

    for word in sorted(all_words):
        old = old_results[word]
        new = new_results[word]
        old_sum = token_summary(old)
        new_sum = token_summary(new)

        old_resolved = old.lemma is not None or old.sandhi is not None
        new_resolved = new.lemma is not None or new.sandhi is not None

        if old_sum == new_sum:
            unchanged += 1
        elif not old_resolved and new_resolved:
            newly_resolved.append((word, old_sum, new_sum))
        elif old_resolved and not new_resolved:
            regressions.append((word, old_sum, new_sum))
        else:
            different_decomposition.append((word, old_sum, new_sum))

    # Print summary
    print(f"\n{'=' * 60}")
    print("COMPARISON RESULTS")
    print(f"{'=' * 60}")
    print(f"Total unique words:    {len(all_words):,}")
    print(f"Unchanged:             {unchanged:,}")
    print(f"Newly resolved:        {len(newly_resolved):,}")
    print(f"Different decomp:      {len(different_decomposition):,}")
    print(f"Regressions:           {len(regressions):,}")

    if newly_resolved:
        print(f"\n--- NEWLY RESOLVED ({len(newly_resolved)}) ---")
        for word, old_sum, new_sum in newly_resolved[:50]:
            print(f"  {word}: {new_sum}")
        if len(newly_resolved) > 50:
            print(f"  ... and {len(newly_resolved) - 50} more")

    if regressions:
        print(f"\n--- REGRESSIONS ({len(regressions)}) ---")
        for word, old_sum, new_sum in regressions:
            print(f"  {word}: {old_sum} -> {new_sum}")

    if different_decomposition:
        print(f"\n--- DIFFERENT DECOMPOSITION ({len(different_decomposition)}) ---")
        for word, old_sum, new_sum in different_decomposition[:30]:
            print(f"  {word}: {old_sum} -> {new_sum}")
        if len(different_decomposition) > 30:
            print(f"  ... and {len(different_decomposition) - 30} more")

    # Write TSV if output path specified
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            f.write("word\tchange_type\told_result\tnew_result\n")
            for word, old_sum, new_sum in newly_resolved:
                f.write(f"{word}\tnewly_resolved\t{old_sum}\t{new_sum}\n")
            for word, old_sum, new_sum in regressions:
                f.write(f"{word}\tregression\t{old_sum}\t{new_sum}\n")
            for word, old_sum, new_sum in different_decomposition:
                f.write(f"{word}\tdifferent\t{old_sum}\t{new_sum}\n")
        print(f"\nDifferences written to: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare old and enhanced lemmatization pipelines")
    parser.add_argument('collections', nargs='+',
                        help='Collections to compare (e.g., dn, abhidhamma)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output TSV path for differences')
    args = parser.parse_args()

    compare_collections(args.collections, args.output)


if __name__ == "__main__":
    main()
