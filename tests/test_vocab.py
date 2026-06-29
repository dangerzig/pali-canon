"""Tests for pali.vocab — Vocabulary statistics and R package exports."""

import pytest
from pathlib import Path
from collections import Counter
from conftest import requires_data, requires_lemmatized, slow, corpus

from pali.vocab import Vocabulary, VocabularyStats, ALL_COLLECTIONS

# Every test here needs the full lemmatized corpus.
pytestmark = corpus


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

@slow
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


# =========================================================================
# R package CSV export methods
# =========================================================================

@slow
@requires_lemmatized
class TestExportTipitakaRaw:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_creates_csv(self, tmp_path):
        output = tmp_path / "raw.csv"
        self.vocab.export_tipitaka_raw(str(output))
        assert output.exists()

    def test_csv_structure(self, tmp_path):
        import csv
        csv.field_size_limit(10 * 1024 * 1024)
        output = tmp_path / "raw.csv"
        self.vocab.export_tipitaka_raw(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(reader.fieldnames) == {"book", "book_name", "text"}
        assert len(rows) == 7  # one per collection
        books = [r["book"] for r in rows]
        assert "dn" in books
        assert "vinaya" in books
        assert "abhidhamma" in books

    def test_text_non_empty(self, tmp_path):
        import csv
        csv.field_size_limit(10 * 1024 * 1024)
        output = tmp_path / "raw.csv"
        self.vocab.export_tipitaka_raw(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert len(row["text"]) > 0, f"Empty text for {row['book']}"


@slow
@requires_lemmatized
class TestExportTipitakaSuttasRaw:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_csv_structure(self, tmp_path):
        import csv
        csv.field_size_limit(10 * 1024 * 1024)
        output = tmp_path / "suttas_raw.csv"
        self.vocab.export_tipitaka_suttas_raw(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(reader.fieldnames) == {"sutta", "nikaya", "text"}
        # Should have many rows (one per text unit)
        assert len(rows) > 100
        # DN should have 34 suttas
        dn_rows = [r for r in rows if r["nikaya"] == "dn"]
        assert len(dn_rows) == 34

    def test_dn1_present(self, tmp_path):
        import csv
        csv.field_size_limit(10 * 1024 * 1024)
        output = tmp_path / "suttas_raw.csv"
        self.vocab.export_tipitaka_suttas_raw(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        dn1 = [r for r in rows if r["sutta"] == "dn1"]
        assert len(dn1) == 1
        assert "Evaṃ" in dn1[0]["text"]


@slow
@requires_lemmatized
class TestExportTipitakaLong:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_csv_structure(self, tmp_path):
        import csv
        output = tmp_path / "long.csv"
        self.vocab.export_tipitaka_long(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(reader.fieldnames) == {"word", "n", "total", "freq", "book"}
        assert len(rows) > 0

    def test_has_all_collections(self, tmp_path):
        import csv
        output = tmp_path / "long.csv"
        self.vocab.export_tipitaka_long(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            books = set(r["book"] for r in reader)

        for coll in ALL_COLLECTIONS:
            assert coll in books, f"Missing collection: {coll}"

    def test_freq_valid(self, tmp_path):
        import csv
        output = tmp_path / "long.csv"
        self.vocab.export_tipitaka_long(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                freq = float(row["freq"])
                assert 0 <= freq <= 1.0, f"Invalid freq {freq} for {row['word']}"
                break  # just check first row for speed


@slow
@requires_lemmatized
class TestExportTipitakaWide:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_csv_structure(self, tmp_path):
        import csv
        output = tmp_path / "wide.csv"
        self.vocab.export_tipitaka_wide(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

        assert header[0] == "book"
        assert len(header) > 10  # many columns (words)
        assert len(rows) == 7  # one per collection


@slow
@requires_lemmatized
class TestExportTipitakaSuttasLong:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_csv_structure(self, tmp_path):
        import csv
        output = tmp_path / "suttas_long.csv"
        self.vocab.export_tipitaka_suttas_long(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(reader.fieldnames) == {"word", "n", "total", "freq", "sutta", "nikaya"}
        assert len(rows) > 0

    def test_has_multiple_nikayas(self, tmp_path):
        import csv
        output = tmp_path / "suttas_long.csv"
        self.vocab.export_tipitaka_suttas_long(str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            nikayas = set(r["nikaya"] for r in reader)

        assert len(nikayas) == 7


@requires_lemmatized
class TestExportVocabulary:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_creates_csv(self, tmp_path):
        output = tmp_path / "vocab.csv"
        self.vocab.export_vocabulary("dn", str(output))
        assert output.exists()

    def test_csv_structure(self, tmp_path):
        import csv
        output = tmp_path / "vocab.csv"
        self.vocab.export_vocabulary("dn", str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(reader.fieldnames) == {"lemma", "count"}
        assert len(rows) > 100  # DN has many unique lemmas

    def test_sorted_by_count_descending(self, tmp_path):
        import csv
        output = tmp_path / "vocab.csv"
        self.vocab.export_vocabulary("dn", str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            counts = [int(r["count"]) for r in reader]

        # Should be sorted descending
        assert counts == sorted(counts, reverse=True)


try:
    import pandas
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import numpy as np
    from scipy import sparse
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

requires_pandas = pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed")
requires_scipy = pytest.mark.skipif(not HAS_SCIPY, reason="scipy not installed")


@requires_lemmatized
@requires_pandas
class TestExportDtm:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_creates_csv(self, tmp_path):
        output = tmp_path / "dtm.csv"
        self.vocab.export_dtm("dn", str(output))
        assert output.exists()

    def test_csv_has_sutta_rows(self, tmp_path):
        import csv
        output = tmp_path / "dtm.csv"
        self.vocab.export_dtm("dn", str(output))

        with open(output, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

        assert len(rows) == 34  # 34 DN suttas


# =========================================================================
# document_term_matrix() — sparse matrix path
# =========================================================================

@requires_lemmatized
@requires_scipy
class TestDocumentTermMatrixSparse:
    def setup_method(self):
        from conftest import DATA_DIR
        self.vocab = Vocabulary(DATA_DIR)

    def test_returns_sparse_tuple(self):
        result = self.vocab.document_term_matrix("dn", min_df=10)
        assert isinstance(result, tuple)
        matrix, doc_list, term_list = result
        assert sparse.issparse(matrix)
        assert matrix.shape[0] == len(doc_list)
        assert matrix.shape[1] == len(term_list)

    def test_dn_has_34_docs(self):
        matrix, doc_list, term_list = self.vocab.document_term_matrix("dn", min_df=10)
        assert len(doc_list) == 34

    def test_values_nonnegative(self):
        matrix, _, _ = self.vocab.document_term_matrix("dn", min_df=10)
        assert matrix.min() >= 0

    def test_min_df_filters_terms(self):
        _, _, terms_low = self.vocab.document_term_matrix("dn", min_df=1)
        _, _, terms_high = self.vocab.document_term_matrix("dn", min_df=10)
        assert len(terms_high) <= len(terms_low)
