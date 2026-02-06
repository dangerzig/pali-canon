#!/usr/bin/env python3
"""
Measure how much the normalization rules improve lemmatization coverage.

This script:
1. Finds all tokens without lemmas in the corpus
2. Tries metrical normalization and sandhi decomposition
3. Checks if normalized forms exist in the lemma vocabulary
4. Reports potential coverage improvement
"""

import sys
sys.path.insert(0, 'src')

from collections import Counter
from pali import Canon
from pali.normalize import normalize_form, generate_metrical_variants, decompose_sandhi


def get_unlemmatized_tokens(canon: Canon, sample_size: int = None) -> tuple:
    """
    Find all tokens without lemmas in the corpus.

    A token is considered "lemmatized" if it has either:
    - A direct lemma field, OR
    - A sandhi decomposition with components (each component has its own lemma)

    Returns:
        (unlemmatized_forms, total_tokens, known_lemmas_set)
    """
    unlemmatized = Counter()
    total_tokens = 0
    known_lemmas = set()

    nikayas = ['dn', 'mn', 'sn', 'an', 'kn'] if not sample_size else ['dn']

    for nikaya in nikayas:
        print(f"  Scanning {nikaya.upper()}...")
        suttas = canon.list_suttas(nikaya, lemmatized=True)

        for i, sutta_info in enumerate(suttas):
            if sample_size and i >= sample_size:
                break

            sutta = canon.get_sutta(sutta_info.id, lemmatized=True)
            if not sutta:
                continue

            for segment in sutta.segments:
                if segment.tokens:
                    for token in segment.tokens:
                        total_tokens += 1
                        if token.lemma:
                            # Direct lemma
                            known_lemmas.add(token.lemma)
                        elif token.sandhi and token.components:
                            # Sandhi decomposition - extract lemmas from components
                            for comp in token.components:
                                if isinstance(comp, dict) and comp.get('lemma'):
                                    known_lemmas.add(comp['lemma'])
                        else:
                            # Truly unlemmatized
                            unlemmatized[token.word] += 1

    return unlemmatized, total_tokens, known_lemmas


def analyze_improvement(unlemmatized: Counter, known_lemmas: set) -> dict:
    """
    Analyze how many unlemmatized forms can be fixed.
    """
    # Common particles/pronouns that are always valid even if not in corpus lemmas
    # (These are grammatically valid Pāli words that may not appear as lemmas in the sample)
    ALWAYS_VALID = {
        'ca', 'na', 'api', 'hi', 'eva', 'evaṃ', 'iti', 'kho', 'pana', 'nu', 'su', 'vā', 'tu',
        'ta', 'ya', 'ima', 'eta', 'idaṃ', 'ahaṃ', 'tvaṃ',
        'assa', 'hoti', 'atthi', 'āha', 'avoca', 'ahosi',
    }
    valid_words = known_lemmas | ALWAYS_VALID

    results = {
        'metrical_fixable': [],
        'sandhi_fixable': [],
        'sandhi_partial': [],  # At least one component is known
        'both_fixable': [],
        'still_unresolved': [],
    }

    for form, count in unlemmatized.most_common():
        # Try metrical normalization
        metrical_results = generate_metrical_variants(form)
        metrical_matches = [r for r in metrical_results if r.normalized in known_lemmas]

        # Try sandhi decomposition
        sandhi_results = decompose_sandhi(form)
        sandhi_full_matches = []
        sandhi_partial_matches = []
        for r in sandhi_results:
            if r.components:
                known_count = sum(1 for comp in r.components if comp in valid_words)
                if known_count == len(r.components):
                    sandhi_full_matches.append(r)
                elif known_count > 0:
                    sandhi_partial_matches.append(r)

        if metrical_matches and sandhi_full_matches:
            results['both_fixable'].append((form, count, metrical_matches[0], sandhi_full_matches[0]))
        elif metrical_matches:
            results['metrical_fixable'].append((form, count, metrical_matches[0]))
        elif sandhi_full_matches:
            results['sandhi_fixable'].append((form, count, sandhi_full_matches[0]))
        elif sandhi_partial_matches:
            results['sandhi_partial'].append((form, count, sandhi_partial_matches[0]))
        else:
            results['still_unresolved'].append((form, count))

    return results


