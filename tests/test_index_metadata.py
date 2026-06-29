"""Tests for SearchIndex staleness detection, atomic build, metadata, and
narrowed error handling (CODE_REVIEW finding 3). Uses tiny synthetic fixtures."""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pali.index import SearchIndex, INDEX_SCHEMA_VERSION


def _make_corpus(data_dir: Path, pali="dhammā buddho", lemma="dhamma"):
    dn = data_dir / "lemmatized" / "dn"
    dn.mkdir(parents=True, exist_ok=True)
    (dn / "dn1.json").write_text(json.dumps({
        "id": "dn1",
        "title_pali": "Test",
        "segments": [{
            "id": "dn1:1.1",
            "pali": pali,
            "tokens": [{"word": "dhammā", "lemma": lemma, "pos": "masc"}],
        }],
    }), encoding="utf-8")


@pytest.fixture
def built_index(tmp_path):
    _make_corpus(tmp_path)
    idx = SearchIndex(tmp_path)
    idx.build()
    yield idx, tmp_path
    idx.close()


class TestIndexMetadata:
    def test_build_creates_meta(self, built_index):
        idx, _ = built_index
        meta = idx._read_meta(idx._get_conn())
        assert meta is not None
        assert meta["schema_version"] == str(INDEX_SCHEMA_VERSION)
        assert int(meta["token_count"]) >= 1
        assert "source_hash" in meta and "built_at" in meta

    def test_is_built_true_after_build(self, built_index):
        idx, _ = built_index
        assert idx.is_built() is True

    def test_no_leftover_temp_file(self, built_index):
        idx, data_dir = built_index
        assert not (data_dir / "index.db.building").exists()

    def test_search_works(self, built_index):
        idx, _ = built_index
        assert any(r for r in idx.search_lemma("dhamma"))
        assert idx.search_text("dhammā")  # FTS hit


class TestStaleness:
    def test_source_change_marks_stale(self, built_index):
        idx, data_dir = built_index
        assert idx.is_built() is True
        # change source content (size differs -> fingerprint differs)
        _make_corpus(data_dir, pali="aññaṃ word here longer", lemma="añña")
        assert idx.is_built() is False  # detected stale

    def test_rebuild_after_change(self, built_index):
        idx, data_dir = built_index
        _make_corpus(data_dir, pali="aññaṃ longer text", lemma="añña")
        idx.build()  # should rebuild because stale
        assert idx.is_built() is True
        assert any(r for r in idx.search_lemma("añña"))

    def test_schema_bump_marks_stale(self, built_index, monkeypatch):
        idx, _ = built_index
        monkeypatch.setattr("pali.index.INDEX_SCHEMA_VERSION", INDEX_SCHEMA_VERSION + 99)
        assert idx.is_built() is False

    def test_premeta_index_is_stale(self, tmp_path):
        """An index lacking index_meta (old format) must be treated as stale."""
        _make_corpus(tmp_path)
        idx = SearchIndex(tmp_path)
        idx.build()
        conn = idx._get_conn()
        conn.execute("DROP TABLE index_meta")
        conn.commit()
        assert idx.is_built() is False
        idx.close()


class TestErrorHandling:
    def test_malformed_query_returns_empty(self, built_index):
        idx, _ = built_index
        # unbalanced quote / FTS5 syntax error -> swallowed as no results
        assert idx.search_text('"unterminated') == []

    def test_db_error_surfaces(self, built_index):
        """A non-query OperationalError (missing table) must NOT be hidden."""
        idx, _ = built_index
        conn = idx._get_conn()
        conn.execute("DROP TABLE segments_fts")
        conn.commit()
        with pytest.raises(sqlite3.OperationalError):
            idx.search_text("dhammā")
