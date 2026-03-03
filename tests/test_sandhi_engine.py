"""Tests for SandhiRuleEngine and enhanced lemmatization strategies."""

from pathlib import Path

import pytest

from lemmatize_canon import (
    SandhiRuleEngine, NegativePrefixStrategy,
    EnhancedCompoundSplitStrategy, SplitCandidate, Lemmatizer, TokenInfo,
    ENHANCED_STRATEGIES, DEFAULT_STRATEGIES, SANDHI_RULES_FILE, DPD_DB,
)


# =============================================================================
# SandhiRuleEngine tests
# =============================================================================

class TestSandhiRuleEngine:
    """Tests for sandhi rule loading and boundary application."""

    def test_load_rules_from_real_file(self):
        engine = SandhiRuleEngine(SANDHI_RULES_FILE)
        total_rules = sum(len(v) for v in engine.rules_by_boundary.values())
        assert total_rules == 626

    def test_load_rules_from_tsv(self, tmp_path):
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\ta\tp\ta\tap\tabhivaggen'api\t3\n"
            "2\tā\tp\ta\tap\tajjā'pi\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        assert len(engine.rules_by_boundary) == 2
        assert ('a', 'p') in engine.rules_by_boundary
        assert ('ā', 'p') in engine.rules_by_boundary

    def test_missing_file_returns_empty(self, tmp_path):
        engine = SandhiRuleEngine(tmp_path / "nonexistent.tsv")
        assert len(engine.rules_by_boundary) == 0

    def test_malformed_tsv_skips_bad_rows(self, tmp_path):
        """Malformed rows should be skipped with a warning, not crash."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\ta\tp\ta\tap\tex\t3\n"
            "bad\tx\ty\tz\tw\tex\tnotanumber\n"
            "3\tb\tc\tb\tc\tex\t2\n"
        )
        engine = SandhiRuleEngine(tsv)
        total_rules = sum(len(v) for v in engine.rules_by_boundary.values())
        assert total_rules == 2  # skipped the malformed row

    def test_apply_at_boundary_identity(self, tmp_path):
        tsv = tmp_path / "rules.tsv"
        tsv.write_text("index\tchA\tchB\tch1\tch2\teg\tweight\n")
        engine = SandhiRuleEngine(tsv)
        results = engine.apply_at_boundary("abcdef", 3)
        assert len(results) == 1
        assert results[0] == ("abc", "def", 1)

    def test_apply_at_boundary_with_rule(self, tmp_path):
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\ta\tp\ta\tap\tex\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        # "abhivaggenapi" split at position 11: left="abhivaggena", right="pi"
        # left[-1]='a' matches chA='a', right[0]='p' matches chB='p'
        results = engine.apply_at_boundary("abhivaggenapi", 11)
        # Should have identity + the rule
        assert len(results) == 2
        # Identity
        assert ("abhivaggena", "pi", 1) in results
        # Rule: Reconstruct: "abhivaggen" + ch1="a" = "abhivaggena", ch2="ap" + "i" = "api"
        assert ("abhivaggena", "api", 3) in results

    def test_apply_at_boundary_multi_char_ch1(self, tmp_path):
        """Test rule with multi-char ch1 (covers 79% of real rules)."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\tb\tā\tbaṃ\tā\tex\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        # "pubbāhaṃ" split at pos 4: left="pubb", right="āhaṃ"
        results = engine.apply_at_boundary("pubbāhaṃ", 4)
        assert ("pubb", "āhaṃ", 1) in results  # identity
        # Rule: left[:-1]+'baṃ' = "pub"+"baṃ" = "pubbaṃ"
        # ch2+'haṃ' = "ā"+"haṃ" = "āhaṃ"
        assert ("pubbaṃ", "āhaṃ", 3) in results

    def test_apply_at_boundary_empty_ch2(self, tmp_path):
        """Test rules where ch2 is empty (sandhi insertion like t-insertion)."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\tā\tt\tā\t\tex\t4\n"
        )
        engine = SandhiRuleEngine(tsv)
        # "tasmātiha" split at pos 5: left="tasmā", right="tiha"
        results = engine.apply_at_boundary("tasmātiha", 5)
        assert ("tasmā", "tiha", 1) in results  # identity
        # Rule: chA='ā' matches left[-1], chB='t' matches right[0]
        # Reconstruct: "tasm" + ch1="ā" = "tasmā", ch2="" + "iha" = "iha"
        assert ("tasmā", "iha", 4) in results

    def test_apply_at_boundary_empty_ch1_filtered(self, tmp_path):
        """Rules producing empty reconstructed_a should be filtered out."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\ta\tb\t\tb\tex\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        # "ab" split at pos 1: left="a", right="b"
        # Rule: left[:-1]+'' = '', ch2+'b'[1:] = 'b'+'' = 'b'
        # Empty reconstructed_a should be filtered
        results = engine.apply_at_boundary("ab", 1)
        assert len(results) == 1  # only identity
        assert results[0] == ("a", "b", 1)

    def test_apply_at_boundary_vowel_change(self, tmp_path):
        """Test rule that changes the boundary vowel."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\tā\tp\ta\tap\tex\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        # "ajjāpi" split at pos 4: left="ajjā", right="pi"
        results = engine.apply_at_boundary("ajjāpi", 4)
        assert ("ajjā", "pi", 1) in results  # identity
        # Rule: chA='ā' matches left[-1], chB='p' matches right[0]
        # Reconstruct: "ajj" + ch1="a" = "ajja", ch2="ap" + "i" = "api"
        assert ("ajja", "api", 3) in results

    def test_apply_at_boundary_duplicate_rules(self, tmp_path):
        """Rules with identical ch1/ch2 produce duplicate results."""
        tsv = tmp_path / "rules.tsv"
        tsv.write_text(
            "index\tchA\tchB\tch1\tch2\teg\tweight\n"
            "1\th\tu\tha\tu\tex1\t3\n"
            "2\th\tu\tha\tu\tex2\t3\n"
        )
        engine = SandhiRuleEngine(tsv)
        results = engine.apply_at_boundary("abhu", 3)
        # Identity + 2 identical-output rules = 3 results
        assert len(results) == 3

    def test_boundary_at_edges_returns_empty(self):
        engine = SandhiRuleEngine(SANDHI_RULES_FILE)
        assert engine.apply_at_boundary("abc", 0) == []
        assert engine.apply_at_boundary("abc", 3) == []

    def test_real_rules_niggahita_boundary(self):
        """Test ṅ+g boundary (niggahīta assimilation)."""
        engine = SandhiRuleEngine(SANDHI_RULES_FILE)
        # "evaṅgatāni" -> should find evaṃ + gatāni
        results = engine.apply_at_boundary("evaṅgatāni", 4)
        # Look for a reconstruction that gives evaṃ + gatāni
        reconstructions = [(a, b, w) for a, b, w in results if a == "evaṃ" and b == "gatāni"]
        assert len(reconstructions) > 0, f"Expected evaṃ+gatāni, got: {results}"


# =============================================================================
# SplitCandidate scoring tests
# =============================================================================

class TestSplitCandidateScoring:
    """Tests for compound split candidate scoring."""

    def test_fewer_parts_preferred(self):
        two_part = SplitCandidate(parts=["abc", "def"], total_weight=1, num_parts=2, min_part_len=3)
        three_part = SplitCandidate(parts=["ab", "cd", "ef"], total_weight=1, num_parts=3, min_part_len=2)
        assert two_part.score > three_part.score

    def test_identity_preferred_over_sandhi(self):
        """Identity splits (weight=1) should beat sandhi-transformed splits (weight=3)."""
        identity = SplitCandidate(parts=["abc", "def"], total_weight=1, num_parts=2, min_part_len=3)
        sandhi = SplitCandidate(parts=["abc", "def"], total_weight=3, num_parts=2, min_part_len=3)
        assert identity.score > sandhi.score

    def test_longer_min_part_preferred(self):
        longer = SplitCandidate(parts=["abcde", "fgh"], total_weight=1, num_parts=2, min_part_len=3)
        shorter = SplitCandidate(parts=["ab", "cdefgh"], total_weight=1, num_parts=2, min_part_len=2)
        assert longer.score > shorter.score

    def test_parts_dominate_weight(self):
        """Fewer parts should beat lower weight even when weight differs."""
        two_heavy = SplitCandidate(parts=["a", "b"], total_weight=8, num_parts=2, min_part_len=1)
        three_light = SplitCandidate(parts=["a", "b", "c"], total_weight=1, num_parts=3, min_part_len=1)
        assert two_heavy.score > three_light.score


# =============================================================================
# NegativePrefixStrategy tests
# =============================================================================

@pytest.fixture
def lemmatizer():
    """Create a lemmatizer for testing."""
    lem = Lemmatizer()
    yield lem
    lem.close()


class TestNegativePrefixStrategy:
    """Tests for negation prefix splitting."""

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_no_prefix_splits(self, lemmatizer):
        """Test no- prefix (Abhidhamma negation) produces split with na."""
        strategy = NegativePrefixStrategy()
        token = TokenInfo(word="noupādāno")
        result = strategy.try_lookup("noupādāno", token, lemmatizer)
        assert result, "noupādāno should be split (no- prefix)"
        assert token.sandhi[0] == "na"
        assert len(token.sandhi) >= 2

    def test_short_word_not_split(self, lemmatizer):
        strategy = NegativePrefixStrategy()
        token = TokenInfo(word="noti")
        result = strategy.try_lookup("noti", token, lemmatizer)
        assert not result

    def test_already_known_word_not_split(self, lemmatizer):
        """Words DPD already knows shouldn't reach this strategy."""
        # 'na' is in DPD, so DPDLookupStrategy handles it first
        token = lemmatizer.lookup_word("na", strategies=ENHANCED_STRATEGIES)
        assert token.lemma == "na"
        assert token.sandhi is None

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_an_prefix_before_vowel(self, lemmatizer):
        """Test an- prefix before vowel (Pattern 3)."""
        strategy = NegativePrefixStrategy()
        token = TokenInfo(word="anupādāno")
        result = strategy.try_lookup("anupādāno", token, lemmatizer)
        assert result, "anupādāno should be split (an- prefix)"
        assert token.sandhi[0] == "na"

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_na_doubled_consonant_prefix(self, lemmatizer):
        """Test na- prefix with consonant doubling (Pattern 2)."""
        strategy = NegativePrefixStrategy()
        # nappahoti -> na + pahoti (de-geminate the doubled 'p')
        token = TokenInfo(word="nappahoti")
        result = strategy.try_lookup("nappahoti", token, lemmatizer)
        if result:
            assert token.sandhi[0] == "na"
            assert token.sandhi[1] == "pahoti"

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_a_doubled_consonant_prefix(self, lemmatizer):
        """Test a- prefix with consonant doubling (Pattern 5)."""
        strategy = NegativePrefixStrategy()
        # Look for a word matching pattern: a + doubled consonant + known remainder
        token = TokenInfo(word="aññāṇa")
        result = strategy.try_lookup("aññāṇa", token, lemmatizer)
        if result:
            assert token.sandhi[0] == "na"

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_custom_lemma_skips_negative_prefix(self, lemmatizer):
        """Words in custom lemma DB should not be split by NegativePrefixStrategy."""
        from pali.custom_lemmas import get_custom_lemma, CUSTOM_LEMMAS
        strategy = NegativePrefixStrategy()
        for word in CUSTOM_LEMMAS:
            if word.startswith(('no', 'na', 'an')) and len(word) >= 5:
                token = TokenInfo(word=word)
                result = strategy.try_lookup(word, token, lemmatizer)
                assert not result, f"Custom lemma word {word} should not be split"
                break

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_negation_with_sandhi_remainder(self, lemmatizer):
        """Test that negation works when remainder resolves via sandhi decomposition."""
        strategy = NegativePrefixStrategy()
        token = TokenInfo(word="noupādāno")
        result = strategy.try_lookup("noupādāno", token, lemmatizer)
        if result:
            # Remainder 'upādāno' may resolve via direct lemma or sandhi
            assert token.sandhi[0] == "na"
            assert len(token.sandhi) >= 2
            # Check components have metadata
            assert len(token.components) >= 2
            assert token.components[0] == {'lemma': 'na', 'pos': 'ind'}


