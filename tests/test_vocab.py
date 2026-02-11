"""Tests for pali.vocab — Vocabulary statistics and R package exports."""

import pytest
from pathlib import Path
from collections import Counter
from conftest import requires_data, requires_lemmatized

from pali.vocab import Vocabulary, VocabularyStats, ALL_COLLECTIONS


# =========================================================================
# Vocabulary basics
# =========================================================================

@requires_lemmatized
class TestVocabularyInit:
    def test_init(self, data_dir):
        v = Vocabulary(data_dir)
        assert v.data_dir == data_dir
        assert v.lemmatized_dir == data_dir / "lemmatized"


# =========================================================================
# get_vocabulary()
# =========================================================================

@requires_lemmatized
class TestGetVocabulary:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_sutta_stats(self):
        stats = self.vocab.get_vocabulary(sutta_id="dn1", top_n=10)
        assert isinstance(stats, VocabularyStats)
        assert stats.sutta_id == "dn1"
        assert stats.unique_lemmas > 0
        assert stats.total_tokens > 0
        assert 0 < stats.coverage <= 1.0
        assert len(stats.top_lemmas) == 10

    def test_nikaya_stats(self):
        stats = self.vocab.get_vocabulary(nikaya="dn", top_n=5)
        assert stats.nikaya == "dn"
        assert stats.total_tokens > 0

    def test_invalid_sutta(self):
        stats = self.vocab.get_vocabulary(sutta_id="xyz999")
        assert stats.total_tokens == 0

    def test_vinaya_stats(self):
        stats = self.vocab.get_vocabulary(nikaya="vinaya", top_n=5)
        assert stats.total_tokens > 0

    def test_abhidhamma_stats(self):
        stats = self.vocab.get_vocabulary(nikaya="abhidhamma", top_n=5)
        assert stats.total_tokens > 0


# =========================================================================
# _count_segments() — sandhi token handling
# =========================================================================

class TestCountSegments:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_sandhi_tokens_counted(self):
        """Sandhi tokens should have their component lemmas counted."""
        segments = [{
            "tokens": [
                {"word": "suppiyopi", "sandhi": ["suppiyo", "api"],
                 "components": [
                     {"lemma": "suppiya", "pos": "masc"},
                     {"lemma": "api", "pos": "ind"},
                 ]},
                {"word": "dhamma", "lemma": "dhamma", "pos": "masc"},
            ]
        }]
        lemma_counts = Counter()
        pos_counts = Counter()
        token_stats = {"total": 0, "with_lemma": 0}

        self.vocab._count_segments(segments, lemma_counts, pos_counts, token_stats)

        assert token_stats["total"] == 2
        assert token_stats["with_lemma"] == 2
        assert lemma_counts["suppiya"] == 1
        assert lemma_counts["api"] == 1
        assert lemma_counts["dhamma"] == 1

    def test_regular_token_counted(self):
        """Regular tokens with lemma should be counted."""
        segments = [{"tokens": [
            {"word": "evaṃ", "lemma": "evaṃ", "pos": "ind"},
        ]}]
        lemma_counts = Counter()
        pos_counts = Counter()
        token_stats = {"total": 0, "with_lemma": 0}

        self.vocab._count_segments(segments, lemma_counts, pos_counts, token_stats)

        assert token_stats["total"] == 1
        assert lemma_counts["evaṃ"] == 1
        assert pos_counts["ind"] == 1

    def test_unknown_token_not_counted(self):
        """Tokens with no lemma and no components should not be counted as resolved."""
        segments = [{"tokens": [
            {"word": "xyzabc"},
        ]}]
        lemma_counts = Counter()
        pos_counts = Counter()
        token_stats = {"total": 0, "with_lemma": 0}

        self.vocab._count_segments(segments, lemma_counts, pos_counts, token_stats)

        assert token_stats["total"] == 1
        assert token_stats["with_lemma"] == 0
        assert len(lemma_counts) == 0


# =========================================================================
# _collect_tipitaka_counts() — sandhi handling in R exports
# =========================================================================

