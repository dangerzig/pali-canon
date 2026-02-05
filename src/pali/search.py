"""Search functionality for the Pāli Canon."""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from .index import SearchIndex


@dataclass
class LemmaOccurrence:
    """A single occurrence of a lemma."""
    lemma: str
    word: str
    segment_id: str
    sutta_id: str
    nikaya: str
    pos: Optional[str] = None


@dataclass
class LemmaSearchResult:
    """Results from a lemma search."""
    lemma: str
    total: int
    by_nikaya: dict[str, int]
    occurrences: list[LemmaOccurrence] = field(default_factory=list)


@dataclass
class TextSearchResult:
    """A single text search result."""
    segment_id: str
    sutta_id: str
    nikaya: str
    snippet: str


class Search:
    """Search interface for the Pāli Canon."""

    def __init__(self, data_dir: Path):
        """Initialize search with data directory.

        Args:
            data_dir: Path to data directory
        """
        self._index = SearchIndex(data_dir)

    def ensure_index(self) -> None:
        """Ensure search index is built."""
        if not self._index.is_built():
            print("Building search index (this may take a few minutes)...")
            self._index.build()
            print("Index built.")

    def search_lemma(
        self,
        lemma: str,
        nikaya: Optional[str] = None,
        limit: int = 1000,
    ) -> LemmaSearchResult:
        """Search for all occurrences of a lemma.

        Args:
            lemma: The lemma (dictionary form) to search for
            nikaya: Optional filter by nikaya (dn, mn, sn, an, kn)
            limit: Maximum occurrences to return (default 1000)

        Returns:
            LemmaSearchResult with total count, breakdown by nikaya, and occurrences

        Example:
            results = canon.search_lemma("dhamma")
            print(f"Found {results.total} occurrences")
            print(f"By nikaya: {results.by_nikaya}")
            for occ in results.occurrences[:10]:
                print(f"  {occ.segment_id}: {occ.word}")
        """
        self.ensure_index()

        # Get counts
        if nikaya:
            total = self._index.count_lemma(lemma, nikaya)
            by_nikaya = {nikaya: total}
        else:
            by_nikaya = self._index.count_lemma_by_nikaya(lemma)
            total = sum(by_nikaya.values())

        # Get occurrences
        raw_results = self._index.search_lemma(lemma, nikaya, limit)
        occurrences = [
            LemmaOccurrence(
                lemma=r["lemma"],
                word=r["word"],
                segment_id=r["segment_id"],
                sutta_id=r["sutta_id"],
                nikaya=r["nikaya"],
                pos=r["pos"],
            )
            for r in raw_results
        ]

        return LemmaSearchResult(
            lemma=lemma,
            total=total,
            by_nikaya=by_nikaya,
            occurrences=occurrences,
        )

    def search_text(
        self,
        query: str,
        nikaya: Optional[str] = None,
        limit: int = 100,
    ) -> list[TextSearchResult]:
        """Full-text search on segment text.

        Uses SQLite FTS5 for fast text search. Supports basic query syntax:
        - Simple terms: "buddha" finds segments containing "buddha"
        - Phrases: '"evaṃ me sutaṃ"' finds exact phrase
        - AND/OR: "buddha OR dhamma"
        - Prefix: "bodhi*" finds bodhisatta, bodhisattva, etc.

        Args:
            query: Search query
            nikaya: Optional filter by nikaya
            limit: Maximum results (default 100)

        Returns:
            List of TextSearchResult with segment_id, sutta_id, and text snippet

        Example:
            results = canon.search_text("evaṃ me sutaṃ")
            for r in results[:10]:
                print(f"{r.segment_id}: {r.snippet}")
        """
        self.ensure_index()

        raw_results = self._index.search_text(query, nikaya, limit)
        return [
            TextSearchResult(
                segment_id=r["segment_id"],
                sutta_id=r["sutta_id"],
                nikaya=r["nikaya"],
                snippet=r["snippet"],
            )
            for r in raw_results
        ]

    def get_all_lemmas(self) -> list[str]:
        """Get all unique lemmas in the corpus.

        Returns:
            Sorted list of all lemmas
        """
        self.ensure_index()
        return self._index.get_all_lemmas()

    def close(self) -> None:
        """Close search index."""
        self._index.close()
