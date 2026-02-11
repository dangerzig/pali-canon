"""Pāli Canon critical edition library.

Simple Python API for accessing Pāli Canon data including:
- Canonical text from multiple editions (SC, PTS, VRI)
- Lemmatized text with token-level analysis
- Critical apparatus with variant readings

Usage:
    from pali import Canon

    canon = Canon()

    # List available nikāyas
    nikayas = canon.list_nikayas()  # ['dn', 'mn', 'sn', 'an', 'kn']

    # Get a sutta
    sutta = canon.get_sutta("dn1")
    print(sutta.title_pali)  # "Brahmajālasutta"
    print(sutta.text)        # Full Pāli text

    # Get lemmatized version with token analysis
    sutta = canon.get_sutta("dn1", lemmatized=True)
    for segment in sutta.segments:
        for token in segment.tokens:
            print(f"{token.word} -> {token.lemma}")
"""

from pathlib import Path
from typing import Optional, Union

from .models import Sutta, Segment, Token, SuttaInfo, NikayaInfo
from .store import Store, NIKAYAS
from .search import Search, LemmaSearchResult, TextSearchResult
from .vocab import Vocabulary, VocabularyStats
from .export import Exporter

__all__ = [
    "Canon",
    "Sutta",
    "Segment",
    "Token",
    "SuttaInfo",
    "NikayaInfo",
    "LemmaSearchResult",
    "TextSearchResult",
    "VocabularyStats",
]


