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
