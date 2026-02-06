#!/usr/bin/env python3
"""
Validation tests for the Pāli Canon critical edition corpus.

Run this before publishing to ensure data integrity.
"""

import sys
sys.path.insert(0, 'src')

from pali import Canon
from collections import Counter
import re

def test_basic_structure():
    """Test that all expected nikāyas and suttas are present."""
    print("=" * 60)
    print("TEST: Basic Structure")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Expected counts (approximate - based on traditional counts)
    expected = {
        'dn': (34, 30, 40),      # (expected, min, max)
        'mn': (152, 150, 160),
        'sn': (2889, 1800, 3000),  # varies by counting method
        'an': (2344, 1400, 2500),  # varies by counting method
        'kn': (None, 1000, 5000),  # highly variable
    }

    nikayas = canon.list_nikayas()
    print(f"Nikāyas found: {nikayas}")

    if set(nikayas) != {'dn', 'mn', 'sn', 'an', 'kn'}:
        errors.append(f"Missing nikāyas: expected dn,mn,sn,an,kn, got {nikayas}")

    for nikaya in nikayas:
        info = canon.get_nikaya_info(nikaya)
        suttas = canon.list_suttas(nikaya)
        exp, min_c, max_c = expected.get(nikaya, (None, 0, 10000))

        print(f"\n{nikaya.upper()}: {info.name_pali}")
        print(f"  Suttas: {len(suttas)}")
        print(f"  Segments: {info.segment_count}")

        if len(suttas) < min_c:
            errors.append(f"{nikaya}: too few suttas ({len(suttas)} < {min_c})")
        if len(suttas) > max_c:
            errors.append(f"{nikaya}: too many suttas ({len(suttas)} > {max_c})")
        if info.segment_count < 1000:
            errors.append(f"{nikaya}: suspiciously few segments ({info.segment_count})")

    return errors


def test_sample_suttas():
    """Verify specific well-known suttas exist and have content."""
    print("\n" + "=" * 60)
    print("TEST: Sample Suttas")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Well-known suttas with approximate segment counts
    test_cases = [
        ('dn1', 'Brahmajālasutta', 500, 800),
        ('dn2', 'Sāmaññaphalasutta', 300, 700),
        ('dn22', 'Mahāsatipaṭṭhānasutta', 200, 500),
        ('mn1', 'Mūlapariyāyasutta', 200, 500),
        ('mn10', 'Satipaṭṭhānasutta', 100, 300),
        ('mn118', 'Ānāpānassatisutta', 50, 200),
        ('sn56.11', None, 10, 100),  # Part of Saccasaṃyutta
        ('dhp1', None, 50, 200),  # Dhammapada chapter 1
        ('snp1.1', None, 30, 100),  # Sutta Nipāta
    ]

    for sutta_id, expected_title, min_seg, max_seg in test_cases:
        sutta = canon.get_sutta(sutta_id)

        if sutta is None:
            errors.append(f"{sutta_id}: NOT FOUND")
            print(f"  {sutta_id}: NOT FOUND ❌")
            continue

        status = "✓"
        issues = []

        if expected_title and sutta.title_pali and expected_title not in sutta.title_pali:
            issues.append(f"title mismatch (got '{sutta.title_pali}')")

        if sutta.segment_count < min_seg:
            issues.append(f"too few segments ({sutta.segment_count} < {min_seg})")
        if sutta.segment_count > max_seg:
            issues.append(f"too many segments ({sutta.segment_count} > {max_seg})")

        if not sutta.text or len(sutta.text) < 100:
            issues.append("text too short or empty")

        if issues:
            status = "⚠"
            errors.extend([f"{sutta_id}: {i}" for i in issues])

        print(f"  {sutta_id}: {sutta.segment_count} segments {status}")
        for i in issues:
            print(f"    → {i}")

    return errors


def test_famous_passages():
    """Check that famous Pāli passages appear correctly."""
    print("\n" + "=" * 60)
    print("TEST: Famous Passages")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Famous opening and key phrases
    passages = [
        ('dn1', 'evaṃ me sutaṃ', 'Opening formula'),
        ('mn1', 'mūlapariyāya', 'Root of All Things'),
        ('dhp1', 'manopubbaṅgamā dhammā', 'Dhp 1 - mind is forerunner'),
        ('sn56.11', 'cakkhukaraṇī', 'Making for vision'),
        ('sn56.11', 'majjhimā paṭipadā', 'Middle way'),
        ('sn56.11', 'ariyasacc', 'Noble Truths'),  # stem matches singular/plural
    ]

    for sutta_id, phrase, description in passages:
        sutta = canon.get_sutta(sutta_id)
        if sutta is None:
            errors.append(f"{sutta_id}: sutta not found for '{description}'")
            print(f"  '{description}': {sutta_id} not found ❌")
            continue

        text = sutta.text.lower()
        phrase_lower = phrase.lower()

        if phrase_lower in text:
            print(f"  '{description}': found ✓")
        else:
            # Try without diacritics variations
            simple_phrase = phrase_lower.replace('ṃ', 'm').replace('ṅ', 'n').replace('ñ', 'n')
            simple_text = text.replace('ṃ', 'm').replace('ṅ', 'n').replace('ñ', 'n')
            if simple_phrase in simple_text:
                print(f"  '{description}': found (diacritic variation) ✓")
            else:
                errors.append(f"{sutta_id}: '{phrase}' not found ({description})")
                print(f"  '{description}': NOT FOUND ❌")

    return errors


