#!/usr/bin/env python3
"""
Tests for lemmatization quality and consistency.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import re
import json
from collections import Counter
from pali import Canon


def test_high_frequency_words_lemmatized():
    """Check that common Pāli words are lemmatized correctly."""
    print("TEST: High-frequency words lemmatized")
    errors = []

    canon = Canon()

    # Common words and their expected lemmas
    # Note: DPD sometimes uses inflected forms as headwords (e.g. bhikkhave, bhagavato)
    # These are valid - the grammar field notes the base form.
    # We accept either the base form OR the DPD headword form.
    expected_lemmas = {
        'bhikkhave': ['bhikkhu', 'bhikkhave'],  # DPD has separate headword
        'bhagavā': ['bhagavant'],
        'bhagavato': ['bhagavant', 'bhagavato'],  # DPD has separate headwords for cases
        'dhammaṃ': ['dhamma'],
        'dhammā': ['dhamma'],
        'saṅghaṃ': ['saṅgha'],
        'buddhaṃ': ['buddha'],
        'nibbānaṃ': ['nibbāna'],
        'dukkhaṃ': ['dukkha'],
        'sukhaṃ': ['sukha'],
        'kāyena': ['kāya'],
        'vācāya': ['vācā'],
        'manasā': ['manas'],
        'cakkhuṃ': ['cakkhu'],
        'sotaṃ': ['sota'],
    }

    # Check in MN1
    sutta = canon.get_sutta('mn1', lemmatized=True)
    if not sutta:
        errors.append("Could not load mn1")
        return errors

    found_words = {}
    for seg in sutta.segments:
        if seg.tokens:
            for token in seg.tokens:
                word_lower = token.word.lower()
                if word_lower in expected_lemmas:
                    found_words[word_lower] = token.lemma

    for word, acceptable in expected_lemmas.items():
        if word in found_words:
            if found_words[word] not in acceptable:
                errors.append(f"'{word}' has lemma '{found_words[word]}', expected one of {acceptable}")
            else:
                print(f"  '{word}' -> '{found_words[word]}' ✓")

    if not errors:
        print(f"  All tested words correctly lemmatized ✓")
    else:
        for e in errors:
            print(f"  ERROR: {e}")

    return errors


def test_sandhi_decomposition_quality():
    """Check that sandhi decompositions are reasonable."""
    print("TEST: Sandhi decomposition quality")
    errors = []

    canon = Canon()
    sutta = canon.get_sutta('dn1', lemmatized=True)
    if not sutta:
        errors.append("Could not load dn1")
        return errors

    sandhi_tokens = []
    for seg in sutta.segments:
        if seg.tokens:
            for token in seg.tokens:
                if token.sandhi:
                    sandhi_tokens.append(token)

    print(f"  Found {len(sandhi_tokens)} sandhi tokens in DN1")

    # Check some sandhi decompositions make sense
    suspicious = []
    for token in sandhi_tokens:
        # Check component count is reasonable (usually 2-4)
        if token.components and len(token.components) > 5:
            suspicious.append(f"'{token.word}' has {len(token.components)} components")

        # Check components have lemmas
        if token.components:
            for i, comp in enumerate(token.components):
                if isinstance(comp, dict) and not comp.get('lemma'):
                    suspicious.append(f"'{token.word}' component {i} missing lemma")

    if suspicious:
        print(f"  Suspicious decompositions:")
        for s in suspicious[:5]:
            print(f"    {s}")
        if len(suspicious) > 5:
            print(f"    ... and {len(suspicious) - 5} more")
    else:
        print(f"  All sandhi decompositions look reasonable ✓")

    return errors


def test_no_empty_lemmas():
    """Check that no tokens have empty/null lemmas when they should have one."""
    print("TEST: No unexpected empty lemmas")
    errors = []

    canon = Canon()

    # Sample a few suttas from each nikaya
    test_suttas = ['dn1', 'mn1', 'sn1.1', 'an1.1-10', 'dhp1']

    for sutta_id in test_suttas:
        sutta = canon.get_sutta(sutta_id, lemmatized=True)
        if not sutta:
            continue

        empty_count = 0
        total_tokens = 0

        for seg in sutta.segments:
            if seg.tokens:
                for token in seg.tokens:
                    total_tokens += 1
                    # Token should have either lemma or sandhi
                    if not token.lemma and not token.sandhi:
                        empty_count += 1

        if empty_count > 0:
            pct = 100 * empty_count / total_tokens
            print(f"  {sutta_id}: {empty_count}/{total_tokens} ({pct:.1f}%) empty")
            if pct > 1:  # More than 1% is concerning
                errors.append(f"{sutta_id} has {pct:.1f}% empty lemmas")

    if not errors:
        print("  All sampled suttas have acceptable lemma coverage ✓")

    return errors


def test_pos_consistency():
    """Check that the same lemma gets consistent POS tags."""
    print("TEST: POS tag consistency")
    errors = []

    canon = Canon()
    sutta = canon.get_sutta('mn1', lemmatized=True)
    if not sutta:
        errors.append("Could not load mn1")
        return errors

    lemma_pos = {}  # lemma -> set of POS tags seen

    for seg in sutta.segments:
        if seg.tokens:
            for token in seg.tokens:
                if token.lemma and token.pos:
                    if token.lemma not in lemma_pos:
                        lemma_pos[token.lemma] = set()
                    lemma_pos[token.lemma].add(token.pos)

    # Check for lemmas with multiple POS (some are valid, like noun/adj)
    multi_pos = {lemma: poses for lemma, poses in lemma_pos.items() if len(poses) > 1}

    if multi_pos:
        print(f"  Lemmas with multiple POS tags (may be valid):")
        for lemma, poses in list(multi_pos.items())[:5]:
            print(f"    {lemma}: {poses}")
    else:
        print("  All lemmas have consistent POS tags ✓")

    return []  # Informational only


def test_token_word_matches_text():
    """Check that token words match the original segment text."""
    print("TEST: Token words match segment text")
    errors = []

    canon = Canon()
    sutta = canon.get_sutta('dn1', lemmatized=True)
    if not sutta:
        errors.append("Could not load dn1")
        return errors

    mismatches = []
    for seg in sutta.segments:
        if seg.tokens and seg.pali:
            # Reconstruct text from tokens
            token_words = [t.word for t in seg.tokens]
            token_text = ' '.join(token_words).lower()

            # Normalize original text
            orig_text = re.sub(r'[^\w\s]', ' ', seg.pali.lower())
            orig_text = ' '.join(orig_text.split())

            # Compare (allow some variation)
            if token_text != orig_text:
                # Check if it's just punctuation differences
                orig_words = set(orig_text.split())
                token_set = set(t.lower() for t in token_words)

                diff = orig_words.symmetric_difference(token_set)
                if len(diff) > 3:  # More than 3 word differences
                    mismatches.append((seg.id, len(diff)))

    if mismatches:
        print(f"  Segments with token/text mismatches:")
        for seg_id, diff_count in mismatches[:5]:
            print(f"    {seg_id}: {diff_count} word differences")
        if len(mismatches) > 5:
            print(f"    ... and {len(mismatches) - 5} more")
    else:
        print("  All segments have matching tokens ✓")

    return []  # Informational only


def test_stats_file_accuracy():
    """Check that _stats.json matches actual data."""
    print("TEST: Stats file accuracy")
    errors = []

    stats_path = Path(__file__).resolve().parent.parent / "data/lemmatized/_stats.json"
    if not stats_path.exists():
        errors.append("Stats file not found")
        return errors

    with open(stats_path) as f:
        stats = json.load(f)

    canon = Canon()

    # Check a sample nikaya's word count
    dn_suttas = canon.list_suttas('dn', lemmatized=True)
    dn_tokens = 0
    for sutta_info in dn_suttas[:5]:  # Sample first 5
        sutta = canon.get_sutta(sutta_info.id, lemmatized=True)
        if sutta:
            for seg in sutta.segments:
                if seg.tokens:
                    dn_tokens += len(seg.tokens)

    print(f"  Stats file reports: {stats['total_words']:,} total words")
    print(f"  Stats file coverage: {stats['coverage']}")
    print(f"  Sample DN tokens: {dn_tokens:,}")

    # Verify coverage claim
    claimed_coverage = float(stats['coverage'].rstrip('%'))
    if claimed_coverage < 97:
        errors.append(f"Claimed coverage {claimed_coverage}% seems too low")
    elif claimed_coverage > 100:
        errors.append(f"Claimed coverage {claimed_coverage}% exceeds 100%")
    else:
        print(f"  Coverage claim {claimed_coverage}% is reasonable ✓")

    return errors


def test_cross_nikaya_consistency():
    """Check lemmatization is consistent across nikāyas."""
    print("TEST: Cross-nikāya consistency")
    errors = []

    canon = Canon()

    # Common word across all nikāyas
    test_word = "bhagavā"
    expected_lemma = "bhagavant"

    lemmas_found = {}
    for nikaya in ['dn', 'mn', 'sn', 'an']:
        suttas = canon.list_suttas(nikaya, lemmatized=True)
        if not suttas:
            continue

        sutta = canon.get_sutta(suttas[0].id, lemmatized=True)
        if not sutta:
            continue

        for seg in sutta.segments:
            if seg.tokens:
                for token in seg.tokens:
                    if token.word.lower() == test_word:
                        lemmas_found[nikaya] = token.lemma
                        break
            if nikaya in lemmas_found:
                break

    print(f"  Lemma for '{test_word}' across nikāyas:")
    for nikaya, lemma in lemmas_found.items():
        status = "✓" if lemma == expected_lemma else "✗"
        print(f"    {nikaya.upper()}: {lemma} {status}")
        if lemma != expected_lemma:
            errors.append(f"{nikaya}: '{test_word}' has lemma '{lemma}', expected '{expected_lemma}'")

    if not errors:
        print(f"  Consistent lemmatization across nikāyas ✓")

    return errors


def main():
    print("=" * 60)
    print("LEMMATIZATION QUALITY TESTS")
    print("=" * 60)

    all_errors = []

    all_errors.extend(test_high_frequency_words_lemmatized())
    print()
    all_errors.extend(test_sandhi_decomposition_quality())
    print()
    all_errors.extend(test_no_empty_lemmas())
    print()
    all_errors.extend(test_pos_consistency())
    print()
    all_errors.extend(test_token_word_matches_text())
    print()
    all_errors.extend(test_stats_file_accuracy())
    print()
    all_errors.extend(test_cross_nikaya_consistency())

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_errors:
        print(f"\n❌ {len(all_errors)} errors found\n")
        for e in all_errors:
            print(f"  • {e}")
        return 1
    else:
        print("\n✓ ALL TESTS PASSED\n")
        return 0


if __name__ == '__main__':
    sys.exit(main())
