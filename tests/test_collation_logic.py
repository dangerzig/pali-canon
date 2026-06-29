"""Tests for collation core functions: classify_variant, normalize_for_comparison, words_are_related.

These test the pure classification logic with synthetic inputs — no data files needed.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path so we can import collate_nikaya
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import collate_nikaya
from collate_nikaya import (
    normalize_for_comparison,
    words_are_related,
    classify_variant,
)


class TestDpdValidationFailsClosed:
    """Finding 2: DPD word validation must fail closed, not pass everything."""

    def _reset(self):
        collate_nikaya._dpd_words = None
        collate_nikaya._dpd_source = None

    def test_raises_when_no_source(self, tmp_path):
        self._reset()
        with patch.object(collate_nikaya, "DPD_DIR", tmp_path / "nodir"), \
             patch.object(collate_nikaya, "DATA_DIR", tmp_path / "nodata"), \
             patch.object(collate_nikaya, "DPD_DB", tmp_path / "no.db"):
            with pytest.raises(FileNotFoundError):
                collate_nikaya.load_dpd_words()
        self._reset()

    def test_falls_back_to_dpd_db(self, tmp_path):
        from pathlib import Path
        real_db = Path(__file__).parent.parent / "data" / "dpd" / "dpd.db"
        if not real_db.exists():
            pytest.skip("dpd.db not present")
        self._reset()
        with patch.object(collate_nikaya, "DPD_DIR", tmp_path / "nodir"), \
             patch.object(collate_nikaya, "DATA_DIR", tmp_path / "nodata"), \
             patch.object(collate_nikaya, "DPD_DB", real_db):
            words = collate_nikaya.load_dpd_words()
            assert len(words) > 100000
            assert collate_nikaya.get_dpd_validation_source().endswith("dpd.db")
        self._reset()

    def test_is_valid_word_rejects_garbage(self):
        real_db = collate_nikaya.DPD_DIR / "dpd.db"
        if not (collate_nikaya.DPD_DIR / "dpd_headwords.json").exists() and not real_db.exists():
            pytest.skip("no DPD validation source present")
        self._reset()
        assert collate_nikaya.is_valid_word("bhikkhu") is True
        assert collate_nikaya.is_valid_word("zzqxnotaword") is False
        self._reset()


# =========================================================================
# normalize_for_comparison()
# =========================================================================

class TestNormalizeForComparison:
    def test_empty_string(self):
        assert normalize_for_comparison('') == ''

    def test_none_returns_empty(self):
        # Function is never called with None (callers guard), but test behavior
        assert normalize_for_comparison(None) == ''

    def test_lowercase(self):
        assert normalize_for_comparison('Dhamma') == 'dhamma'

    def test_niggahita_variants(self):
        """ṁ and ŋ should normalize to ṃ."""
        assert normalize_for_comparison('dhammaṁ') == 'dhammaṃ'
        assert normalize_for_comparison('dhammaŋ') == 'dhammaṃ'
        assert normalize_for_comparison('dhammaṃ') == 'dhammaṃ'

    def test_sangha_normalization(self):
        """saṅgh should normalize to saṃgh."""
        assert normalize_for_comparison('saṅgha') == 'saṃgha'
        assert normalize_for_comparison('saṃgha') == 'saṃgha'

    def test_sankh_normalization(self):
        """saṅk should normalize to saṃk."""
        assert normalize_for_comparison('saṅkhāra') == 'saṃkhāra'
        assert normalize_for_comparison('saṃkhāra') == 'saṃkhāra'

    def test_already_normalized(self):
        assert normalize_for_comparison('nibbāna') == 'nibbāna'

    def test_multiple_normalizations(self):
        """Multiple normalizations in one word."""
        result = normalize_for_comparison('Saṅghaṁ')
        assert result == 'saṃghaṃ'


# =========================================================================
# words_are_related()
# =========================================================================

class TestWordsAreRelated:
    def test_identical_words(self):
        assert words_are_related('dhamma', 'dhamma') is True

    def test_case_insensitive(self):
        assert words_are_related('Dhamma', 'dhamma') is True

    def test_empty_first(self):
        assert words_are_related('', 'dhamma') is False

    def test_empty_second(self):
        assert words_are_related('dhamma', '') is False

    def test_both_empty(self):
        assert words_are_related('', '') is False

    def test_none_first(self):
        assert words_are_related(None, 'dhamma') is False

    def test_none_second(self):
        assert words_are_related('dhamma', None) is False

    def test_short_words_equal(self):
        """Words <= 2 chars must be exactly equal."""
        assert words_are_related('ca', 'ca') is True
        assert words_are_related('ca', 'ce') is False

    def test_short_word_different(self):
        assert words_are_related('na', 'no') is False

    def test_similar_inflections(self):
        """Related inflected forms should match."""
        assert words_are_related('dhammassa', 'dhammaṃ') is True

    def test_substring_match(self):
        """One word contained in the other."""
        assert words_are_related('buddha', 'buddhaṃ') is True

    def test_unrelated_words(self):
        """Completely unrelated words."""
        assert words_are_related('āyasmā', 'pathavī') is False

    def test_very_different_lengths(self):
        """Length ratio > 3 should return False."""
        assert words_are_related('ca', 'mahāparinibbānasutta') is False

    def test_prefix_match(self):
        """Words sharing significant prefix."""
        assert words_are_related('suttaṃ', 'suttanta') is True

    def test_similarity_threshold(self):
        """Similarity just at the boundary (~0.5)."""
        # These are quite different but may share some characters
        assert words_are_related('abcdefgh', 'xyzabcde') is True  # substring match


# =========================================================================
# classify_variant() — mock is_valid_word to control DPD validation
# =========================================================================

def mock_valid_always(word):
    """Mock: all words are valid."""
    return True


def mock_valid_except_pts(word):
    """Mock: PTS-only words are invalid, others valid."""
    invalid = {'dhammo', 'bhikkhavo', 'xyznotaword', 'tīhi'}
    return word.lower() not in invalid


def mock_valid_all_invalid(word):
    """Mock: no words are valid."""
    return False


class TestClassifyVariantBasicPaths:
    """Test early-return paths that don't depend on DPD validation."""

    def test_all_agree(self):
        """All witnesses have the same word."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhamma', 'dhamma')
            assert result['type'] == 'orthographic'
            assert result['confidence'] == 1.0

    def test_all_agree_with_bjt_thai(self):
        """All 5 witnesses agree."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhamma', 'dhamma',
                                     'dhamma', 'dhamma')
            assert result['type'] == 'orthographic'
            assert result['confidence'] == 1.0

    def test_orthographic_normalization(self):
        """Same word with niggahita variants normalizes to agree."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhammaṃ', 'dhammaṁ', 'dhammaṃ')
            assert result['type'] == 'orthographic'

    def test_pts_missing_no_sc_vri(self):
        """PTS (GRETIL) word is missing and SC/VRI also missing."""
        result = classify_variant('', None, None)
        assert result['type'] == 'missing'

    def test_pts_omission_empty_string(self):
        """Empty PTS with SC/VRI present → pts_omission."""
        result = classify_variant('', 'dhamma', 'dhamma')
        assert result['type'] == 'pts_omission'

    def test_pts_omission_none(self):
        """None PTS with SC/VRI present → pts_omission."""
        result = classify_variant(None, 'dhamma', 'dhamma')
        assert result['type'] == 'pts_omission'

    def test_sc_vri_omission(self):
        """Word in PTS but not SC/VRI."""
        result = classify_variant('dhamma', None, None)
        assert result['type'] == 'pts_addition'

    def test_pts_addition_present_sc_vri_missing(self):
        result = classify_variant('dhamma', '', '')
        assert result['type'] == 'pts_addition'

    def test_alignment_artifact(self):
        """Unrelated words should be classified as alignment artifact."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('āyasmā', 'pathavī', 'pathavī')
            assert result['type'] == 'alignment_artifact'

    def test_short_fragment(self):
        """Very short non-common words classified as fragment (no SC/VRI)."""
        result = classify_variant('x', None, None)
        assert result['type'] == 'fragment'

    def test_short_word_with_sc_vri_is_alignment(self):
        """Short unrelated word with SC/VRI → alignment artifact (not fragment)."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('x', 'dhamma', 'dhamma')
            assert result['type'] == 'alignment_artifact'

    def test_short_common_word_not_fragment(self):
        """Common 2-letter Pāli words should NOT be fragments."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('ca', 'ca', 'ca')
            assert result['type'] != 'fragment'

    def test_bjt_disagrees_breaks_agreement(self):
        """G/S/V agree but BJT differs — not orthographic."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhamma', 'dhamma',
                                     bjt='dhammo')
            assert result['type'] != 'orthographic'

    def test_thai_disagrees_breaks_agreement(self):
        """G/S/V agree but Thai differs — not orthographic."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhamma', 'dhamma',
                                     thai='dhammo')
            assert result['type'] != 'orthographic'


