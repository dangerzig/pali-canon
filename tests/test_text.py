"""Tests for pali.text — shared text utilities."""

import pytest
from pali.text import (
    tokenize, word_count, tokenize_with_positions,
    parse_sutta_id, normalize_pali, normalize_title,
    iter_file_segments, PALI_WORD_PATTERN, KN_TEXT_PREFIXES,
    VINAYA_TEXT_IDS, ABHIDHAMMA_TEXT_IDS,
)


# =========================================================================
# tokenize()
# =========================================================================

class TestTokenize:
    def test_basic(self):
        assert tokenize("Evaṃ me sutaṃ") == ["evaṃ", "me", "sutaṃ"]

    def test_lowercase(self):
        result = tokenize("Dīgha Nikāya")
        assert result == ["dīgha", "nikāya"]

    def test_diacritics(self):
        result = tokenize("āīūṭḍṇṅñṃḷ")
        assert result == ["āīūṭḍṇṅñṃḷ"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_strips_punctuation(self):
        result = tokenize("dhamma, saṅgha; buddha.")
        assert result == ["dhamma", "saṅgha", "buddha"]

    def test_strips_numbers(self):
        result = tokenize("sutta 123 text")
        assert result == ["sutta", "text"]

    def test_strips_brackets(self):
        result = tokenize("[PTS I.1] evaṃ")
        assert result == ["pts", "i", "evaṃ"]


# =========================================================================
# word_count()
# =========================================================================

class TestWordCount:
    def test_basic(self):
        assert word_count("Evaṃ me sutaṃ") == 3

    def test_matches_tokenize_length(self):
        text = "Ekaṃ samayaṃ bhagavā sāvatthiyaṃ viharati"
        assert word_count(text) == len(tokenize(text))

    def test_empty(self):
        assert word_count("") == 0

    def test_ignores_punctuation(self):
        assert word_count("dhamma, saṅgha; buddha.") == 3


# =========================================================================
# tokenize_with_positions()
# =========================================================================

class TestTokenizeWithPositions:
    def test_returns_tuple(self):
        words, positions = tokenize_with_positions("Evaṃ me sutaṃ")
        assert isinstance(words, list)
        assert isinstance(positions, list)
        assert len(words) == len(positions)

    def test_words_match_tokenize(self):
        text = "Evaṃ me sutaṃ"
        words, _ = tokenize_with_positions(text)
        assert words == tokenize(text)

    def test_positions_are_char_offsets(self):
        text = "Evaṃ me sutaṃ"
        words, positions = tokenize_with_positions(text)
        # First word starts at 0
        assert positions[0] == 0
        # Each position lets you find the word in original text
        for word, pos in zip(words, positions):
            assert text[pos:pos + len(word)].lower() == word

    def test_with_punctuation(self):
        text = "[1] evaṃ me"
        words, positions = tokenize_with_positions(text)
        assert words == ["evaṃ", "me"]
        assert text[positions[0]:positions[0] + 4] == "evaṃ"


# =========================================================================
# parse_sutta_id()
# =========================================================================

class TestParseSuttaId:
    def test_dn(self):
        assert parse_sutta_id("dn1") == "dn"
        assert parse_sutta_id("dn34") == "dn"

    def test_mn(self):
        assert parse_sutta_id("mn1") == "mn"
        assert parse_sutta_id("mn152") == "mn"

    def test_sn(self):
        assert parse_sutta_id("sn1.1") == "sn"
        assert parse_sutta_id("sn56.11") == "sn"

    def test_an(self):
        assert parse_sutta_id("an1.1") == "an"
        assert parse_sutta_id("an11.15") == "an"

    def test_kn_dhp(self):
        assert parse_sutta_id("dhp1") == "kn"
        assert parse_sutta_id("dhp1-20") == "kn"

    def test_kn_snp(self):
        # "snp" should match KN, not "sn"
        assert parse_sutta_id("snp1.1") == "kn"

    def test_kn_all_prefixes(self):
        for prefix in KN_TEXT_PREFIXES:
            assert parse_sutta_id(f"{prefix}1") == "kn", f"{prefix} should map to kn"

    def test_kn_itself(self):
        assert parse_sutta_id("kn") == "kn"

    def test_unknown(self):
        assert parse_sutta_id("xyz123") is None
        assert parse_sutta_id("") is None

    def test_thag_thig(self):
        assert parse_sutta_id("thag1.1") == "kn"
        assert parse_sutta_id("thig1.1") == "kn"

    def test_apadana_prefixes(self):
        assert parse_sutta_id("tha-ap1") == "kn"
        assert parse_sutta_id("thi-ap1") == "kn"

    def test_vinaya_text_ids(self):
        for text_id in VINAYA_TEXT_IDS:
            assert parse_sutta_id(text_id) == "vinaya", f"{text_id} should map to vinaya"

    def test_abhidhamma_text_ids(self):
        for text_id in ABHIDHAMMA_TEXT_IDS:
            assert parse_sutta_id(text_id) == "abhidhamma", f"{text_id} should map to abhidhamma"

    def test_vinaya_not_kn(self):
        # Vinaya IDs should not be confused with KN prefixes
        assert parse_sutta_id("mahavagga") == "vinaya"
        assert parse_sutta_id("cullavagga") == "vinaya"

    def test_abhidhamma_not_other(self):
        assert parse_sutta_id("dhammasangani") == "abhidhamma"
        assert parse_sutta_id("patthana") == "abhidhamma"


# =========================================================================
# normalize_pali()
# =========================================================================

class TestNormalizePali:
    def test_niggahita_normalization(self):
        assert normalize_pali("evaṁ me sutaṁ") == "evaṃ me sutaṃ"

    def test_whitespace_normalization(self):
        assert normalize_pali("evaṃ  me   sutaṃ") == "evaṃ me sutaṃ"

    def test_strip_whitespace(self):
        assert normalize_pali("  evaṃ me  ") == "evaṃ me"

    def test_tabs_and_newlines(self):
        assert normalize_pali("evaṃ\tme\nsutaṃ") == "evaṃ me sutaṃ"

    def test_combined(self):
        assert normalize_pali("  evaṁ  me  ") == "evaṃ me"


# =========================================================================
# normalize_title()
# =========================================================================

class TestNormalizeTitle:
    def test_strips_sutta_suffix(self):
        assert normalize_title("Brahmajālasutta") == "brahmajāla"

    def test_strips_suttam_suffix(self):
        assert normalize_title("Brahmajālasuttaṃ") == "brahmajāla"

    def test_strips_ordinal_prefix(self):
        assert normalize_title("Paṭhama Brahmajāla") == "brahmajāla"
        assert normalize_title("Dutiya Kosala") == "kosala"
        assert normalize_title("Tatiya Ānanda") == "ānanda"

    def test_lowercases(self):
        assert normalize_title("BRAHMAJĀLA") == "brahmajāla"

    def test_removes_whitespace(self):
        assert normalize_title("Brahma jāla suttaṃ") == "brahmajāla"

    def test_combined(self):
        assert normalize_title("Paṭhama Brahmajāla Suttaṃ") == "brahmajāla"


# =========================================================================
# iter_file_segments()
# =========================================================================

class TestIterFileSegments:
    def test_dn_mn_structure(self):
        data = {
            "id": "dn1",
            "segments": [
                {"id": "dn1:1.1", "pali": "Evaṃ me sutaṃ."},
                {"id": "dn1:1.2", "pali": "Ekaṃ samayaṃ."},
            ]
        }
        results = list(iter_file_segments(data, "dn"))
        assert len(results) == 1
        doc_id, segments = results[0]
        assert doc_id == "dn1"
        assert len(segments) == 2

    def test_sn_an_structure(self):
        data = {
            "id": "sn1",
            "suttas": [
                {"id": "sn1.1", "segments": [{"id": "sn1.1:1.1", "pali": "A"}]},
                {"id": "sn1.2", "segments": [{"id": "sn1.2:1.1", "pali": "B"}]},
            ]
        }
        results = list(iter_file_segments(data, "sn"))
        assert len(results) == 2
        assert results[0][0] == "sn1.1"
        assert results[1][0] == "sn1.2"

    def test_kn_items_structure(self):
        data = {
            "id": "dhp",
            "items": [
                {"id": "dhp1-20", "segments": [{"id": "dhp1-20:1", "pali": "C"}]},
                {"id": "dhp21-32", "segments": [{"id": "dhp21-32:1", "pali": "D"}]},
            ]
        }
        results = list(iter_file_segments(data, "kn"))
        assert len(results) == 2
        assert results[0][0] == "dhp1-20"

    def test_kn_flat_structure(self):
        data = {
            "id": "mil",
            "segments": [{"id": "mil:1.1", "pali": "E"}]
        }
        results = list(iter_file_segments(data, "kn"))
        assert len(results) == 1
        assert results[0][0] == "mil"

    def test_empty_segments(self):
        data = {"id": "dn1", "segments": []}
        results = list(iter_file_segments(data, "dn"))
        assert len(results) == 1
        assert results[0][1] == []
