"""SQLite index for fast lemma and text search."""

import hashlib
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional
import json

from .text import FLAT_COLLECTIONS, NESTED_COLLECTIONS, ITEMS_COLLECTIONS

# Bump when the index schema changes so old indexes are rebuilt automatically.
INDEX_SCHEMA_VERSION = 2


class SearchIndex:
    """SQLite-based search index for lemma and text lookups."""

    def __init__(self, data_dir: Path, index_path: Optional[Path] = None):
        """Initialize search index.

        Args:
            data_dir: Path to data directory containing lemmatized/
            index_path: Path for SQLite index file. Defaults to data_dir/index.db
        """
        self.data_dir = data_dir
        self.index_path = index_path or (data_dir / "index.db")
        self._conn: Optional[sqlite3.Connection] = None
        # Transient build state
        self._fts_batch: list = []
        self._lemma_batch: list = []
        self._batch_size: int = 1000

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.index_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _source_fingerprint(self) -> tuple[int, str]:
        """Cheap fingerprint of the lemmatized source: (file_count, sha256).

        Hashes each lemmatized JSON file's relative path and byte size (size
        changes whenever content changes; unlike mtime it is stable across git
        checkouts and clones). Used to detect a stale index.
        """
        lemmatized_dir = self.data_dir / "lemmatized"
        entries = []
        if lemmatized_dir.is_dir():
            for f in sorted(lemmatized_dir.rglob("*.json")):
                if f.name.startswith("_"):
                    continue
                rel = f.relative_to(lemmatized_dir).as_posix()
                entries.append(f"{rel}:{f.stat().st_size}")
        h = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
        return len(entries), h

    def _read_meta(self, conn: sqlite3.Connection) -> Optional[dict]:
        """Return the index_meta row as a dict, or None if absent/empty."""
        try:
            cur = conn.execute("SELECT key, value FROM index_meta")
        except sqlite3.OperationalError:
            return None
        meta = {k: v for k, v in cur.fetchall()}
        return meta or None

    def is_built(self) -> bool:
        """Check if a current (non-stale) index exists.

        Returns False if the index is missing, lacks the core tables, was built
        under a different schema version, or no longer matches the source-data
        fingerprint — any of which forces build() to rebuild.
        """
        if not self.index_path.exists():
            return False
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='lemma_index'"
        )
        if cursor.fetchone() is None:
            return False
        meta = self._read_meta(conn)
        if not meta:
            return False  # pre-metadata index -> treat as stale
        if meta.get("schema_version") != str(INDEX_SCHEMA_VERSION):
            return False
        count, source_hash = self._source_fingerprint()
        return (meta.get("source_file_count") == str(count)
                and meta.get("source_hash") == source_hash)

    def build(self, force: bool = False) -> None:
        """Build the search index from lemmatized data.

        Built atomically: the index is written to a temporary file and then
        renamed over index_path, so a failed or interrupted build never leaves a
        half-written index in place. An index_meta row records the schema
        version, source fingerprint, counts, and build time for staleness checks.

        Args:
            force: If True, rebuild even if a current index exists.
        """
        if self.is_built() and not force:
            return

        # Build into a temp DB, then atomically replace the real one.
        tmp_path = self.index_path.with_name(self.index_path.name + ".building")
        if tmp_path.exists():
            tmp_path.unlink()

        self._fts_batch.clear()
        self._lemma_batch.clear()
        count, source_hash = self._source_fingerprint()

        conn = sqlite3.connect(str(tmp_path))
        try:
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
                    segment_id,
                    sutta_id,
                    nikaya,
                    pali,
                    tokenize='unicode61'
                );
                CREATE TABLE sutta_meta (
                    sutta_id TEXT PRIMARY KEY,
                    nikaya TEXT NOT NULL,
                    title_pali TEXT,
                    title_eng TEXT,
                    pts TEXT,
                    segment_count INTEGER
                );
                CREATE TABLE index_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            lemmatized_dir = self.data_dir / "lemmatized"
            if lemmatized_dir.is_dir():
                for nikaya_dir in sorted(lemmatized_dir.iterdir()):
                    if not nikaya_dir.is_dir():
                        continue
                    self._index_nikaya(conn, nikaya_dir, nikaya_dir.name)

            self._flush_batches(conn)

            conn.executescript("""
                CREATE INDEX idx_lemma ON lemma_index(lemma);
                CREATE INDEX idx_lemma_nikaya ON lemma_index(lemma, nikaya);
                CREATE INDEX idx_segment ON lemma_index(segment_id);
                CREATE INDEX idx_sutta ON lemma_index(sutta_id);
            """)

            token_count = conn.execute("SELECT COUNT(*) FROM lemma_index").fetchone()[0]
            meta = {
                "schema_version": str(INDEX_SCHEMA_VERSION),
                "source_file_count": str(count),
                "source_hash": source_hash,
                "token_count": str(token_count),
                "built_at": str(int(time.time())),
            }
            conn.executemany(
                "INSERT INTO index_meta (key, value) VALUES (?, ?)",
                list(meta.items()),
            )
            conn.commit()
        except Exception:
            conn.close()
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        finally:
            self._fts_batch.clear()
            self._lemma_batch.clear()

        conn.close()
        # Drop the live connection before swapping the file underneath it.
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        os.replace(tmp_path, self.index_path)

    def _flush_batches(self, conn: sqlite3.Connection) -> None:
        """Flush batched inserts to the database."""
        if self._fts_batch:
            conn.executemany(
                "INSERT INTO segments_fts (segment_id, sutta_id, nikaya, pali) VALUES (?, ?, ?, ?)",
                self._fts_batch
            )
            self._fts_batch = []

        if self._lemma_batch:
            conn.executemany(
                """INSERT INTO lemma_index (lemma, word, segment_id, sutta_id, nikaya, pos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                self._lemma_batch
            )
            self._lemma_batch = []

    def _index_nikaya(self, conn: sqlite3.Connection, nikaya_dir: Path, nikaya: str) -> None:
        """Index all files in a nikaya directory."""
        for json_file in sorted(nikaya_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different structures
            if nikaya in FLAT_COLLECTIONS:  # dn, mn, vinaya, abhidhamma
                self._index_sutta(conn, data, nikaya)
            elif nikaya in NESTED_COLLECTIONS:  # sn, an
                for sutta_data in data.get("suttas", []):
                    self._index_nested_sutta(conn, sutta_data, data, nikaya)
            elif nikaya in ITEMS_COLLECTIONS:  # kn
                if "items" in data:
                    for item in data["items"]:
                        self._index_kn_item(conn, item, data, nikaya)
                else:
                    self._index_sutta(conn, data, nikaya)

    def _index_sutta(self, conn: sqlite3.Connection, data: dict, nikaya: str) -> None:
        """Index a single sutta (DN/MN structure)."""
        sutta_id = data["id"]

        # Insert sutta metadata
        conn.execute(
            """INSERT INTO sutta_meta (sutta_id, nikaya, title_pali, title_eng, pts, segment_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sutta_id, nikaya, data.get("title_pali"), data.get("title_eng"),
             data.get("pts"), len(data.get("segments", [])))
        )

        # Index segments
        for segment in data.get("segments", []):
            self._index_segment(conn, segment, sutta_id, nikaya)

    def _index_nested_sutta(self, conn: sqlite3.Connection, sutta_data: dict,
                           parent_data: dict, nikaya: str) -> None:
        """Index a nested sutta (SN/AN structure)."""
        sutta_id = sutta_data["id"]

        conn.execute(
            """INSERT INTO sutta_meta (sutta_id, nikaya, title_pali, title_eng, pts, segment_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sutta_id, nikaya, parent_data.get("name_pali"), None,
             parent_data.get("pts"), len(sutta_data.get("segments", [])))
        )

        for segment in sutta_data.get("segments", []):
            self._index_segment(conn, segment, sutta_id, nikaya)

    def _index_kn_item(self, conn: sqlite3.Connection, item: dict,
                      parent_data: dict, nikaya: str) -> None:
        """Index a KN item."""
        sutta_id = item["id"]

        conn.execute(
            """INSERT INTO sutta_meta (sutta_id, nikaya, title_pali, title_eng, pts, segment_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sutta_id, nikaya, parent_data.get("name_pali"), parent_data.get("name_eng"),
             None, len(item.get("segments", [])))
        )

        for segment in item.get("segments", []):
            self._index_segment(conn, segment, sutta_id, nikaya)

    def _index_segment(self, conn: sqlite3.Connection, segment: dict,
                      sutta_id: str, nikaya: str) -> None:
        """Index a single segment using batched inserts."""
        segment_id = segment["id"]
        pali = segment.get("pali", "")

        # Add to FTS batch
        self._fts_batch.append((segment_id, sutta_id, nikaya, pali))

        # Add to lemma batch
        for token in segment.get("tokens", []):
            lemma = token.get("lemma")
            if lemma:
                self._lemma_batch.append(
                    (lemma, token["word"], segment_id, sutta_id, nikaya, token.get("pos"))
                )
            # Also index component lemmas from sandhi tokens
            for comp in token.get("components") or []:
                comp_lemma = comp.get("lemma")
                if comp_lemma:
                    self._lemma_batch.append(
                        (comp_lemma, token["word"], segment_id, sutta_id, nikaya, comp.get("pos"))
                    )

        # Flush batches when they reach the threshold
        if len(self._fts_batch) >= self._batch_size:
            self._flush_batches(conn)

    def search_lemma(self, lemma: str, nikaya: Optional[str] = None,
                    limit: int = 1000) -> list[dict]:
        """Search for occurrences of a lemma.

        Args:
            lemma: The lemma to search for
            nikaya: Optional filter by nikaya
            limit: Maximum results to return

        Returns:
            List of occurrence dicts with segment_id, sutta_id, word, etc.
        """
        if not self.is_built():
            self.build()

        conn = self._get_conn()

        if nikaya:
            cursor = conn.execute(
                """SELECT lemma, word, segment_id, sutta_id, nikaya, pos
                   FROM lemma_index WHERE lemma = ? AND nikaya = ? LIMIT ?""",
                (lemma, nikaya, limit)
            )
        else:
            cursor = conn.execute(
                """SELECT lemma, word, segment_id, sutta_id, nikaya, pos
                   FROM lemma_index WHERE lemma = ? LIMIT ?""",
                (lemma, limit)
            )

        return [dict(row) for row in cursor.fetchall()]

    def count_lemma(self, lemma: str, nikaya: Optional[str] = None) -> int:
        """Count occurrences of a lemma."""
        if not self.is_built():
            self.build()

        conn = self._get_conn()

        if nikaya:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM lemma_index WHERE lemma = ? AND nikaya = ?",
                (lemma, nikaya)
            )
        else:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM lemma_index WHERE lemma = ?",
                (lemma,)
            )

        return cursor.fetchone()[0]

    def count_lemma_by_nikaya(self, lemma: str) -> dict[str, int]:
        """Count lemma occurrences grouped by nikaya."""
        if not self.is_built():
            self.build()

        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT nikaya, COUNT(*) as count FROM lemma_index
               WHERE lemma = ? GROUP BY nikaya""",
            (lemma,)
        )

        return {row["nikaya"]: row["count"] for row in cursor.fetchall()}

    def search_text(self, query: str, nikaya: Optional[str] = None,
                   limit: int = 100) -> list[dict]:
        """Full-text search on segment text.

        Args:
            query: Search query (supports FTS5 syntax)
            nikaya: Optional filter by nikaya
            limit: Maximum results to return

        Returns:
            List of matching segments with id, sutta_id, text snippet
        """
        if not self.is_built():
            self.build()

        conn = self._get_conn()

        try:
            if nikaya:
                cursor = conn.execute(
                    """SELECT segment_id, sutta_id, nikaya,
                              snippet(segments_fts, 3, '«', '»', '...', 30) as snippet
                       FROM segments_fts
                       WHERE segments_fts MATCH ? AND nikaya = ?
                       LIMIT ?""",
                    (query, nikaya, limit)
                )
            else:
                cursor = conn.execute(
                    """SELECT segment_id, sutta_id, nikaya,
                              snippet(segments_fts, 3, '«', '»', '...', 30) as snippet
                       FROM segments_fts
                       WHERE segments_fts MATCH ?
                       LIMIT ?""",
                    (query, limit)
                )

            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            # Surface index/DB corruption (missing table, unreadable file, lock)
            # instead of hiding it as "no results"; swallow only malformed user
            # FTS5 queries (unterminated string, syntax error, bad MATCH, etc.).
            msg = str(e).lower()
            index_errors = ("no such table", "no such module", "no such index",
                            "disk image is malformed", "not a database",
                            "database is locked", "file is encrypted")
            if any(s in msg for s in index_errors):
                raise
            return []

    def get_sutta_ids(self, nikaya: Optional[str] = None) -> list[str]:
        """Get all sutta IDs, optionally filtered by nikaya."""
        if not self.is_built():
            self.build()

        conn = self._get_conn()

        if nikaya:
            cursor = conn.execute(
                "SELECT sutta_id FROM sutta_meta WHERE nikaya = ? ORDER BY sutta_id",
                (nikaya,)
            )
        else:
            cursor = conn.execute(
                "SELECT sutta_id FROM sutta_meta ORDER BY sutta_id"
            )

        return [row[0] for row in cursor.fetchall()]

    def get_all_lemmas(self) -> list[str]:
        """Get all unique lemmas in the corpus."""
        if not self.is_built():
            self.build()

        conn = self._get_conn()
        cursor = conn.execute("SELECT DISTINCT lemma FROM lemma_index ORDER BY lemma")
        return [row[0] for row in cursor.fetchall()]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
