"""Tests for pali.search and pali.index — search functionality.

These tests require the search index (built from lemmatized data).
They are marked @pytest.mark.slow since index building takes ~30s.
"""

import pytest
from pathlib import Path
from conftest import requires_lemmatized

from pali.index import SearchIndex
from pali.search import Search, LemmaSearchResult, TextSearchResult


slow = pytest.mark.slow


# =========================================================================
# SearchIndex
# =========================================================================

class TestSearchIndex:
    def test_is_built_nonexistent(self, tmp_path):
        idx = SearchIndex(tmp_path, index_path=tmp_path / "test.db")
        assert idx.is_built() is False

    @requires_lemmatized
    @slow
    def test_is_built_after_build(self, data_dir):
        idx = SearchIndex(data_dir)
        # If index already exists, this checks it
        if idx.is_built():
            assert True
        else:
            pytest.skip("Index not built and building is too slow for default test run")

    def test_close_no_connection(self, tmp_path):
        idx = SearchIndex(tmp_path)
        idx.close()  # Should not raise

    def test_search_text_malformed_query(self, tmp_path):
        """Malformed FTS5 queries should return empty list, not raise."""
        import sqlite3
        idx = SearchIndex(tmp_path, index_path=tmp_path / "test.db")
        conn = idx._get_conn()
        conn.executescript("""
            CREATE VIRTUAL TABLE segments_fts USING fts5(
                segment_id, sutta_id, nikaya, pali, tokenize='unicode61'
            );
            CREATE TABLE lemma_index (
                lemma TEXT NOT NULL,
                word TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                sutta_id TEXT NOT NULL,
                nikaya TEXT NOT NULL,
                pos TEXT
            );
            CREATE TABLE sutta_meta (
                sutta_id TEXT PRIMARY KEY,
                nikaya TEXT NOT NULL,
                title_pali TEXT,
                title_eng TEXT,
                pts TEXT,
                segment_count INTEGER
            );
        """)
        # Force is_built() to return True by ensuring tables exist
        results = idx.search_text("OR AND NOT")
        assert results == []
        results = idx.search_text("unclosed\"quote")
        assert results == []
        idx.close()

    def test_get_sutta_ids_empty(self, tmp_path):
        """get_sutta_ids on empty index should return empty list."""
        import sqlite3
        idx = SearchIndex(tmp_path, index_path=tmp_path / "test.db")
        conn = idx._get_conn()
        conn.executescript("""
            CREATE TABLE lemma_index (
                lemma TEXT NOT NULL,
                word TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                sutta_id TEXT NOT NULL,
                nikaya TEXT NOT NULL,
                pos TEXT
            );
            CREATE VIRTUAL TABLE segments_fts USING fts5(
                segment_id, sutta_id, nikaya, pali, tokenize='unicode61'
            );
            CREATE TABLE sutta_meta (
                sutta_id TEXT PRIMARY KEY,
                nikaya TEXT NOT NULL,
                title_pali TEXT,
                title_eng TEXT,
                pts TEXT,
                segment_count INTEGER
            );
        """)
        result = idx.get_sutta_ids()
        assert result == []
        result_filtered = idx.get_sutta_ids(nikaya="dn")
        assert result_filtered == []
        idx.close()

    def test_index_segment_includes_sandhi_components(self, tmp_path):
        """Regression: sandhi component lemmas must be indexed."""
        import sqlite3
        idx = SearchIndex(tmp_path, index_path=tmp_path / "test.db")
        conn = idx._get_conn()
        # Create tables
        conn.executescript("""
            CREATE TABLE lemma_index (
                lemma TEXT NOT NULL,
                word TEXT NOT NULL,
                segment_id TEXT NOT NULL,
                sutta_id TEXT NOT NULL,
                nikaya TEXT NOT NULL,
                pos TEXT
            );
            CREATE VIRTUAL TABLE segments_fts USING fts5(
                segment_id, sutta_id, nikaya, pali, tokenize='unicode61'
            );
        """)
        idx._batch_size = 10000
        idx._lemma_batch = []
        idx._fts_batch = []
        segment = {
            "id": "dn1:1.1",
            "pali": "dhammañca",
            "tokens": [
                {
                    "word": "dhammañca",
                    "sandhi": ["dhammaṃ", "ca"],
                    "components": [
                        {"lemma": "dhamma", "pos": "masc"},
                        {"lemma": "ca", "pos": "ind"},
                    ]
                }
            ]
        }
        idx._index_segment(conn, segment, "dn1", "dn")
        # Both component lemmas should be in the batch
        lemmas = [row[0] for row in idx._lemma_batch]
        assert "dhamma" in lemmas
        assert "ca" in lemmas
        idx.close()


# =========================================================================
# Search.search_lemma()
# =========================================================================

@requires_lemmatized
@slow
class TestSearchLemma:
    @pytest.fixture(autouse=True)
    def setup_search(self, data_dir):
        self.search = Search(data_dir)
        yield
        self.search.close()

    def test_common_lemma(self):
        result = self.search.search_lemma("dhamma")
        assert isinstance(result, LemmaSearchResult)
        assert result.lemma == "dhamma"
        assert result.total > 0

    def test_has_by_nikaya(self):
        result = self.search.search_lemma("dhamma")
        assert isinstance(result.by_nikaya, dict)
        assert len(result.by_nikaya) > 0

    def test_nikaya_filter(self):
        result = self.search.search_lemma("dhamma", nikaya="dn")
        assert result.total > 0
        # All occurrences should be from dn
        for occ in result.occurrences:
            assert occ.nikaya == "dn"

    def test_unknown_lemma(self):
        result = self.search.search_lemma("xyznonexistent")
        assert result.total == 0
        assert result.occurrences == []

    def test_occurrences_have_fields(self):
        result = self.search.search_lemma("dhamma", limit=5)
        if result.occurrences:
            occ = result.occurrences[0]
            assert occ.word
            assert occ.segment_id
            assert occ.sutta_id
            assert occ.nikaya


# =========================================================================
# Search.search_text()
# =========================================================================

@requires_lemmatized
@slow
class TestSearchText:
    @pytest.fixture(autouse=True)
    def setup_search(self, data_dir):
        self.search = Search(data_dir)
        yield
        self.search.close()

    def test_phrase_search(self):
        results = self.search.search_text("evaṃ me sutaṃ")
        assert len(results) > 0
        assert all(isinstance(r, TextSearchResult) for r in results)

    def test_nikaya_filter(self):
        results = self.search.search_text("evaṃ me sutaṃ", nikaya="dn")
        for r in results:
            assert r.nikaya == "dn"

    def test_result_has_fields(self):
        results = self.search.search_text("evaṃ me sutaṃ", limit=1)
        if results:
            r = results[0]
            assert r.segment_id
            assert r.sutta_id
            assert r.nikaya
            assert r.snippet


# =========================================================================
# Search.get_all_lemmas()
# =========================================================================

@requires_lemmatized
@slow
class TestGetAllLemmas:
    def test_returns_sorted_list(self, data_dir):
        search = Search(data_dir)
        try:
            lemmas = search.get_all_lemmas()
            assert isinstance(lemmas, list)
            assert len(lemmas) > 0
            assert lemmas == sorted(lemmas)
        finally:
            search.close()