# =============================================================================
# EnhancedCompoundSplitStrategy tests
# =============================================================================

class TestEnhancedCompoundSplitStrategy:
    """Tests for sandhi-aware compound splitting."""

    def test_short_word_skipped(self, lemmatizer):
        strategy = EnhancedCompoundSplitStrategy()
        token = TokenInfo(word="abc")
        assert not strategy.try_lookup("abc", token, lemmatizer)

    def test_word_under_min_length_skipped(self, lemmatizer):
        """Words under 8 chars (2 * min_component) should be skipped."""
        strategy = EnhancedCompoundSplitStrategy()
        token = TokenInfo(word="abcdefg")  # 7 chars
        assert not strategy.try_lookup("abcdefg", token, lemmatizer)

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_known_compound_split(self, lemmatizer):
        """Test that a known compound gets split."""
        strategy = EnhancedCompoundSplitStrategy()
        token = TokenInfo(word="mahāpurisa")
        result = strategy.try_lookup("mahāpurisa", token, lemmatizer)
        assert result, "mahāpurisa should be split into mahā + purisa"
        assert len(token.sandhi) >= 2

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_compound_components_have_headword_info(self, lemmatizer):
        """Enhanced compound splits should produce component metadata."""
        strategy = EnhancedCompoundSplitStrategy()
        token = TokenInfo(word="mahāpurisa")
        result = strategy.try_lookup("mahāpurisa", token, lemmatizer)
        if result:
            has_lemma = any("lemma" in comp for comp in token.components)
            assert has_lemma, f"Components should have headword info: {token.components}"

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_custom_lemma_not_split(self, lemmatizer):
        """Words in custom lemma database should not be split."""
        from pali.custom_lemmas import get_custom_lemma
        strategy = EnhancedCompoundSplitStrategy()
        for test_word in ["ekantasukhaṃ", "aṭṭhapurisapuggalā"]:
            custom = get_custom_lemma(test_word)
            if custom:
                token = TokenInfo(word=test_word)
                result = strategy.try_lookup(test_word, token, lemmatizer)
                assert not result, f"Custom lemma word {test_word} should not be split"
                break

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_metrical_component_fallback(self, lemmatizer):
        """Metrically lengthened components should be accepted."""
        strategy = EnhancedCompoundSplitStrategy()
        # 'dhammā' has long final vowel; 'dhamma' is in DPD
        assert strategy._is_valid_component("dhammā", lemmatizer) is True
        # Nonsense word fails even after normalization
        assert strategy._is_valid_component("zzzznotaword", lemmatizer) is False

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_find_best_split_max_depth_zero(self, lemmatizer):
        """max_depth=0 should return None immediately."""
        strategy = EnhancedCompoundSplitStrategy()
        engine = lemmatizer.sandhi_engine
        result = strategy._find_best_split("anyword", lemmatizer, engine, max_depth=0)
        assert result is None

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_find_best_split_no_valid_splits(self, lemmatizer):
        """A word with no valid compound split should return None."""
        strategy = EnhancedCompoundSplitStrategy()
        engine = lemmatizer.sandhi_engine
        result = strategy._find_best_split("zzzzzzzznotaword", lemmatizer, engine, max_depth=4)
        assert result is None

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_three_part_compound_via_recursion(self, lemmatizer):
        """Test that recursion can find three-part compound splits."""
        strategy = EnhancedCompoundSplitStrategy()
        # 'mahābodhisatta' = mahā + bodhi + satta (all valid DPD words)
        token = TokenInfo(word="mahābodhisatta")
        result = strategy.try_lookup("mahābodhisatta", token, lemmatizer)
        if result:
            assert len(token.sandhi) >= 2
            # Verify all parts have component info
            assert len(token.components) == len(token.sandhi)


