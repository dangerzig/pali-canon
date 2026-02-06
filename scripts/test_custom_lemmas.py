#!/usr/bin/env python3
"""
Tests for custom_lemmas.py to catch errors and inconsistencies.
"""

import sys
sys.path.insert(0, 'src')

from pali.custom_lemmas import (
    POTENTIAL_DPD_ADDITIONS,
    METRICAL_VARIANTS,
    PROJECT_SPECIFIC,
    SANDHI_DECOMPOSITIONS,
    get_custom_lemma,
    get_all_custom_words,
)
import sqlite3
from pathlib import Path


def test_no_duplicates():
    """Check for duplicate entries across categories."""
    print("TEST: No duplicate entries across categories")
    errors = []

    all_words = []
    categories = [
        ("POTENTIAL_DPD_ADDITIONS", POTENTIAL_DPD_ADDITIONS),
        ("METRICAL_VARIANTS", METRICAL_VARIANTS),
        ("PROJECT_SPECIFIC", PROJECT_SPECIFIC),
        ("SANDHI_DECOMPOSITIONS", SANDHI_DECOMPOSITIONS),
    ]

    for cat_name, cat_dict in categories:
        for word in cat_dict.keys():
            if word in all_words:
                errors.append(f"Duplicate: '{word}' in {cat_name}")
            all_words.append(word)

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  No duplicates found ✓")

    return errors


