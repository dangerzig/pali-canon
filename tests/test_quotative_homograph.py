"""Tests for the quotative-split and verb-homograph fixes in lemmatize_canon.

Covers:
- Bug A: reconstruction-gated quotative splits (jānaṃ+iti rejected for jānāti;
  valid quotatives kept).
- Bug B: POS-gated homograph override (jānāti -> verb, not adj `ja`), with no
  pronoun/noun regressions.
- -nti extension: 3rd-plural finite verbs (santi, bhavissanti) not mis-split as
  quotatives, while genuine -nti quotatives (evanti) are kept.
- The _iti_surface_forms and _is_finite_verb helpers.
"""

import pytest

from lemmatize_canon import (
    Lemmatizer, TokenInfo, ENHANCED_STRATEGIES, FINITE_VERB_POS, DPD_DB,
)

requires_dpd = pytest.mark.skipif(not DPD_DB.exists(), reason="DPD database not present")


@pytest.fixture
def lemmatizer():
    lem = Lemmatizer()
    yield lem
    lem.close()


# =============================================================================
# _iti_surface_forms (pure forward-sandhi enumeration; no DB needed)
# =============================================================================

class TestItiSurfaceForms:
    def test_empty_host(self, lemmatizer):
        assert lemmatizer._iti_surface_forms("") == set()

    def test_niggahita_host_produces_nti_and_miti(self, lemmatizer):
        forms = lemmatizer._iti_surface_forms("jānaṃ")
        assert "jānanti" in forms      # ṃ + iti -> ...nti
        assert "jānamiti" in forms     # ṃ + iti -> ...miti
        assert "jānāti" not in forms   # the spurious target must NOT reconstruct

    def test_niggahita_keeps_real_quotative(self, lemmatizer):
        # vimuttaṃ + iti -> vimuttamiti (must remain reconstructible)
        assert "vimuttamiti" in lemmatizer._iti_surface_forms("vimuttaṃ")

    def test_short_vowel_host_lengthens(self, lemmatizer):
        assert "hotīti" in lemmatizer._iti_surface_forms("hoti")   # i -> ī
        assert "atthīti" in lemmatizer._iti_surface_forms("atthi")

    def test_long_vowel_and_oe_host_absorbs_i(self, lemmatizer):
        assert "atthīti" in lemmatizer._iti_surface_forms("atthī")  # ī + iti
        assert "gammoti" in lemmatizer._iti_surface_forms("gammo")  # o + iti

    def test_hiatus_form(self, lemmatizer):
        # uncontracted dhamadhamā + iti -> dhamadhamāiti
        assert "dhamadhamāiti" in lemmatizer._iti_surface_forms("dhamadhamā")

    def test_metrically_lengthened_final(self, lemmatizer):
        # ...ti -> ...tī ; desessaṃ -> desessanti -> desessantī
        assert "desessantī" in lemmatizer._iti_surface_forms("desessaṃ")


# =============================================================================
# _is_finite_verb
# =============================================================================

class TestIsFiniteVerb:
    @requires_dpd
    def test_present_verb_is_finite(self, lemmatizer):
        assert lemmatizer._is_finite_verb("santi") is True   # 3pl pr of atthi
        assert lemmatizer._is_finite_verb("jānāti") is True

    @requires_dpd
    def test_noun_is_not_finite(self, lemmatizer):
        assert lemmatizer._is_finite_verb("dhamma") is False
        assert lemmatizer._is_finite_verb("evaṃ") is False

    @requires_dpd
    def test_unknown_word_is_not_finite(self, lemmatizer):
        assert lemmatizer._is_finite_verb("zzzznotaword") is False

    @requires_dpd
    def test_result_is_cached(self, lemmatizer):
        lemmatizer._is_finite_verb("santi")
        assert "santi" in lemmatizer._finite_verb_cache


# =============================================================================
# Bug A: reconstruction-gated quotative splits
# =============================================================================