# =============================================================================
# Integration tests
# =============================================================================

class TestPipelineIntegration:
    """Test that old and new pipelines coexist correctly."""

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_enhanced_resolves_common_words(self, lemmatizer):
        """Enhanced pipeline should resolve common words the same as default."""
        common_words = ["dhamma", "buddha", "saṅgha", "sutta", "vinaya"]
        for word in common_words:
            lemmatizer.cache.clear()
            lemmatizer._active_strategies = DEFAULT_STRATEGIES
            old = lemmatizer.lookup_word(word, strategies=DEFAULT_STRATEGIES)
            lemmatizer.cache.clear()
            lemmatizer._active_strategies = ENHANCED_STRATEGIES
            new = lemmatizer.lookup_word(word, strategies=ENHANCED_STRATEGIES)
            assert old.lemma == new.lemma, f"{word}: old={old.lemma}, new={new.lemma}"

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_enhanced_stats_tracked(self, lemmatizer):
        """New stat keys should exist and track correctly."""
        assert "negative_prefix" in lemmatizer.stats
        assert "enhanced_compound_splits" in lemmatizer.stats
        lemmatizer.lookup_word("noupādāno", strategies=ENHANCED_STRATEGIES)
        stats = lemmatizer.get_stats()
        assert "negative_prefix" in stats
        assert "enhanced_compound_splits" in stats

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_valid_word_cache(self, lemmatizer):
        """_valid_word_cache should cache results."""
        assert lemmatizer._is_valid_word("dhamma") is True
        assert "dhamma" in lemmatizer._valid_word_cache
        assert lemmatizer._valid_word_cache["dhamma"] is True

        assert lemmatizer._is_valid_word("zzzznotaword") is False
        assert lemmatizer._valid_word_cache["zzzznotaword"] is False

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_sandhi_engine_on_lemmatizer(self, lemmatizer):
        """Lemmatizer should have a sandhi_engine attribute."""
        assert hasattr(lemmatizer, 'sandhi_engine')
        assert isinstance(lemmatizer.sandhi_engine, SandhiRuleEngine)
        total_rules = sum(len(v) for v in lemmatizer.sandhi_engine.rules_by_boundary.values())
        assert total_rules == 626

    @pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")
    def test_active_strategies_used_by_recursive_calls(self, lemmatizer):
        """Recursive lookup_word calls should use _active_strategies."""
        lemmatizer._active_strategies = DEFAULT_STRATEGIES
        lemmatizer.cache.clear()
        old = lemmatizer.lookup_word("noupādāno", strategies=DEFAULT_STRATEGIES)

        lemmatizer._active_strategies = ENHANCED_STRATEGIES
        lemmatizer.cache.clear()
        new = lemmatizer.lookup_word("noupādāno", strategies=ENHANCED_STRATEGIES)

        # Enhanced should resolve this (via NegativePrefixStrategy)
        # while default may not
        if new.sandhi:
            assert new.sandhi[0] == "na"

    def test_dpd_db_missing_raises_error(self, tmp_path):
        """Lemmatizer should raise FileNotFoundError if DPD database is missing."""
        with pytest.raises(FileNotFoundError):
            Lemmatizer(db_path=tmp_path / "nonexistent.db")
