"""Tests for pali.custom_lemmas — custom lemma lookups."""

import pytest
from pali.custom_lemmas import (
    get_custom_lemma, get_all_custom_words, get_potential_dpd_additions,
    CUSTOM_LEMMAS, CUSTOM_SANDHI,
    POTENTIAL_DPD_ADDITIONS, METRICAL_VARIANTS, PROJECT_SPECIFIC,
    SANDHI_DECOMPOSITIONS,
)


# =========================================================================
# get_custom_lemma()
# =========================================================================

class TestGetCustomLemma:
    def test_known_direct_lemma(self):
        # Pick a word we know is in the config
        if CUSTOM_LEMMAS:
            word = next(iter(CUSTOM_LEMMAS))
            result = get_custom_lemma(word)
            assert result is not None
            assert "lemma" in result
            assert "pos" in result

    def test_known_sandhi(self):
        if CUSTOM_SANDHI:
            word = next(iter(CUSTOM_SANDHI))
            result = get_custom_lemma(word)
            assert result is not None
            assert "sandhi" in result
            assert "components" in result

    def test_unknown_word(self):
        result = get_custom_lemma("xyznonexistent")
        assert result is None

    def test_case_insensitive(self):
        if CUSTOM_LEMMAS:
            word = next(iter(CUSTOM_LEMMAS))
            # Test uppercase version
            result_upper = get_custom_lemma(word.upper())
            result_lower = get_custom_lemma(word.lower())
            # Both should find the same entry (since lookup lowercases)
            assert result_upper == result_lower

    def test_empty_string(self):
        result = get_custom_lemma("")
        assert result is None


# =========================================================================
# get_all_custom_words()
# =========================================================================

class TestGetAllCustomWords:
    def test_returns_set(self):
        words = get_all_custom_words()
        assert isinstance(words, set)

    def test_includes_all_categories(self):
        words = get_all_custom_words()
        # Should include direct lemmas
        for word in CUSTOM_LEMMAS:
            assert word in words
        # Should include sandhi
        for word in CUSTOM_SANDHI:
            assert word in words

    def test_non_empty(self):
        words = get_all_custom_words()
        assert len(words) > 0


# =========================================================================
# get_potential_dpd_additions()
# =========================================================================

class TestGetPotentialDpdAdditions:
    def test_returns_dict(self):
        additions = get_potential_dpd_additions()
        assert isinstance(additions, dict)

    def test_returns_copy(self):
        additions1 = get_potential_dpd_additions()
        additions2 = get_potential_dpd_additions()
        # Modifying one shouldn't affect the other
        additions1["__test__"] = ("test", "test")
        assert "__test__" not in additions2

    def test_entry_format(self):
        additions = get_potential_dpd_additions()
        for word, value in additions.items():
            assert isinstance(value, tuple), f"{word}: expected tuple, got {type(value)}"
            assert len(value) == 2, f"{word}: expected (lemma, pos) tuple"
            lemma, pos = value
            assert isinstance(lemma, str), f"{word}: lemma should be str"
            assert isinstance(pos, str), f"{word}: pos should be str"


# =========================================================================
# Dictionary consistency
# =========================================================================

class TestDictionaryConsistency:
    def test_no_overlap_direct_and_sandhi(self):
        """Direct lemma entries should not overlap with sandhi entries."""
        overlap = set(CUSTOM_LEMMAS.keys()) & set(CUSTOM_SANDHI.keys())
        assert overlap == set(), f"Overlap between direct and sandhi: {overlap}"

    def test_all_pos_tags_valid(self):
        """All POS tags should be recognized values."""
        valid_pos = {
            "noun", "verb", "adj", "adv", "ind", "pron", "pp", "prp",
            "ptp", "ger", "inf", "caus", "pass", "deno", "desid",
            "prefix", "suffix", "cs", "abs", "aor", "card", "fem",
            "fpp", "imp", "masc", "name", "nt",
        }
        for word, (lemma, pos) in CUSTOM_LEMMAS.items():
            assert pos in valid_pos, f"{word}: unknown POS tag '{pos}'"

    def test_sandhi_parts_match_components(self):
        """Sandhi parts count should match components count."""
        for word, (parts, components) in SANDHI_DECOMPOSITIONS.items():
            assert len(parts) == len(components), (
                f"{word}: {len(parts)} parts but {len(components)} components"
            )


# =========================================================================
# reload_config()
# =========================================================================

class TestYamlValidation:
    def test_malformed_lemma_entries_skipped(self):
        """Malformed entries (non-dict, missing keys) should be silently skipped."""
        from pali.custom_lemmas import _build_lemma_dict, _CONFIG
        import copy

        # Save original config
        original = copy.deepcopy(_CONFIG)

        # Inject malformed entries
        _CONFIG['potential_dpd_additions'] = {
            'good_word': {'lemma': 'test', 'pos': 'noun'},
            'bad_string': 'not_a_dict',
            'bad_missing_lemma': {'pos': 'noun'},
            'bad_missing_pos': {'lemma': 'test'},
            'bad_none': None,
        }

        result = _build_lemma_dict('potential_dpd_additions')

        # Only the good entry should survive
        assert 'good_word' in result
        assert len(result) == 1

        # Restore
        _CONFIG.clear()
        _CONFIG.update(original)

    def test_malformed_sandhi_entries_skipped(self):
        """Malformed sandhi entries should be silently skipped."""
        from pali.custom_lemmas import _build_sandhi_dict, _CONFIG
        import copy

        original = copy.deepcopy(_CONFIG)

        _CONFIG['sandhi_decompositions'] = {
            'good_word': {'parts': ['a', 'b'], 'components': [{'lemma': 'a', 'pos': 'noun'}, {'lemma': 'b', 'pos': 'noun'}]},
            'bad_string': 'not_a_dict',
            'bad_missing_parts': {'components': []},
        }

        result = _build_sandhi_dict()
        assert 'good_word' in result
        assert len(result) == 1

        _CONFIG.clear()
        _CONFIG.update(original)


class TestReloadConfig:
    def test_reload_preserves_data(self):
        from pali.custom_lemmas import reload_config
        # Record state before reload
        words_before = get_all_custom_words()
        reload_config()
        words_after = get_all_custom_words()
        assert words_before == words_after

    def test_reload_repopulates_dicts(self):
        from pali.custom_lemmas import reload_config
        reload_config()
        # All dicts should be populated after reload
        assert len(CUSTOM_LEMMAS) > 0
        assert len(CUSTOM_SANDHI) > 0
        assert len(POTENTIAL_DPD_ADDITIONS) > 0