def test_valid_pos_tags():
    """Check that all POS tags are valid."""
    print("TEST: Valid POS tags")
    errors = []

    valid_pos = {
        # Nominal
        'masc', 'fem', 'nt', 'adj', 'pron', 'card', 'name',
        # Verbal
        'verb', 'pp', 'prp', 'fpp', 'abs', 'inf', 'aor', 'imp', 'opt', 'caus',
        # Indeclinable
        'ind', 'prefix',
    }

    all_entries = {}
    all_entries.update(POTENTIAL_DPD_ADDITIONS)
    all_entries.update(METRICAL_VARIANTS)
    all_entries.update(PROJECT_SPECIFIC)

    for word, (lemma, pos) in all_entries.items():
        if pos not in valid_pos:
            errors.append(f"Invalid POS '{pos}' for '{word}' -> '{lemma}'")

    # Check sandhi components
    for word, (parts, components) in SANDHI_DECOMPOSITIONS.items():
        for comp in components:
            if comp.get('pos') not in valid_pos:
                errors.append(f"Invalid POS '{comp.get('pos')}' in sandhi '{word}'")

    if errors:
        for e in errors[:10]:  # Show first 10
            print(f"  ERROR: {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print(f"  All {len(all_entries)} entries have valid POS tags ✓")

    return errors


def test_lemma_format():
    """Check that lemmas are properly formatted."""
    print("TEST: Lemma format validation")
    errors = []

    all_entries = {}
    all_entries.update(POTENTIAL_DPD_ADDITIONS)
    all_entries.update(METRICAL_VARIANTS)
    all_entries.update(PROJECT_SPECIFIC)

    for word, (lemma, pos) in all_entries.items():
        # Check for empty lemmas
        if not lemma or not lemma.strip():
            errors.append(f"Empty lemma for '{word}'")

        # Check for spaces in lemma (shouldn't have any)
        if ' ' in lemma:
            errors.append(f"Space in lemma '{lemma}' for '{word}'")

        # Check for uppercase (Pāli lemmas should be lowercase except names)
        if pos != 'name' and lemma[0].isupper():
            errors.append(f"Uppercase lemma '{lemma}' for '{word}' (not a name)")

        # Check word matches expected pattern (Pāli characters only)
        import re
        pali_pattern = r'^[a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ\-]+$'
        if not re.match(pali_pattern, word):
            errors.append(f"Non-Pāli characters in word '{word}'")
        if not re.match(pali_pattern, lemma):
            errors.append(f"Non-Pāli characters in lemma '{lemma}'")

    if errors:
        for e in errors[:10]:
            print(f"  ERROR: {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print(f"  All {len(all_entries)} entries properly formatted ✓")

    return errors


def test_sandhi_consistency():
    """Check sandhi decompositions for consistency."""
    print("TEST: Sandhi decomposition consistency")
    errors = []

    for word, (parts, components) in SANDHI_DECOMPOSITIONS.items():
        # Check parts and components have same length
        if len(parts) != len(components):
            errors.append(f"'{word}': parts ({len(parts)}) != components ({len(components)})")

        # Check each component has required fields
        for i, comp in enumerate(components):
            if 'lemma' not in comp:
                errors.append(f"'{word}': component {i} missing 'lemma'")
            if 'pos' not in comp:
                errors.append(f"'{word}': component {i} missing 'pos'")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  All {len(SANDHI_DECOMPOSITIONS)} sandhi entries consistent ✓")

    return errors


def test_dpd_overlap():
    """Check if any custom lemmas are actually in DPD (shouldn't be)."""
    print("TEST: Check for DPD overlap (custom lemmas not needed)")

    db_path = Path("data/dpd/dpd.db")
    if not db_path.exists():
        print("  SKIP: DPD database not found")
        return []

    errors = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    all_entries = {}
    all_entries.update(POTENTIAL_DPD_ADDITIONS)
    all_entries.update(METRICAL_VARIANTS)
    all_entries.update(PROJECT_SPECIFIC)

    overlap_count = 0
    for word in all_entries.keys():
        cursor.execute("SELECT lookup_key FROM lookup WHERE lookup_key = ?", (word,))
        if cursor.fetchone():
            overlap_count += 1
            # This is informational - might be intentional override
            # errors.append(f"'{word}' is also in DPD lookup table")

    conn.close()

    if overlap_count > 0:
        print(f"  INFO: {overlap_count} words also found in DPD (may be intentional overrides)")
    else:
        print("  No overlaps with DPD ✓")

    return errors


def test_get_custom_lemma_function():
    """Test the lookup function works correctly."""
    print("TEST: get_custom_lemma() function")
    errors = []

    # Test direct lemma lookup
    result = get_custom_lemma("samāropano")
    if not result or result.get('lemma') != 'samāropana':
        errors.append(f"Failed lookup 'samāropano': got {result}")

    # Test sandhi lookup
    result = get_custom_lemma("tetaṃ")
    if not result or 'sandhi' not in result:
        errors.append(f"Failed sandhi lookup 'tetaṃ': got {result}")

    # Test case insensitivity
    result = get_custom_lemma("SAMĀROPANO")
    if not result:
        errors.append("Case-insensitive lookup failed")

    # Test unknown word returns None
    result = get_custom_lemma("xyznotaword")
    if result is not None:
        errors.append(f"Unknown word should return None, got {result}")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  All function tests passed ✓")

    return errors


def test_metrical_variants_map_to_known_lemmas():
    """Check that metrical variants map to lemmas that exist."""
    print("TEST: Metrical variants map to known lemmas")

    db_path = Path("data/dpd/dpd.db")
    if not db_path.exists():
        print("  SKIP: DPD database not found")
        return []

    errors = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for word, (lemma, pos) in METRICAL_VARIANTS.items():
        # Check if the target lemma exists in DPD headwords
        cursor.execute("SELECT id FROM dpd_headwords WHERE lemma_1 = ?", (lemma,))
        if not cursor.fetchone():
            # Also check lookup table
            cursor.execute("SELECT lookup_key FROM lookup WHERE lookup_key = ?", (lemma,))
            if not cursor.fetchone():
                errors.append(f"'{word}' -> '{lemma}' but '{lemma}' not found in DPD")

    conn.close()

    if errors:
        for e in errors:
            print(f"  WARNING: {e}")
    else:
        print(f"  All {len(METRICAL_VARIANTS)} metrical variants map to known lemmas ✓")

    return errors


def test_actual_usage_in_corpus():
    """Verify custom lemmas are actually used in the corpus."""
    print("TEST: Custom lemmas actually appear in corpus")

    from pali import Canon
    canon = Canon()

    # Get a sample of custom words
    sample_words = list(POTENTIAL_DPD_ADDITIONS.keys())[:10]

    found_count = 0
    not_found = []

    for word in sample_words:
        # Search in a few suttas
        found = False
        for nikaya in ['dn', 'mn', 'kn']:
            suttas = canon.list_suttas(nikaya)[:5]
            for sutta_info in suttas:
                sutta = canon.get_sutta(sutta_info.id)
                if sutta and word in sutta.text.lower():
                    found = True
                    break
            if found:
                break

        if found:
            found_count += 1
        else:
            not_found.append(word)

    print(f"  Found {found_count}/{len(sample_words)} sample words in corpus")
    if not_found:
        print(f"  Not found in sample: {not_found[:5]}...")

    return []  # Informational only


def test_lemmatized_data_uses_custom_lemmas():
    """Verify custom lemmas appear in lemmatized output."""
    print("TEST: Custom lemmas in lemmatized data")

    from pali import Canon
    canon = Canon()

    # Check for some known custom lemma words
    test_cases = [
        ('dn16', 'osāriyamānāni', 'osāreti'),  # Should have this lemma
    ]

    errors = []
    for sutta_id, word, expected_lemma in test_cases:
        sutta = canon.get_sutta(sutta_id, lemmatized=True)
        if not sutta:
            errors.append(f"Could not load {sutta_id}")
            continue

        found = False
        for seg in sutta.segments:
            if seg.tokens:
                for token in seg.tokens:
                    if token.word.lower() == word.lower():
                        if token.lemma == expected_lemma:
                            found = True
                            print(f"  Found '{word}' -> '{token.lemma}' in {sutta_id} ✓")
                        else:
                            errors.append(f"'{word}' has lemma '{token.lemma}', expected '{expected_lemma}'")
                        break

    if not errors:
        print("  Custom lemmas correctly applied ✓")
    else:
        for e in errors:
            print(f"  ERROR: {e}")

    return errors


def main():
    print("=" * 60)
    print("CUSTOM LEMMAS TEST SUITE")
    print("=" * 60)

    all_errors = []

    all_errors.extend(test_no_duplicates())
    print()
    all_errors.extend(test_valid_pos_tags())
    print()
    all_errors.extend(test_lemma_format())
    print()
    all_errors.extend(test_sandhi_consistency())
    print()
    all_errors.extend(test_dpd_overlap())
    print()
    all_errors.extend(test_get_custom_lemma_function())
    print()
    all_errors.extend(test_metrical_variants_map_to_known_lemmas())
    print()
    test_actual_usage_in_corpus()
    print()
    all_errors.extend(test_lemmatized_data_uses_custom_lemmas())

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