def main():
    print("=" * 70)
    print("NORMALIZATION IMPROVEMENT ANALYSIS")
    print("=" * 70)

    canon = Canon()

    print("\nStep 1: Scanning corpus for unlemmatized tokens...")
    print("(This may take a few minutes for the full corpus)")

    # Use sample for quick testing, None for full corpus
    unlemmatized, total_tokens, known_lemmas = get_unlemmatized_tokens(canon, sample_size=None)

    unlemmatized_count = sum(unlemmatized.values())
    unique_unlemmatized = len(unlemmatized)

    print(f"\nCorpus Statistics:")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Known lemmas: {len(known_lemmas):,}")
    print(f"  Unlemmatized tokens: {unlemmatized_count:,} ({100*unlemmatized_count/total_tokens:.2f}%)")
    print(f"  Unique unlemmatized forms: {unique_unlemmatized:,}")

    print("\nStep 2: Analyzing potential fixes...")
    results = analyze_improvement(unlemmatized, known_lemmas)

    # Calculate token counts for each category
    metrical_tokens = sum(count for _, count, *_ in results['metrical_fixable'])
    sandhi_tokens = sum(count for _, count, *_ in results['sandhi_fixable'])
    sandhi_partial_tokens = sum(count for _, count, *_ in results['sandhi_partial'])
    both_tokens = sum(count for _, count, *_ in results['both_fixable'])
    unresolved_tokens = sum(count for _, count in results['still_unresolved'])

    print(f"\nResults:")
    print(f"  Metrical variants fixable: {len(results['metrical_fixable']):,} forms ({metrical_tokens:,} tokens)")
    print(f"  Sandhi fully decomposable: {len(results['sandhi_fixable']):,} forms ({sandhi_tokens:,} tokens)")
    print(f"  Sandhi partially decomposable: {len(results['sandhi_partial']):,} forms ({sandhi_partial_tokens:,} tokens)")
    print(f"  Both methods apply: {len(results['both_fixable']):,} forms ({both_tokens:,} tokens)")
    print(f"  Still unresolved: {len(results['still_unresolved']):,} forms ({unresolved_tokens:,} tokens)")

    # Calculate improvement (include partial as 50% recoverable)
    fixable_tokens = metrical_tokens + sandhi_tokens + both_tokens + (sandhi_partial_tokens // 2)
    original_coverage = (total_tokens - unlemmatized_count) / total_tokens
    new_coverage = (total_tokens - unlemmatized_count + fixable_tokens) / total_tokens

    print(f"\nCoverage Improvement:")
    print(f"  Original coverage: {100*original_coverage:.2f}%")
    print(f"  Potential new coverage: {100*new_coverage:.2f}%")
    print(f"  Improvement: +{100*(new_coverage - original_coverage):.2f}%")

    # Show examples of each category
    print("\n" + "=" * 70)
    print("EXAMPLES")
    print("=" * 70)

    print("\nMetrical variants (top 10):")
    for form, count, result in results['metrical_fixable'][:10]:
        print(f"  {form} ({count}x) → {result.normalized} [{result.rule_applied}]")

    print("\nSandhi fully decomposable (top 10):")
    for form, count, result in results['sandhi_fixable'][:10]:
        print(f"  {form} ({count}x) → {result.components} [{result.rule_applied}]")

    print("\nSandhi partially decomposable (top 10):")
    for form, count, result in results['sandhi_partial'][:10]:
        print(f"  {form} ({count}x) → {result.components} [{result.rule_applied}]")

    print("\nStill unresolved (top 20):")
    for form, count in results['still_unresolved'][:20]:
        print(f"  {form} ({count}x)")

    return results


if __name__ == "__main__":
    main()