def test_lemmatization():
    """Verify lemmatization is working correctly."""
    print("\n" + "=" * 60)
    print("TEST: Lemmatization")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Get a lemmatized sutta
    sutta = canon.get_sutta('mn1', lemmatized=True)

    if sutta is None:
        errors.append("mn1: lemmatized version not found")
        return errors

    # Count tokens with lemmas (including sandhi-decomposed words)
    total_tokens = 0
    tokens_with_lemma = 0
    lemma_counts = Counter()

    for seg in sutta.segments:
        if seg.tokens:
            for token in seg.tokens:
                total_tokens += 1
                if token.lemma:
                    # Direct lemma
                    tokens_with_lemma += 1
                    lemma_counts[token.lemma] += 1
                elif token.sandhi and token.components:
                    # Sandhi decomposition - count as lemmatized
                    tokens_with_lemma += 1
                    for comp in token.components:
                        if isinstance(comp, dict) and comp.get('lemma'):
                            lemma_counts[comp['lemma']] += 1

    coverage = tokens_with_lemma / total_tokens if total_tokens > 0 else 0

    print(f"  MN1 total tokens: {total_tokens}")
    print(f"  Tokens with lemmas: {tokens_with_lemma}")
    print(f"  Coverage: {coverage:.1%}")
    print(f"  Unique lemmas: {len(lemma_counts)}")
    print(f"  Top 10 lemmas: {lemma_counts.most_common(10)}")

    if coverage < 0.97:
        errors.append(f"Low lemmatization coverage: {coverage:.1%} (expected >97%)")

    if total_tokens < 100:
        errors.append(f"Too few tokens in MN1: {total_tokens}")

    return errors


def test_search_index():
    """Verify search functionality works."""
    print("\n" + "=" * 60)
    print("TEST: Search Index")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Test lemma search
    results = canon.search_lemma('buddha')
    print(f"  search_lemma('buddha'): {results.total} occurrences")
    print(f"    By nikāya: {results.by_nikaya}")

    if results.total < 1000:
        errors.append(f"'buddha' count too low: {results.total}")

    # Test common lemmas (note: saṅgha with ṅ, not ṃ)
    for lemma, min_count in [('dhamma', 3000), ('bhikkhu', 5000), ('saṅgha', 500)]:
        results = canon.search_lemma(lemma)
        print(f"  search_lemma('{lemma}'): {results.total}")
        if results.total < min_count:
            errors.append(f"'{lemma}' count too low: {results.total} < {min_count}")

    # Test text search
    results = canon.search_text('evaṃ me sutaṃ')
    print(f"  search_text('evaṃ me sutaṃ'): {len(results)} results")

    if len(results) < 50:
        errors.append(f"'evaṃ me sutaṃ' too few results: {len(results)}")

    return errors


def test_no_english():
    """Verify no English text has crept into the corpus."""
    print("\n" + "=" * 60)
    print("TEST: No English Contamination")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Common English words that shouldn't appear
    english_words = ['the', 'and', 'is', 'are', 'was', 'were', 'this', 'that',
                     'with', 'from', 'have', 'has', 'been', 'being']

    # Check a sample of suttas
    sample_suttas = ['dn1', 'mn1', 'sn1.1', 'an1.1-10', 'dhp1']

    found_english = []
    for sutta_id in sample_suttas:
        sutta = canon.get_sutta(sutta_id)
        if sutta:
            text_lower = sutta.text.lower()
            words = set(re.findall(r'\b[a-z]+\b', text_lower))
            english_found = words.intersection(english_words)
            if english_found:
                found_english.append((sutta_id, english_found))

    if found_english:
        for sutta_id, words in found_english:
            print(f"  {sutta_id}: found English words: {words} ⚠")
            errors.append(f"{sutta_id}: contains English words {words}")
    else:
        print("  No English contamination found ✓")

    return errors


def test_data_export():
    """Verify export functions produce valid data."""
    print("\n" + "=" * 60)
    print("TEST: Data Export")
    print("=" * 60)

    canon = Canon()
    errors = []

    # Test vocabulary export (use nikaya= keyword argument)
    vocab = canon.get_vocabulary(nikaya='dn')
    print(f"  DN vocabulary: {vocab.unique_lemmas} unique lemmas")
    print(f"  Total tokens: {vocab.total_tokens}")

    if vocab.unique_lemmas < 5000:
        errors.append(f"DN vocab too small: {vocab.unique_lemmas}")

    if vocab.total_tokens < 100000:
        errors.append(f"DN token count too low: {vocab.total_tokens}")

    # Check top lemmas make sense
    top_5 = [lemma for lemma, count in vocab.top_lemmas[:5]]
    print(f"  Top 5 lemmas: {top_5}")

    # Common Pāli words that should be near the top
    expected_common = {'ta', 'ca', 'na', 'ti', 'hoti', 'bhikkhu', 'kho'}
    if not any(lemma in expected_common for lemma in top_5):
        errors.append(f"Top lemmas don't include expected common words: {top_5}")

    return errors


def main():
    print("\n" + "=" * 60)
    print("PĀLI CANON CORPUS VALIDATION")
    print("=" * 60)

    all_errors = []

    all_errors.extend(test_basic_structure())
    all_errors.extend(test_sample_suttas())
    all_errors.extend(test_famous_passages())
    all_errors.extend(test_lemmatization())
    all_errors.extend(test_search_index())
    all_errors.extend(test_no_english())
    all_errors.extend(test_data_export())

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_errors:
        print(f"\n❌ VALIDATION FAILED: {len(all_errors)} errors found\n")
        for err in all_errors:
            print(f"  • {err}")
        return 1
    else:
        print("\n✓ ALL VALIDATION TESTS PASSED\n")
        return 0


if __name__ == '__main__':
    sys.exit(main())
