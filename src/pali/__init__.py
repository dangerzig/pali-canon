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
from typing import Optional

from .models import Sutta, Segment, Token, SuttaInfo, NikayaInfo
from .store import Store, NIKAYAS

__all__ = [
    "Canon",
    "Sutta",
    "Segment",
    "Token",
    "SuttaInfo",
    "NikayaInfo",
]


class Canon:
    """Main interface for accessing Pāli Canon data.

    Provides methods to navigate and retrieve texts from the five nikāyas:
    - DN (Dīgha Nikāya) - Long Discourses
    - MN (Majjhima Nikāya) - Middle Length Discourses
    - SN (Saṃyutta Nikāya) - Connected Discourses
    - AN (Aṅguttara Nikāya) - Numerical Discourses
    - KN (Khuddaka Nikāya) - Minor Collection

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