class TestBugAQuotativeSplits:
    @requires_dpd
    def test_janati_not_split(self, lemmatizer):
        """jānāti must NOT be split as jānaṃ+iti (it doesn't reconstruct)."""
        t = lemmatizer.lookup_word("jānāti")
        assert t.sandhi is None
        assert t.lemma == "jānāti"
        assert t.pos == "pr"

    @requires_dpd
    def test_valid_quotative_kept_niggahita(self, lemmatizer):
        t = lemmatizer.lookup_word("vimuttamiti")
        assert t.sandhi == ["vimuttaṃ", "iti"]

    @requires_dpd
    def test_valid_quotative_kept_vowel(self, lemmatizer):
        t = lemmatizer.lookup_word("hotīti")
        assert t.sandhi == ["hoti", "iti"]

    @requires_dpd
    def test_nonreconstructing_primary_skipped_for_reconstructing_alt(self, lemmatizer):
        """atthīti: atthā+iti (primary) rejected, a reconstructing iti split kept."""
        t = lemmatizer.lookup_word("atthīti")
        assert t.sandhi is not None
        assert t.sandhi[0] != "atthā"
        assert t.sandhi[-1] == "iti"
        assert "atthīti" in lemmatizer._iti_surface_forms(t.sandhi[0])

    @requires_dpd
    def test_no_fallback_to_nonquotative_alt(self, lemmatizer):
        """visesīti must not fall back to the bogus non-quotative 'vise + asīti'."""
        t = lemmatizer.lookup_word("visesīti")
        assert t.sandhi != ["vise", "asīti"]

    @requires_dpd
    def test_select_deconstruction_rejects_impossible(self, lemmatizer):
        assert lemmatizer._select_deconstruction(["jānaṃ + iti"], "jānāti") is None

    @requires_dpd
    def test_select_deconstruction_keeps_reconstructing(self, lemmatizer):
        assert lemmatizer._select_deconstruction(["hoti + iti"], "hotīti") == ["hoti", "iti"]

    def test_select_deconstruction_nonquotative_uses_first(self, lemmatizer):
        # primary is non-quotative -> prior behaviour (use first), no DB needed
        assert lemmatizer._select_deconstruction(
            ["imaṃ + atthaṃ"], "imamatthaṃ") == ["imaṃ", "atthaṃ"]

    def test_select_deconstruction_empty(self, lemmatizer):
        assert lemmatizer._select_deconstruction([], "x") is None


# =============================================================================
# Bug B: POS-gated homograph override
# =============================================================================

class TestBugBHomograph:
    @requires_dpd
    def test_janati_lemmatized_as_verb_not_adj(self, lemmatizer):
        t = lemmatizer.lookup_word("jānāti")
        assert t.lemma == "jānāti"   # not the adj `ja` (DPD's headword[0])
        assert t.pos == "pr"

    @requires_dpd
    def test_lengthened_present_corrected(self, lemmatizer):
        t = lemmatizer.lookup_word("jānātī")
        assert t.lemma == "jānāti"
        assert t.pos == "pr"

    @requires_dpd
    @pytest.mark.parametrize("word,lemma", [
        ("so", "ta"), ("taṃ", "ta"), ("me", "ahaṃ"), ("bhagavā", "bhagavant"),
        ("yo", "ya"),
    ])
    def test_pronoun_holdout_unchanged(self, lemmatizer, word, lemma):
        """The override must NOT touch pronoun/noun forms."""
        t = lemmatizer.lookup_word(word)
        assert t.lemma == lemma

    @requires_dpd
    def test_noun_verb_homograph_keeps_noun(self, lemmatizer):
        """muni/sappi are first-class noun citations; must stay nouns, not aor verbs."""
        assert lemmatizer.lookup_word("muni").pos != "aor"
        assert lemmatizer.lookup_word("sappi").pos != "aor"


# =============================================================================
# -nti extension: 3pl finite verbs vs genuine quotatives
# =============================================================================

class TestNtiVerbs:
    @requires_dpd
    @pytest.mark.parametrize("word", [
        "santi", "bhavissanti", "gamissanti", "desessanti", "gaccheyyanti",
        "abhinandunti",
    ])
    def test_nti_finite_verb_not_split(self, lemmatizer, word):
        t = lemmatizer.lookup_word(word)
        assert t.sandhi is None, f"{word} wrongly split as {t.sandhi}"
        assert t.lemma is not None

    @requires_dpd
    def test_santi_is_the_verb(self, lemmatizer):
        t = lemmatizer.lookup_word("santi")
        assert t.lemma == "atthi"
        assert t.pos == "pr"

    @requires_dpd
    @pytest.mark.parametrize("word,host", [("evanti", "evaṃ"), ("cittanti", "cittaṃ")])
    def test_genuine_nti_quotative_kept(self, lemmatizer, word, host):
        """Non-verb -nti words (evaṃ/cittaṃ + iti) must stay split."""
        t = lemmatizer.lookup_word(word)
        assert t.sandhi == [host, "iti"]

    @requires_dpd
    def test_select_deconstruction_rejects_nti_verb(self, lemmatizer):
        assert lemmatizer._select_deconstruction(["saṃ + iti"], "santi") is None

    @requires_dpd
    def test_select_deconstruction_keeps_nti_nonverb(self, lemmatizer):
        assert lemmatizer._select_deconstruction(["evaṃ + iti"], "evanti") == ["evaṃ", "iti"]
