#!/usr/bin/env python3
"""
Digital Pali Dictionary lookup module.
Provides easy word lookups against the DPD SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data/dpd/dpd.db"


@dataclass
class DPDEntry:
    """A dictionary entry from DPD."""
    id: int
    lemma: str
    pos: str  # part of speech
    meaning: str
    meaning_lit: str
    grammar: str
    root: str
    root_sign: str
    root_base: str
    construction: str
    sanskrit: str
    example: str
    inflections: list[str]

    def __str__(self):
        parts = [f"{self.lemma} ({self.pos})"]
        if self.meaning:
            parts.append(f"  {self.meaning}")
        if self.meaning_lit:
            parts.append(f"  lit. {self.meaning_lit}")
        if self.root:
            parts.append(f"  √{self.root}")
        return "\n".join(parts)


@dataclass
class LookupResult:
    """Result of looking up a word form."""
    query: str
    entries: list[DPDEntry]
    deconstructor: list[str]  # compound breakdowns

    @property
    def found(self) -> bool:
        return len(self.entries) > 0 or len(self.deconstructor) > 0

    def __str__(self):
        if not self.found:
            return f"'{self.query}': not found"

        parts = [f"'{self.query}':"]

        if self.deconstructor:
            parts.append(f"  Compounds: {', '.join(self.deconstructor)}")

        for entry in self.entries:
            parts.append(f"  • {entry.lemma} ({entry.pos}): {entry.meaning}")
            if entry.root:
                parts.append(f"    √{entry.root}")

        return "\n".join(parts)


class DPD:
    """Digital Pali Dictionary interface."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _get_entry(self, headword_id: int) -> Optional[DPDEntry]:
        """Get a dictionary entry by ID."""
        cursor = self.conn.execute("""
            SELECT id, lemma_1, pos, meaning_1, meaning_lit, grammar,
                   root_key, root_sign, root_base, construction, sanskrit,
                   example_1, inflections
            FROM dpd_headwords WHERE id = ?
        """, (headword_id,))

        row = cursor.fetchone()
        if not row:
            return None

        inflections = []
        if row['inflections']:
            inflections = [i.strip() for i in row['inflections'].split(',')]

        return DPDEntry(
            id=row['id'],
            lemma=row['lemma_1'] or "",
            pos=row['pos'] or "",
            meaning=row['meaning_1'] or "",
            meaning_lit=row['meaning_lit'] or "",
            grammar=row['grammar'] or "",
            root=row['root_key'] or "",
            root_sign=row['root_sign'] or "",
            root_base=row['root_base'] or "",
            construction=row['construction'] or "",
            sanskrit=row['sanskrit'] or "",
            example=row['example_1'] or "",
            inflections=inflections,
        )

    def lookup(self, word: str) -> LookupResult:
        """
        Look up a Pāli word form.
        Returns dictionary entries and compound analysis if available.
        """
        word = word.lower().strip()

        cursor = self.conn.execute("""
            SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
        """, (word,))

        row = cursor.fetchone()

        entries = []
        deconstructor = []

        if row:
            # Parse headword IDs
            if row['headwords']:
                try:
                    headword_ids = json.loads(row['headwords'])
                    for hid in headword_ids:
                        entry = self._get_entry(hid)
                        if entry:
                            entries.append(entry)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Parse deconstructor
            if row['deconstructor']:
                try:
                    deconstructor = json.loads(row['deconstructor'])
                except (json.JSONDecodeError, TypeError):
                    pass

        return LookupResult(query=word, entries=entries, deconstructor=deconstructor)

    def lookup_many(self, words: list[str]) -> dict[str, LookupResult]:
        """Look up multiple words efficiently."""
        results = {}
        for word in words:
            results[word] = self.lookup(word)
        return results

    def get_lemma(self, word: str) -> Optional[str]:
        """Get the lemma (dictionary form) for a word."""
        result = self.lookup(word)
        if result.entries:
            return result.entries[0].lemma
        return None

    def get_meaning(self, word: str) -> Optional[str]:
        """Get the primary meaning for a word."""
        result = self.lookup(word)
        if result.entries:
            return result.entries[0].meaning
        return None

    def search_headwords(self, pattern: str, limit: int = 20) -> list[DPDEntry]:
        """Search headwords by pattern (SQL LIKE)."""
        cursor = self.conn.execute("""
            SELECT id FROM dpd_headwords
            WHERE lemma_1 LIKE ?
            ORDER BY lemma_1
            LIMIT ?
        """, (pattern, limit))

        entries = []
        for row in cursor:
            entry = self._get_entry(row['id'])
            if entry:
                entries.append(entry)
        return entries

    def get_root(self, root_key: str) -> Optional[dict]:
        """Get information about a Pāli root."""
        cursor = self.conn.execute("""
            SELECT * FROM dpd_roots WHERE root = ?
        """, (root_key,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def tokenize_text(self, text: str) -> list[str]:
        """
        Simple tokenization of Pāli text.
        Splits on whitespace and punctuation, normalizes.
        """
        import re
        # Normalize niggahīta
        text = text.replace('ṁ', 'ṃ')
        # Split on non-letter characters
        tokens = re.split(r'[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+', text.lower())
        return [t for t in tokens if t]

    def analyze_text(self, text: str) -> list[LookupResult]:
        """
        Analyze a Pāli text by looking up each word.
        Returns list of lookup results for each token.
        """
        tokens = self.tokenize_text(text)
        return [self.lookup(token) for token in tokens]

    def stats(self) -> dict:
        """Get database statistics."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM dpd_headwords")
        headwords = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM lookup")
        lookups = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM dpd_roots")
        roots = cursor.fetchone()[0]

        return {
            "headwords": headwords,
            "lookup_entries": lookups,
            "roots": roots,
        }


# Convenience function for quick lookups
def lookup(word: str) -> LookupResult:
    """Quick lookup of a single word."""
    with DPD() as dpd:
        return dpd.lookup(word)


def analyze(text: str) -> list[LookupResult]:
    """Quick analysis of a text."""
    with DPD() as dpd:
        return dpd.analyze_text(text)


if __name__ == "__main__":
    # Demo usage
    with DPD() as dpd:
        print("=== DPD Stats ===")
        stats = dpd.stats()
        print(f"Headwords: {stats['headwords']:,}")
        print(f"Lookup entries: {stats['lookup_entries']:,}")
        print(f"Roots: {stats['roots']:,}")

        print("\n=== Sample Lookups ===")

        test_words = ["dhamma", "bhikkhu", "bhikkhave", "nibbāna", "saṃsāra", "evaṃ"]
        for word in test_words:
            result = dpd.lookup(word)
            print(f"\n{result}")

        print("\n=== Text Analysis ===")
        sample = "Evaṃ me sutaṃ"
        print(f"Text: '{sample}'")
        for result in dpd.analyze_text(sample):
            if result.found:
                meanings = [e.meaning for e in result.entries[:2]]
                print(f"  {result.query}: {'; '.join(meanings)}")