class TestClassifyVariantErrorDetection:
    """Test error classification (PTS invalid, SC/VRI valid)."""

    def test_sc_vri_agree_pts_invalid(self):
        """SC=VRI agree, PTS reading not in DPD → error."""
        with patch('collate_nikaya.is_valid_word', mock_valid_except_pts):
            result = classify_variant('dhammo', 'dhamma', 'dhamma')
            assert result['type'] == 'error'
            assert result['confidence'] >= 0.9
            assert result['preferred'] == 'dhamma'

    def test_error_with_bjt_majority(self):
        """SC=VRI=BJT agree, PTS invalid → high confidence error."""
        with patch('collate_nikaya.is_valid_word', mock_valid_except_pts):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhamma')
            assert result['type'] == 'error'
            assert result['confidence'] >= 0.95

    def test_error_with_all_four_majority(self):
        """SC=VRI=BJT=Thai agree, PTS invalid → very high confidence."""
        with patch('collate_nikaya.is_valid_word', mock_valid_except_pts):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhamma', thai='dhamma')
            assert result['type'] == 'error'
            assert result['confidence'] >= 0.98

    def test_error_bjt_with_pts(self):
        """SC=VRI vs PTS, BJT sides with PTS — lower confidence."""
        with patch('collate_nikaya.is_valid_word', mock_valid_except_pts):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhammo')
            assert result['type'] == 'error'
            assert result['confidence'] < 0.9  # Lower because BJT agrees with PTS


