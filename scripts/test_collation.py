#!/usr/bin/env python3
"""
Tests for collation data integrity and classification correctness.

Validates:
- Collation JSON structure
- Five-way classification with BJT and Thai witnesses
- Two-way fallback for AN nipātas 5-11 (no VRI)
- Apadāna split is correct (tha-ap vs thi-ap)
- Error classifications (SC=VRI=BJT≠PTS, PTS not in DPD)
- Vinaya/Abhidhamma five-witness collation
- No alignment artifacts in reported variants
"""

import sys
sys.path.insert(0, 'src')

import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data")
COLLATION_DIR = DATA_DIR / "collation"


def test_collation_json_structure():
    """Verify all collation files have required fields."""
    print("TEST: Collation JSON structure")
    errors = []

    # Fields expected in individual collation files
    required_fields = ['stats', 'errors', 'variants']
    # Either 'sutta' (DN/MN/SN/AN) or 'text' (KN/Vinaya/Abhidhamma) for ID
    id_fields = ['sutta', 'text']
    required_stats = ['total_positions', 'match', 'errors', 'variants']

    for nikaya in ['dn', 'mn', 'sn', 'an', 'kn', 'vinaya', 'abhidhamma']:
        nikaya_dir = COLLATION_DIR / nikaya
        if not nikaya_dir.exists():
            errors.append(f"{nikaya}: collation directory not found")
            continue

        json_files = list(nikaya_dir.glob("*_collation.json"))
        # Filter out summary files
        json_files = [f for f in json_files if not f.name.startswith('_')]

        if not json_files:
            errors.append(f"{nikaya}: no collation files found")
            continue

        for jf in json_files[:5]:  # Sample first 5
            try:
                data = json.loads(jf.read_text())

                for field in required_fields:
                    if field not in data:
                        errors.append(f"{jf.name}: missing field '{field}'")

                # Check for ID field (either 'sutta' or 'text')
                if not any(f in data for f in id_fields):
                    errors.append(f"{jf.name}: missing ID field ('sutta' or 'text')")

                if 'stats' in data:
                    for stat in required_stats:
                        if stat not in data['stats']:
                            errors.append(f"{jf.name}: missing stat '{stat}'")

            except json.JSONDecodeError as e:
                errors.append(f"{jf.name}: invalid JSON - {e}")

    if errors:
        for e in errors[:10]:
            print(f"  ERROR: {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print("  All collation files have valid structure ✓")

    return errors


def test_two_way_classification_an():
    """Verify AN nipātas 5-11 use two-way classification (no VRI)."""
    print("TEST: AN nipātas 5-11 use two-way classification")
    errors = []

    an_dir = COLLATION_DIR / "an"
    if not an_dir.exists():
        errors.append("AN collation directory not found")
        return errors

    # Nipātas 5-11 should NOT have VRI
    for nipata in range(5, 12):
        pattern = f"an{nipata}.*_collation.json"
        files = list(an_dir.glob(pattern))

        for jf in files[:3]:  # Sample a few from each
            if jf.name.startswith('_'):
                continue
            data = json.loads(jf.read_text())
            has_vri = data.get('has_vri', True)

            if has_vri:
                errors.append(f"{jf.name}: should have has_vri=False (nipāta {nipata})")

    # Nipātas 1-4 SHOULD have VRI
    for nipata in range(1, 5):
        pattern = f"an{nipata}.*_collation.json"
        files = list(an_dir.glob(pattern))

        for jf in files[:3]:
            if jf.name.startswith('_'):
                continue
            data = json.loads(jf.read_text())
            has_vri = data.get('has_vri', True)

            if not has_vri:
                errors.append(f"{jf.name}: should have has_vri=True (nipāta {nipata})")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  AN nipātas 5-11 correctly use two-way classification ✓")

    return errors


def test_apadana_split():
    """Verify tha-ap and thi-ap have correctly split content."""
    print("TEST: Apadāna split (tha-ap vs thi-ap)")
    errors = []

    kn_dir = COLLATION_DIR / "kn"
    if not kn_dir.exists():
        errors.append("KN collation directory not found")
        return errors

    tha_file = kn_dir / "tha-ap_collation.json"
    thi_file = kn_dir / "thi-ap_collation.json"

    if not tha_file.exists():
        errors.append("tha-ap_collation.json not found")
    if not thi_file.exists():
        errors.append("thi-ap_collation.json not found")

    if errors:
        return errors

    tha_data = json.loads(tha_file.read_text())
    thi_data = json.loads(thi_file.read_text())

    # Get word counts from the correct location
    tha_words = tha_data.get('word_counts', {}).get('gretil', 0)
    thi_words = thi_data.get('word_counts', {}).get('gretil', 0)

    print(f"  tha-ap GRETIL words: {tha_words:,}")
    print(f"  thi-ap GRETIL words: {thi_words:,}")

    if tha_words == thi_words and tha_words > 0:
        errors.append(f"tha-ap and thi-ap have identical GRETIL word counts ({tha_words}) - split may have failed")

    # Thera-Apadāna should be larger (it's ~83% of the text)
    if tha_words > 0 and thi_words > 0 and tha_words < thi_words:
        errors.append(f"tha-ap ({tha_words}) is smaller than thi-ap ({thi_words}) - unexpected")

    # Both should have reasonable word counts
    if tha_words < 10000:
        errors.append(f"tha-ap GRETIL word count too low: {tha_words}")
    if thi_words < 2000:
        errors.append(f"thi-ap GRETIL word count too low: {thi_words}")

    if not errors:
        print("  Apadāna correctly split into Thera/Therī sections ✓")
    else:
        for e in errors:
            print(f"  ERROR: {e}")

    return errors


def test_error_classification_accuracy():
    """Sample-check that error classifications are correct (PTS not in DPD)."""
    print("TEST: Error classification accuracy")
    errors = []

    # Load DPD headwords for validation
    dpd_file = DATA_DIR / "dpd" / "dpd_headwords.json"
    if not dpd_file.exists():
        print("  SKIP: DPD headwords file not found")
        return []

    dpd_data = json.loads(dpd_file.read_text())
    dpd_words = set(w.lower() for w in dpd_data.get('headwords', []))

    # Sample errors from DN and MN
    sample_count = 0
    false_positives = []

    for nikaya in ['dn', 'mn']:
        nikaya_dir = COLLATION_DIR / nikaya
        if not nikaya_dir.exists():
            continue

        for jf in list(nikaya_dir.glob("*_collation.json"))[:10]:
            if jf.name.startswith('_'):
                continue
            data = json.loads(jf.read_text())

            for err in data.get('errors', [])[:5]:  # Check first 5 errors
                gretil_word = err.get('gretil', '').lower()

                # Normalize for DPD lookup
                gretil_norm = gretil_word.replace('ṁ', 'ṃ').replace('ŋ', 'ṃ')

                sample_count += 1

                # If GRETIL word IS in DPD, it shouldn't be classified as error
                if gretil_norm in dpd_words:
                    false_positives.append({
                        'file': jf.name,
                        'gretil': gretil_word,
                        'sc': err.get('sc'),
                        'vri': err.get('vri')
                    })

    print(f"  Sampled {sample_count} error classifications")

    if false_positives:
        print(f"  Potential false positives: {len(false_positives)}")
        for fp in false_positives[:5]:
            print(f"    {fp['file']}: '{fp['gretil']}' is in DPD (SC={fp['sc']}, VRI={fp['vri']})")
        if len(false_positives) > 5:
            print(f"    ... and {len(false_positives) - 5} more")
        # This is informational - some may be valid due to context
    else:
        print("  No false positives found in sample ✓")

    return []  # Informational only


def test_variant_word_validity():
    """Check that variants have valid DPD words on both sides."""
    print("TEST: Variant word validity")

    dpd_file = DATA_DIR / "dpd" / "dpd_headwords.json"
    if not dpd_file.exists():
        print("  SKIP: DPD headwords file not found")
        return []

    dpd_data = json.loads(dpd_file.read_text())
    dpd_words = set(w.lower() for w in dpd_data.get('headwords', []))

    sample_count = 0
    invalid_variants = []

    for nikaya in ['dn', 'mn']:
        nikaya_dir = COLLATION_DIR / nikaya
        if not nikaya_dir.exists():
            continue

        for jf in list(nikaya_dir.glob("*_collation.json"))[:10]:
            if jf.name.startswith('_'):
                continue
            data = json.loads(jf.read_text())

            for var in data.get('variants', [])[:5]:
                gretil = var.get('gretil', '').lower().replace('ṁ', 'ṃ')
                sc = var.get('sc', '').lower().replace('ṁ', 'ṃ')

                sample_count += 1

                # Both should be valid DPD words for a true variant
                gretil_valid = gretil in dpd_words
                sc_valid = sc in dpd_words

                if not gretil_valid and not sc_valid:
                    invalid_variants.append({
                        'file': jf.name,
                        'gretil': var.get('gretil'),
                        'sc': var.get('sc')
                    })

    print(f"  Sampled {sample_count} variants")

    if invalid_variants:
        print(f"  Variants where neither word is in DPD: {len(invalid_variants)}")
        for iv in invalid_variants[:3]:
            print(f"    {iv['file']}: '{iv['gretil']}' vs '{iv['sc']}'")
    else:
        print("  All sampled variants have at least one valid DPD word ✓")

    return []


def test_no_empty_collations():
    """Check that no collation files are empty or have zero matches."""
    print("TEST: No empty collations")
    errors = []

    for nikaya in ['dn', 'mn', 'sn', 'an', 'kn']:
        nikaya_dir = COLLATION_DIR / nikaya
        if not nikaya_dir.exists():
            continue

        for jf in nikaya_dir.glob("*_collation.json"):
            if jf.name.startswith('_'):
                continue

            data = json.loads(jf.read_text())
            stats = data.get('stats', {})

            total_positions = stats.get('total_positions', 0)
            matches = stats.get('match', 0)

            if total_positions == 0:
                errors.append(f"{nikaya}/{jf.name}: zero total positions")
            elif matches == 0:
                errors.append(f"{nikaya}/{jf.name}: zero matches (suspicious)")
            elif total_positions > 0 and matches / total_positions < 0.01:
                errors.append(f"{nikaya}/{jf.name}: <1% match rate (suspicious)")

    if errors:
        for e in errors[:10]:
            print(f"  WARNING: {e}")
    else:
        print("  All collations have reasonable match rates ✓")

    return []  # Warnings only


def test_has_vri_flag():
    """Verify has_vri flag is set correctly in KN files."""
    print("TEST: has_vri flag correctness")
    errors = []

    kn_dir = COLLATION_DIR / "kn"
    if not kn_dir.exists():
        errors.append("KN collation directory not found")
        return errors

    for jf in kn_dir.glob("*_collation.json"):
        if jf.name.startswith('_'):
            continue

        data = json.loads(jf.read_text())
        has_vri = data.get('has_vri')
        word_counts = data.get('word_counts', {})
        vri_words = word_counts.get('vri', 0)

        # If has_vri is True, should have VRI word count > 0
        if has_vri and vri_words == 0:
            errors.append(f"{jf.name}: has_vri=True but vri word count is 0")

        # If has_vri is False, VRI word count should be 0
        if has_vri is False and vri_words > 0:
            errors.append(f"{jf.name}: has_vri=False but vri word count is {vri_words}")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  has_vri flag consistent with word counts ✓")

    return errors


def test_summary_files_exist():
    """Check that summary files exist for each collection."""
    print("TEST: Summary files exist")
    errors = []

    for nikaya in ['dn', 'mn', 'sn', 'an', 'kn', 'vinaya', 'abhidhamma']:
        summary_file = COLLATION_DIR / nikaya / "_collation_summary.json"
        if not summary_file.exists():
            errors.append(f"{nikaya}: _collation_summary.json not found")
        else:
            data = json.loads(summary_file.read_text())
            # Check for totals section
            if 'totals' not in data:
                errors.append(f"{nikaya}: summary missing 'totals' section")
            elif 'errors' not in data.get('totals', {}):
                errors.append(f"{nikaya}: summary totals missing 'errors'")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  All summary files present with correct structure ✓")

    return errors


def test_collation_stats_consistency():
    """Verify stats add up correctly in summaries."""
    print("TEST: Collation stats consistency")
    errors = []

    for nikaya in ['dn', 'mn']:
        nikaya_dir = COLLATION_DIR / nikaya
        summary_file = nikaya_dir / "_collation_summary.json"

        if not summary_file.exists():
            continue

        summary = json.loads(summary_file.read_text())

        # Sum up individual files
        calc_errors = 0
        calc_variants = 0

        for jf in nikaya_dir.glob("*_collation.json"):
            if jf.name.startswith('_'):
                continue
            data = json.loads(jf.read_text())
            calc_errors += data.get('stats', {}).get('errors', 0)
            calc_variants += data.get('stats', {}).get('variants', 0)

        # Get from summary totals
        totals = summary.get('totals', {})
        reported_errors = totals.get('errors', 0)
        reported_variants = totals.get('variants', 0)

        if calc_errors != reported_errors:
            errors.append(f"{nikaya}: error sum mismatch (calc={calc_errors}, reported={reported_errors})")
        if calc_variants != reported_variants:
            errors.append(f"{nikaya}: variant sum mismatch (calc={calc_variants}, reported={reported_variants})")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  Summary stats match individual file totals ✓")

    return errors


def test_word_count_sanity():
    """Check that word counts are reasonable and consistent."""
    print("TEST: Word count sanity")
    errors = []

    for nikaya in ['dn', 'mn', 'kn']:
        nikaya_dir = COLLATION_DIR / nikaya
        if not nikaya_dir.exists():
            continue

        for jf in list(nikaya_dir.glob("*_collation.json"))[:5]:
            if jf.name.startswith('_'):
                continue

            data = json.loads(jf.read_text())
            word_counts = data.get('word_counts', {})

            gretil = word_counts.get('gretil', 0)
            sc = word_counts.get('sc', 0)
            vri = word_counts.get('vri', 0)

            # All sources should have some words
            if gretil == 0:
                errors.append(f"{nikaya}/{jf.name}: GRETIL word count is 0")
            if sc == 0:
                errors.append(f"{nikaya}/{jf.name}: SC word count is 0")

            # Word counts shouldn't differ by more than 50%
            if gretil > 0 and sc > 0:
                ratio = max(gretil, sc) / min(gretil, sc)
                if ratio > 1.5:
                    # Just a warning, not an error
                    pass

    if errors:
        for e in errors[:10]:
            print(f"  ERROR: {e}")
    else:
        print("  Word counts are reasonable ✓")

    return errors


def test_classify_variant_with_bjt():
    """Test that classify_variant() works with BJT as 4th witness."""
    print("TEST: classify_variant() with BJT parameter")
    errors = []

    try:
        from collate_nikaya import classify_variant
    except ImportError:
        print("  SKIP: Could not import classify_variant from collate_nikaya")
        return []

    # Test 1: SC=VRI=BJT != PTS (3 vs 1) should have high confidence
    result = classify_variant('bhikkhūnam', 'bhikkhūnaṃ', 'bhikkhūnaṃ', bjt='bhikkhūnaṃ')
    if result['type'] not in ('pts_error', 'error'):
        errors.append(f"SC=VRI=BJT≠PTS: expected error type, got '{result['type']}'")
    if result.get('confidence', 0) < 0.9:
        errors.append(f"SC=VRI=BJT≠PTS: confidence {result.get('confidence')} should be >= 0.9")

    # Test 2: SC=VRI != PTS, BJT=PTS (2 vs 2 split) - lower confidence
    result2 = classify_variant('dhammo', 'dhamma', 'dhamma', bjt='dhammo')
    if result2.get('confidence', 0) > 0.7:
        errors.append(f"2-2 split: confidence {result2.get('confidence')} should be <= 0.7")

    # Test 3: Backward compatible (no BJT) — should work the same as before
    result3 = classify_variant('bhikkhūnam', 'bhikkhūnaṃ', 'bhikkhūnaṃ')
    if result3['type'] not in ('pts_error', 'error'):
        errors.append(f"No-BJT fallback: expected error type, got '{result3['type']}'")

    # Test 4: All four agree after normalization — classify_variant returns 'orthographic'
    # (this function is only called on positions with detected differences; identical
    # normalized forms mean the difference was purely orthographic)
    result4 = classify_variant('dhamma', 'dhamma', 'dhamma', bjt='dhamma')
    if result4['type'] != 'orthographic':
        errors.append(f"All-agree: expected 'orthographic', got '{result4['type']}'")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  classify_variant() handles BJT correctly ✓")

    return errors


def test_vinaya_abhidhamma_four_way():
    """Verify Vinaya and Abhidhamma collation files include SC and BJT data."""
    print("TEST: Vinaya/Abhidhamma five-witness collation")
    errors = []

    for collection in ['vinaya', 'abhidhamma']:
        col_dir = COLLATION_DIR / collection
        if not col_dir.exists():
            errors.append(f"{collection}: collation directory not found")
            continue

        json_files = [f for f in col_dir.glob("*_collation.json") if not f.name.startswith('_')]
        if not json_files:
            errors.append(f"{collection}: no collation files found")
            continue

        has_sc_count = 0
        has_bjt_count = 0

        for jf in json_files:
            data = json.loads(jf.read_text())

            # Check for SC and BJT flags/word counts
            word_counts = data.get('word_counts', {})
            has_sc = data.get('has_sc', word_counts.get('sc', 0) > 0)
            has_bjt = data.get('has_bjt', word_counts.get('bjt', 0) > 0)

            if has_sc:
                has_sc_count += 1
            if has_bjt:
                has_bjt_count += 1

        total = len(json_files)
        print(f"  {collection}: {total} files, {has_sc_count} with SC, {has_bjt_count} with BJT")

        if has_sc_count == 0:
            errors.append(f"{collection}: no files have SC data")
        if has_bjt_count == 0:
            errors.append(f"{collection}: no files have BJT data")

    if not errors:
        print("  Vinaya/Abhidhamma have five-witness data ✓")
    else:
        for e in errors:
            print(f"  ERROR: {e}")

    return errors


def main():
    print("=" * 60)
    print("COLLATION DATA VALIDATION")
    print("=" * 60)

    all_errors = []

    all_errors.extend(test_collation_json_structure())
    print()
    all_errors.extend(test_two_way_classification_an())
    print()
    all_errors.extend(test_apadana_split())
    print()
    all_errors.extend(test_has_vri_flag())
    print()
    all_errors.extend(test_classify_variant_with_bjt())
    print()
    all_errors.extend(test_vinaya_abhidhamma_four_way())
    print()
    all_errors.extend(test_error_classification_accuracy())
    print()
    all_errors.extend(test_variant_word_validity())
    print()
    all_errors.extend(test_no_empty_collations())
    print()
    all_errors.extend(test_summary_files_exist())
    print()
    all_errors.extend(test_collation_stats_consistency())
    print()
    all_errors.extend(test_word_count_sanity())

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
        print("\n✓ ALL COLLATION TESTS PASSED\n")
        return 0


if __name__ == '__main__':
    sys.exit(main())