class Canon:
    """Main interface for accessing Pāli Canon data.

    Provides methods to navigate and retrieve texts from the complete Tipiṭaka:

    Sutta Piṭaka:
    - DN (Dīgha Nikāya) - Long Discourses
    - MN (Majjhima Nikāya) - Middle Length Discourses
    - SN (Saṃyutta Nikāya) - Connected Discourses
    - AN (Aṅguttara Nikāya) - Numerical Discourses
    - KN (Khuddaka Nikāya) - Minor Collection

    Vinaya Piṭaka:
    - Suttavibhaṅga I & II, Mahāvagga, Cūḷavagga, Parivāra

    Abhidhamma Piṭaka:
    - Dhammasaṅgaṇī, Vibhaṅga, Dhātukathā, Puggalapaññatti,
      Kathāvatthu, Yamaka I & II, Paṭṭhāna

    Example:
        canon = Canon()

        # Get info about a nikāya
        info = canon.get_nikaya_info("dn")
        print(f"{info.name_pali}: {info.sutta_count} suttas")

        # List suttas in a nikāya
        for sutta_info in canon.list_suttas("mn"):
            print(f"{sutta_info.id}: {sutta_info.title_pali}")

        # Get a specific sutta
        sutta = canon.get_sutta("mn1", lemmatized=True)
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize Canon with data directory.

        Args:
            data_dir: Path to data directory containing canonical/ and lemmatized/
                     subdirectories. Defaults to package data directory.
        """
        self._store = Store(data_dir)
        self._search: Optional[Search] = None
        self._vocab: Optional[Vocabulary] = None
        self._exporter: Optional[Exporter] = None

    def close(self) -> None:
        """Close any open resources."""
        if self._search is not None:
            self._search.close()
            self._search = None
        self._vocab = None
        self._exporter = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _get_search(self) -> Search:
        """Get or create search instance (lazy initialization)."""
        if self._search is None:
            self._search = Search(self._store.data_dir)
        return self._search

    def list_nikayas(self) -> list[str]:
        """List available nikāya IDs.

        Returns:
            List of nikāya IDs: ['dn', 'mn', 'sn', 'an', 'kn']
        """
        return self._store.list_nikayas()

    def get_nikaya_info(self, nikaya: str) -> Optional[NikayaInfo]:
        """Get metadata for a nikāya.

        Args:
            nikaya: Nikāya ID (dn, mn, sn, an, kn)

        Returns:
            NikayaInfo with name, sutta count, segment count, or None if not found
        """
        return self._store.get_nikaya_info(nikaya)

    def list_suttas(self, nikaya: str, lemmatized: bool = False) -> list[SuttaInfo]:
        """List all suttas in a nikāya.

        Args:
            nikaya: Nikāya ID (dn, mn, sn, an, kn)
            lemmatized: Whether to use lemmatized data directory

        Returns:
            List of SuttaInfo objects with id, title, segment count
        """
        return self._store.list_suttas(nikaya, lemmatized=lemmatized)

    def get_sutta(
        self,
        sutta_id: str,
        lemmatized: bool = False,
        include_tokens: bool = True,
    ) -> Optional[Sutta]:
        """Load a single sutta by ID.

        Args:
            sutta_id: Sutta ID in standard format:
                     - DN/MN: "dn1", "mn1"
                     - SN/AN: "sn1.1", "an1.1"
                     - KN: "dhp1", "snp1.1"
            lemmatized: Whether to load lemmatized version with token analysis
            include_tokens: Whether to include token data (only when lemmatized=True)

        Returns:
            Sutta object with segments, or None if not found

        Example:
            sutta = canon.get_sutta("dn1")
            print(sutta.title_pali)
            print(sutta.segment_count)

            # With lemmatization
            sutta = canon.get_sutta("dn1", lemmatized=True)
            for seg in sutta.segments:
                print(f"{seg.id}: {len(seg.tokens)} tokens")
        """
        return self._store.get_sutta(
            sutta_id,
            lemmatized=lemmatized,
            include_tokens=include_tokens
        )

    def get_segments(
        self,
        sutta_id: str,
        from_id: Optional[str] = None,
        to_id: Optional[str] = None,
        lemmatized: bool = False,
    ) -> list[Segment]:
        """Get segments from a sutta, optionally filtered by range.

        Args:
            sutta_id: Sutta ID
            from_id: Starting segment ID (inclusive)
            to_id: Ending segment ID (inclusive)
            lemmatized: Whether to load lemmatized version

        Returns:
            List of Segment objects

        Example:
            # Get all segments
            segments = canon.get_segments("dn1")

            # Get a range
            segments = canon.get_segments("dn1", from_id="dn1:1.1.1", to_id="dn1:1.1.10")
        """
        return self._store.get_segments(
            sutta_id,
            from_id=from_id,
            to_id=to_id,
            lemmatized=lemmatized,
        )

    def get_text(self, sutta_id: str, lemmatized: bool = False) -> Optional[str]:
        """Get full text of a sutta as a single string.

        Convenience method that returns just the Pāli text without metadata.

        Args:
            sutta_id: Sutta ID
            lemmatized: Whether to use lemmatized data

        Returns:
            Full Pāli text as string, or None if sutta not found
        """
        sutta = self.get_sutta(sutta_id, lemmatized=lemmatized, include_tokens=False)
        if sutta:
            return sutta.text
        return None

    # -------------------------------------------------------------------------
    # Search methods
    # -------------------------------------------------------------------------

    def search_lemma(
        self,
        lemma: str,
        nikaya: Optional[str] = None,
        limit: int = 1000,
    ) -> LemmaSearchResult:
        """Search for all occurrences of a lemma.

        Searches the lemmatized corpus for all forms of a dictionary headword.
        On first call, builds a search index (takes a few minutes).

        Args:
            lemma: The lemma (dictionary form) to search for
            nikaya: Optional filter by nikaya (dn, mn, sn, an, kn)
            limit: Maximum occurrences to return (default 1000)

        Returns:
            LemmaSearchResult with:
            - total: Total occurrence count
            - by_nikaya: Dict of counts per nikaya
            - occurrences: List of LemmaOccurrence objects

        Example:
            results = canon.search_lemma("dhamma")
            print(f"Found {results.total} occurrences")
            print(f"By nikaya: {results.by_nikaya}")

            for occ in results.occurrences[:10]:
                print(f"  {occ.segment_id}: {occ.word} ({occ.pos})")
        """
        return self._get_search().search_lemma(lemma, nikaya, limit)

    def search_text(
        self,
        query: str,
        nikaya: Optional[str] = None,
        limit: int = 100,
    ) -> list[TextSearchResult]:
        """Full-text search on segment text.

        Uses SQLite FTS5 for fast text search. Supports query syntax:
        - Simple terms: "buddha" finds segments containing "buddha"
        - Phrases: '"evaṃ me sutaṃ"' finds exact phrase
        - AND/OR: "buddha OR dhamma"
        - Prefix: "bodhi*" finds bodhisatta, etc.

        Args:
            query: Search query
            nikaya: Optional filter by nikaya
            limit: Maximum results (default 100)

        Returns:
            List of TextSearchResult with segment_id, sutta_id, and snippet

        Example:
            results = canon.search_text("evaṃ me sutaṃ")
            for r in results[:10]:
                print(f"{r.segment_id}: {r.snippet}")
        """
        return self._get_search().search_text(query, nikaya, limit)

    def get_all_lemmas(self) -> list[str]:
        """Get all unique lemmas in the corpus.

        Returns:
            Sorted list of all lemmas (dictionary headwords)
        """
        return self._get_search().get_all_lemmas()

    # -------------------------------------------------------------------------
    # Vocabulary & Analysis methods
    # -------------------------------------------------------------------------

    def _get_vocab(self) -> Vocabulary:
        """Get or create vocabulary analyzer (lazy initialization)."""
        if self._vocab is None:
            self._vocab = Vocabulary(self._store.data_dir)
        return self._vocab

    def get_vocabulary(
        self,
        sutta_id: Optional[str] = None,
        nikaya: Optional[str] = None,
        top_n: int = 100,
        as_dataframe: bool = False,
    ):
        """Get vocabulary statistics for a sutta or nikaya.

        Args:
            sutta_id: Specific sutta ID (e.g., "dn1")
            nikaya: Nikaya ID (e.g., "dn") - used if sutta_id not provided
            top_n: Number of top lemmas to include
            as_dataframe: If True, return pandas DataFrame

        Returns:
            VocabularyStats object with:
            - unique_lemmas: Count of unique lemmas
            - total_tokens: Total token count
            - top_lemmas: List of (lemma, count) tuples
            - lemma_counts: Full dict of lemma counts
            - pos_distribution: Dict of POS tag counts

        Example:
            vocab = canon.get_vocabulary("dn1")
            print(f"Unique lemmas: {vocab.unique_lemmas}")
            print(f"Top 10: {vocab.top_lemmas[:10]}")

            # As DataFrame (requires pandas)
            df = canon.get_vocabulary("dn", as_dataframe=True)
        """
        return self._get_vocab().get_vocabulary(sutta_id, nikaya, top_n, as_dataframe)

    def document_term_matrix(
        self,
        nikaya: str,
        unit: str = "sutta",
        terms: str = "lemmas",
        min_df: int = 1,
        as_dataframe: bool = False,
    ):
        """Generate a document-term matrix for analysis.

        Creates a matrix where rows are documents (suttas or segments)
        and columns are terms (lemmas or words). Useful for clustering,
        topic modeling, and other text analysis.

        Args:
            nikaya: Nikaya ID (dn, mn, sn, an, kn)
            unit: Document unit - "sutta" or "segment"
            terms: Term type - "lemmas" or "words"
            min_df: Minimum document frequency (exclude rare terms)
            as_dataframe: If True, return pandas DataFrame

        Returns:
            If as_dataframe=False: (sparse_matrix, doc_ids, term_list)
            If as_dataframe=True: pandas DataFrame with doc_id index

        Example:
            # Get sparse matrix (requires scipy)
            matrix, docs, terms = canon.document_term_matrix("dn")
            print(f"Shape: {matrix.shape}")  # (34, N) for 34 DN suttas

            # Get DataFrame (requires pandas)
            df = canon.document_term_matrix("dn", as_dataframe=True)
        """
        return self._get_vocab().document_term_matrix(nikaya, unit, terms, min_df, as_dataframe)

    def export_vocabulary(self, nikaya: str, output_path: str) -> None:
        """Export vocabulary counts to CSV.

        Args:
            nikaya: Nikaya ID
            output_path: Output file path (.csv)

        Example:
            canon.export_vocabulary("dn", "dn_vocab.csv")
        """
        self._get_vocab().export_vocabulary(nikaya, output_path)

    def export_dtm(
        self,
        nikaya: str,
        output_path: str,
        unit: str = "sutta",
        terms: str = "lemmas",
        min_df: int = 2,
    ) -> None:
        """Export document-term matrix to CSV.

        Args:
            nikaya: Nikaya ID
            output_path: Output file path (.csv)
            unit: Document unit ("sutta" or "segment")
            terms: Term type ("lemmas" or "words")
            min_df: Minimum document frequency

        Example:
            canon.export_dtm("dn", "dn_dtm.csv")
        """
        self._get_vocab().export_dtm(nikaya, output_path, unit, terms, min_df)

    # -------------------------------------------------------------------------
    # LaTeX/PDF Export methods
    # -------------------------------------------------------------------------

    def _get_exporter(self) -> Exporter:
        """Get or create exporter (lazy initialization)."""
        if self._exporter is None:
            self._exporter = Exporter(self._store.data_dir)
        return self._exporter

    def to_latex(
        self,
        sutta_ids: Union[str, list[str]],
        title: Optional[str] = None,
    ) -> str:
        """Generate LaTeX for one or more suttas.

        Creates a complete LaTeX document with:
        - Title page
        - Table of contents (for multiple suttas)
        - Properly formatted Pāli text with diacritics
        - Verse detection and formatting
        - reledmac package for critical edition features

        Args:
            sutta_ids: Single sutta ID or list of IDs
            title: Custom document title

        Returns:
            Complete LaTeX document as string

        Example:
            latex = canon.to_latex("dn1")
            latex = canon.to_latex(["dn1", "dn2"], title="Selected Suttas")
        """
        return self._get_exporter().to_latex(sutta_ids, title)

    def export_latex(
        self,
        sutta_ids: Union[str, list[str]],
        output_path: str,
        title: Optional[str] = None,
    ) -> None:
        """Export sutta(s) to LaTeX file.

        Args:
            sutta_ids: Single sutta ID or list of IDs
            output_path: Output file path (.tex)
            title: Custom document title

        Example:
            canon.export_latex("dn1", "dn1.tex")
            canon.export_latex(["dn1", "dn2"], "dn_selection.tex")
        """
        self._get_exporter().export_latex(sutta_ids, output_path, title)

    def export_pdf(
        self,
        sutta_ids: Union[str, list[str]],
        output_path: str,
        title: Optional[str] = None,
        keep_tex: bool = False,
    ) -> bool:
        """Export sutta(s) to PDF.

        Requires XeLaTeX to be installed (part of TeX Live or MacTeX).

        Args:
            sutta_ids: Single sutta ID or list of IDs
            output_path: Output file path (.pdf)
            title: Custom document title
            keep_tex: If True, keep the intermediate .tex file

        Returns:
            True if PDF generation succeeded, False otherwise

        Example:
            canon.export_pdf("dn1", "dn1.pdf")
            canon.export_pdf("dn", "digha_nikaya.pdf", title="Dīgha Nikāya")
        """
        return self._get_exporter().export_pdf(sutta_ids, output_path, title, keep_tex)

    # -------------------------------------------------------------------------
    # Tipitaka R package export methods
    # -------------------------------------------------------------------------

    def export_tipitaka_raw(self, output_path: str, use_lemmas: bool = True) -> None:
        """Export data in tipitaka_raw format for R package.

        Creates CSV with columns: book, book_name, text
        One row per nikaya with full concatenated text.

        Args:
            output_path: Output CSV path
            use_lemmas: If True, use lemmatized text source

        Example:
            canon.export_tipitaka_raw("data-raw/tipitaka_raw.csv")
        """
        self._get_vocab().export_tipitaka_raw(output_path, use_lemmas)

    def export_tipitaka_suttas_raw(self, output_path: str, use_lemmas: bool = True) -> None:
        """Export per-sutta raw text for R package.

        Creates CSV with columns: sutta, nikaya, text
        One row per sutta with the full critical edition text.

        Args:
            output_path: Output CSV path
            use_lemmas: If True, use lemmatized text source

        Example:
            canon.export_tipitaka_suttas_raw("data-raw/tipitaka_suttas_raw.csv")
        """
        self._get_vocab().export_tipitaka_suttas_raw(output_path, use_lemmas)

    def export_tipitaka_long(
        self,
        output_path: str,
        use_lemmas: bool = True,
        by_sutta: bool = False,
    ) -> None:
        """Export data in tipitaka_long format for R package.

        Creates CSV with columns: word, n, total, freq, book
        Compatible with existing tipitaka R package format.

        Args:
            output_path: Output CSV path
            use_lemmas: If True, count lemmas; otherwise surface forms
            by_sutta: If True, one entry per sutta; otherwise per nikaya

        Example:
            canon.export_tipitaka_long("data-raw/tipitaka_long.csv")
            canon.export_tipitaka_long("data-raw/tipitaka_suttas_long.csv", by_sutta=True)
        """
        self._get_vocab().export_tipitaka_long(output_path, use_lemmas, by_sutta)

    def export_tipitaka_wide(
        self,
        output_path: str,
        use_lemmas: bool = True,
        by_sutta: bool = False,
        min_freq: int = 5,
    ) -> None:
        """Export data in tipitaka_wide format for R package.

        Creates CSV with books/suttas as rows and words as columns.
        Cell values are word frequencies (count / total).

        Args:
            output_path: Output CSV path
            use_lemmas: If True, count lemmas; otherwise surface forms
            by_sutta: If True, one row per sutta; otherwise per nikaya
            min_freq: Minimum total frequency to include a word

        Example:
            canon.export_tipitaka_wide("data-raw/tipitaka_wide.csv")
        """
        self._get_vocab().export_tipitaka_wide(output_path, use_lemmas, by_sutta, min_freq)

    def export_tipitaka_texts(self, output_path: str) -> None:
        """Export both surface and lemmatized text per text unit.

        Creates CSV with columns: id, collection, pitaka, title, text, text_lemmatized
        One row per text unit (sutta/vinaya section/abhidhamma book).
        Covers the full Tipitaka (all three pitakas).

        This is the primary export for the tipitaka.critical R package.

        Args:
            output_path: Output CSV path

        Example:
            canon.export_tipitaka_texts("../tipitaka.critical/data-raw/texts.csv")
        """
        self._get_vocab().export_tipitaka_texts(output_path)

    def export_tipitaka_data(self, output_dir: str) -> None:
        """Export all data files needed for tipitaka R package.

        Covers the complete Tipiṭaka (Sutta, Vinaya, and Abhidhamma).

        Generates the following files in output_dir:
        - tipitaka_raw.csv: Full text per collection
        - tipitaka_suttas_raw.csv: Full text per text unit
        - tipitaka_long.csv: Word frequencies by collection (lemmas)
        - tipitaka_long_words.csv: Word frequencies by collection (surface forms)
        - tipitaka_wide.csv: Frequency matrix by collection
        - tipitaka_suttas_long.csv: Word frequencies by text unit
        - tipitaka_suttas_wide.csv: Frequency matrix by text unit

        Args:
            output_dir: Directory to write CSV files

        Example:
            canon.export_tipitaka_data("../tipitaka/data-raw/")
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        print("Exporting tipitaka_raw.csv...")
        self.export_tipitaka_raw(str(out / "tipitaka_raw.csv"))

        print("Exporting tipitaka_suttas_raw.csv...")
        self.export_tipitaka_suttas_raw(str(out / "tipitaka_suttas_raw.csv"))

        print("Exporting tipitaka_long.csv (lemmas by nikaya)...")
        self.export_tipitaka_long(str(out / "tipitaka_long.csv"), use_lemmas=True)

        print("Exporting tipitaka_long_words.csv (surface forms by nikaya)...")
        self.export_tipitaka_long(str(out / "tipitaka_long_words.csv"), use_lemmas=False)

        print("Exporting tipitaka_wide.csv...")
        self.export_tipitaka_wide(str(out / "tipitaka_wide.csv"), use_lemmas=True, min_freq=10)

        print("Exporting tipitaka_suttas_long.csv...")
        self._get_vocab().export_tipitaka_suttas_long(str(out / "tipitaka_suttas_long.csv"))

        print("Exporting tipitaka_suttas_wide.csv...")
        self.export_tipitaka_wide(str(out / "tipitaka_suttas_wide.csv"), use_lemmas=True, by_sutta=True, min_freq=10)

        print("Done! Files written to:", output_dir)