class TestClassifyVariantVariantDetection:
    """Test variant classification (both readings valid)."""

    def test_sc_vri_agree_both_valid(self):
        """SC=VRI agree, both readings in DPD → variant."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhammo', 'dhamma', 'dhamma')
            assert result['type'] == 'variant'

    def test_variant_with_bjt_majority(self):
        """SC=VRI=BJT vs PTS, both valid → variant with higher confidence."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhamma')
            assert result['type'] == 'variant'
            assert result['confidence'] >= 0.8

    def test_variant_with_full_majority(self):
        """SC=VRI=BJT=Thai vs PTS → variant with 0.9 confidence."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhamma', thai='dhamma')
            assert result['type'] == 'variant'
            assert result['confidence'] >= 0.9

    def test_variant_bjt_with_pts(self):
        """SC=VRI vs PTS+BJT, both valid → variant with reduced confidence."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhammo', 'dhamma', 'dhamma',
                                     bjt='dhammo')
            assert result['type'] == 'variant'
            assert result['confidence'] <= 0.7  # Reduced due to split


class TestClassifyVariantMultiWay:
    """Test multi-way disagreement paths."""

    def test_three_way_disagreement(self):
        """All three G/S/V disagree."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhammo', 'dhammā')
            assert result['type'] == 'uncertain'

    def test_three_way_with_bjt_creating_majority(self):
        """G/S/V disagree but BJT creates 2-witness coalition."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhammo', 'dhammā',
                                     bjt='dhamma')
            assert result['type'] == 'uncertain'
            # PTS+BJT coalition of 2
            assert result['confidence'] >= 0.4


class TestClassifyVariantEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_g_not_none_after_guard(self):
        """g_norm is always non-None after the early return on line 460."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            # This tests the chained equality path at line 470
            # g='dhamma', s=None, v=None → g_norm≠None, s_norm=None, v_norm=None
            # So 'dhamma' == None == None → False. Should NOT be orthographic.
            result = classify_variant('dhamma', None, None)
            assert result['type'] == 'pts_addition'  # Caught by earlier guard

    def test_sangha_normalization_orthographic(self):
        """saṅgha vs saṃgha should normalize to orthographic."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('saṅgha', 'saṃgha', 'saṃgha')
            assert result['type'] == 'orthographic'

    def test_sc_only_missing_vri(self):
        """SC present but VRI missing — falls through to PTS=SC vs VRI path."""
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            result = classify_variant('dhamma', 'dhamma', None)
            # PTS=SC agree, VRI is missing → vri_variant path
            assert result['type'] in ('orthographic', 'uncertain', 'variant', 'vri_variant')

    def test_result_always_has_required_keys(self):
        """Every result should have type, confidence, preferred, notes."""
        test_cases = [
            ('dhamma', 'dhamma', 'dhamma'),
            ('dhamma', None, None),
            (None, 'dhamma', 'dhamma'),
            ('', '', ''),
        ]
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            for g, s, v in test_cases:
                result = classify_variant(g, s, v)
                assert 'type' in result, f"Missing 'type' for {g}/{s}/{v}"
                assert 'confidence' in result, f"Missing 'confidence' for {g}/{s}/{v}"
                assert 'preferred' in result, f"Missing 'preferred' for {g}/{s}/{v}"
                assert 'notes' in result, f"Missing 'notes' for {g}/{s}/{v}"

    def test_confidence_range(self):
        """Confidence should always be between 0 and 1."""
        test_cases = [
            ('dhamma', 'dhamma', 'dhamma'),
            ('dhammo', 'dhamma', 'dhamma'),
            ('dhamma', 'dhammo', 'dhammā'),
            (None, 'dhamma', 'dhamma'),
            ('dhamma', None, None),
        ]
        with patch('collate_nikaya.is_valid_word', mock_valid_always):
            for g, s, v in test_cases:
                result = classify_variant(g, s, v)
                assert 0 <= result['confidence'] <= 1.0, \
                    f"Confidence {result['confidence']} out of range for {g}/{s}/{v}"