@requires_lemmatized
class TestCollectTipitakaCounts:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)
        self.data_dir = DATA_DIR

    def test_lemma_counts_match_count_segments(self):
        """_collect_tipitaka_counts with lemmas should match _count_segments."""
        import json

        json_file = self.data_dir / "lemmatized" / "dn" / "dn1.json"
        with open(json_file) as f:
            data = json.load(f)

        # Method 1: _count_segments
        lemma_counts1 = Counter()
        pos_counts1 = Counter()
        token_stats1 = {"total": 0, "with_lemma": 0}
        self.vocab._count_segments(data["segments"], lemma_counts1, pos_counts1, token_stats1)

        # Method 2: _collect_tipitaka_counts
        word_counts = Counter()
        self.vocab._collect_tipitaka_counts(
            json_file, "dn", True, {"_": word_counts}, by_sutta=False
        )

        total1 = sum(lemma_counts1.values())
        total2 = sum(word_counts.values())
        assert total1 == total2, f"Counts differ: _count_segments={total1}, _collect_tipitaka={total2}"

    def test_surface_form_counts(self):
        """Surface form counting should count words, not lemmas."""
        word_counts = Counter()
        json_file = self.data_dir / "lemmatized" / "dn" / "dn1.json"
        self.vocab._collect_tipitaka_counts(
            json_file, "dn", False, {"_": word_counts}, by_sutta=False
        )
        assert sum(word_counts.values()) > 0

    def test_by_sutta_mode(self):
        """by_sutta=True should create per-sutta counters."""
        doc_counts = {}
        json_file = self.data_dir / "lemmatized" / "sn" / "sn1.json"
        self.vocab._collect_tipitaka_counts(
            json_file, "sn", True, doc_counts, by_sutta=True
        )
        # SN1 has multiple suttas
        assert len(doc_counts) > 1
        assert "sn1.1" in doc_counts


# =========================================================================
# _count_doc_terms() — sandhi handling in DTM
# =========================================================================

class TestCountDocTerms:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_sandhi_lemmas_in_dtm(self):
        """Sandhi component lemmas should appear in document-term counts."""
        segments = [{
            "tokens": [
                {"word": "suppiyopi", "sandhi": ["suppiyo", "api"],
                 "components": [
                     {"lemma": "suppiya", "pos": "masc"},
                     {"lemma": "api", "pos": "ind"},
                 ]},
            ]
        }]
        doc_term_counts = {}
        term_doc_counts = Counter()
        self.vocab._count_doc_terms(
            segments, "test_doc", "lemmas", doc_term_counts, term_doc_counts
        )

        assert "suppiya" in doc_term_counts["test_doc"]
        assert "api" in doc_term_counts["test_doc"]
        assert "suppiya" in term_doc_counts
        assert "api" in term_doc_counts

    def test_word_mode_ignores_sandhi(self):
        """In word mode, sandhi tokens use surface form."""
        segments = [{
            "tokens": [
                {"word": "suppiyopi", "sandhi": ["suppiyo", "api"],
                 "components": [
                     {"lemma": "suppiya", "pos": "masc"},
                     {"lemma": "api", "pos": "ind"},
                 ]},
            ]
        }]
        doc_term_counts = {}
        term_doc_counts = Counter()
        self.vocab._count_doc_terms(
            segments, "test_doc", "words", doc_term_counts, term_doc_counts
        )

        assert "suppiyopi" in doc_term_counts["test_doc"]
        assert "suppiya" not in doc_term_counts["test_doc"]


# =========================================================================
# ALL_COLLECTIONS constant
# =========================================================================

class TestAllCollections:
    def test_includes_all_pitakas(self):
        assert "dn" in ALL_COLLECTIONS
        assert "vinaya" in ALL_COLLECTIONS
        assert "abhidhamma" in ALL_COLLECTIONS
        assert len(ALL_COLLECTIONS) == 7

    def test_order(self):
        assert ALL_COLLECTIONS == ["dn", "mn", "sn", "an", "kn", "vinaya", "abhidhamma"]


# =========================================================================
# Export methods (smoke tests)
# =========================================================================

@requires_lemmatized
class TestExports:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_export_tipitaka_texts_structure(self, tmp_path):
        """export_tipitaka_texts should produce a CSV with correct columns."""
        import csv
        csv.field_size_limit(10 * 1024 * 1024)  # 10MB — texts can be very large
        output = tmp_path / "texts.csv"
        self.vocab.export_tipitaka_texts(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0
        assert set(reader.fieldnames) == {"id", "collection", "pitaka", "title", "text", "text_lemmatized"}

        # Should have all three pitakas
        pitakas = set(r["pitaka"] for r in rows)
        assert "sutta" in pitakas
        assert "vinaya" in pitakas
        assert "abhidhamma" in pitakas

        # Spot-check: dn1 should be present
        dn1 = [r for r in rows if r["id"] == "dn1"]
        assert len(dn1) == 1
        assert dn1[0]["collection"] == "dn"
        assert len(dn1[0]["text"]) > 0
        assert len(dn1[0]["text_lemmatized"]) > 0
