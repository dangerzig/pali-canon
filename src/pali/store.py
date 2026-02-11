"""JSON file store for accessing Pāli Canon data."""

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from .models import Sutta, Segment, SuttaInfo, NikayaInfo
from .text import (
    KN_TEXT_PREFIXES, NESTED_COLLECTIONS, ITEMS_COLLECTIONS, FLAT_COLLECTIONS,
    VINAYA_TEXT_IDS, ABHIDHAMMA_TEXT_IDS,
    parse_sutta_id, iter_file_segments,
)

# Default data directory (relative to package)
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Collection metadata
NIKAYAS = {
    "dn": {"name_pali": "Dīgha Nikāya", "name_eng": "Long Discourses"},
    "mn": {"name_pali": "Majjhima Nikāya", "name_eng": "Middle Length Discourses"},
    "sn": {"name_pali": "Saṃyutta Nikāya", "name_eng": "Connected Discourses"},
    "an": {"name_pali": "Aṅguttara Nikāya", "name_eng": "Numerical Discourses"},
    "kn": {"name_pali": "Khuddaka Nikāya", "name_eng": "Minor Collection"},
    "vinaya": {"name_pali": "Vinaya Piṭaka", "name_eng": "Basket of Discipline"},
    "abhidhamma": {"name_pali": "Abhidhamma Piṭaka", "name_eng": "Basket of Higher Doctrine"},
}


class Store:
    """Access layer for JSON data files."""

    _CACHE_SIZE = 100

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize store with data directory.

        Args:
            data_dir: Path to data directory. Defaults to package data dir.
        """
        self.data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self.canonical_dir = self.data_dir / "canonical"
        self.lemmatized_dir = self.data_dir / "lemmatized"
        self._index_cache = {}
        self._json_cache: OrderedDict[str, dict] = OrderedDict()

    def _get_data_dir(self, lemmatized: bool) -> Path:
        """Get appropriate data directory."""
        return self.lemmatized_dir if lemmatized else self.canonical_dir

    def _load_json(self, path: Path) -> dict:
        """Load and cache JSON file (LRU eviction)."""
        path_str = str(path)
        if path_str in self._json_cache:
            self._json_cache.move_to_end(path_str)
            return self._json_cache[path_str]
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(self._json_cache) >= self._CACHE_SIZE:
            self._json_cache.popitem(last=False)  # Evict least recently used
        self._json_cache[path_str] = data
        return data

    def _id_in_range(self, sutta_id: str, range_id: str) -> bool:
        """Check if sutta_id falls within a range like 'dhp1-20'.

        Args:
            sutta_id: The ID to check (e.g., "dhp5", "sn1.1", "an1.1.1")
            range_id: A range ID (e.g., "dhp1-20")

        Returns:
            True if sutta_id is within the range
        """
        # Extract prefix and number from sutta_id
        # Handles: "dhp5", "sn1.1", "an1.1.1" etc.
        # For dotted IDs, use the first number for range comparison
        match = re.match(r"([a-z]+)(\d+)", sutta_id)
        if not match:
            return False
        prefix, num = match.groups()
        num = int(num)

        # Check if range_id is actually a range (e.g., "dhp1-20")
        range_match = re.match(r"([a-z]+)(\d+)-(\d+)$", range_id)
        if not range_match:
            return False
        range_prefix, start, end = range_match.groups()

        # Prefixes must match
        if prefix != range_prefix:
            return False

        # Check if number is in range
        return int(start) <= num <= int(end)

    def _find_sutta_file(self, nikaya: str, sutta_id: str, lemmatized: bool) -> Optional[Path]:
        """Find the JSON file containing a sutta."""
        data_dir = self._get_data_dir(lemmatized) / nikaya

        # For DN/MN: direct file mapping (dn1.json, mn1.json)
        if nikaya in ("dn", "mn"):
            # Normalize: handle both "dn1" and "1" formats
            if not sutta_id.startswith(nikaya):
                sutta_id = f"{nikaya}{sutta_id}"
            num = sutta_id[len(nikaya):]
            path = data_dir / f"{nikaya}{num}.json"
            if path.exists():
                return path

        # For Vinaya/Abhidhamma: direct file mapping by text ID
        elif nikaya in ("vinaya", "abhidhamma"):
            path = data_dir / f"{sutta_id}.json"
            if path.exists():
                return path

        # For SN/AN: file is the samyutta/nipata (sn1.json contains sn1.1, sn1.2, etc.)
        elif nikaya in NESTED_COLLECTIONS:
            # Normalize: handle both "sn1.1" and "1.1" formats
            if not sutta_id.startswith(nikaya):
                sutta_id = f"{nikaya}{sutta_id}"
            # Extract samyutta/nipata number (e.g., "sn1.1" -> "sn1")
            parts = sutta_id.split(".")
            collection_file = parts[0]  # "sn1" or "an1"
            path = data_dir / f"{collection_file}.json"
            if path.exists():
                return path

        # For KN: each text has its own file (dhp.json, snp.json, etc.)
        # KN texts have their own prefixes, not "kn" prefix
        elif nikaya == "kn":
            # Build/use cached stem index for O(1) lookup
            cache_key = str(data_dir)
            if cache_key not in self._index_cache:
                stems = []
                for f in data_dir.glob("*.json"):
                    if not f.name.startswith("_"):
                        stems.append((f.stem, f))
                # Sort by stem length descending so longer prefixes match first
                stems.sort(key=lambda x: len(x[0]), reverse=True)
                self._index_cache[cache_key] = stems
            for stem, f in self._index_cache[cache_key]:
                if sutta_id.startswith(stem):
                    return f

        return None

    def get_sutta(
        self,
        sutta_id: str,
        lemmatized: bool = False,
        include_tokens: bool = True,
    ) -> Optional[Sutta]:
        """Load a single sutta by ID.

        Args:
            sutta_id: Sutta ID (e.g., "dn1", "mn1", "sn1.1", "an1.1")
            lemmatized: Whether to load lemmatized version
            include_tokens: Whether to include token data (only for lemmatized)

        Returns:
            Sutta object or None if not found

        Note:
            For Khuddaka Nikāya (KN) texts that are organized by vagga ranges
            (e.g., Dhammapada verses "dhp1-20"), requesting a specific verse
            like "dhp5" will return the containing range item ("dhp1-20").
            The returned Sutta.id will be the range ID, not the requested ID.
            This matches the traditional vagga organization of these texts.
        """
        nikaya = parse_sutta_id(sutta_id)
        if not nikaya:
            return None

        path = self._find_sutta_file(nikaya, sutta_id, lemmatized)
        if not path:
            return None

        data = self._load_json(path)

        # For DN/MN/Vinaya/Abhidhamma: the file IS the text
        if nikaya in FLAT_COLLECTIONS:
            return Sutta.from_dict(data, include_tokens=include_tokens and lemmatized)

        # For SN/AN: find the specific sutta in the nested structure
        elif nikaya in NESTED_COLLECTIONS:
            for sutta_data in data.get("suttas", []):
                if sutta_data.get("id") == sutta_id:
                    # Build Sutta from nested data
                    return Sutta(
                        id=sutta_data["id"],
                        title_pali=data.get("name_pali"),
                        collection=nikaya,
                        vagga=data.get("vagga"),
                        pts=data.get("pts"),
                        segments=[
                            Segment.from_dict(s, include_tokens=include_tokens and lemmatized)
                            for s in sutta_data.get("segments", [])
                        ],
                    )

        # For KN: find in items structure
        elif nikaya == "kn":
            # The whole file might be a single "sutta" or have items
            if "items" in data:
                for item in data["items"]:
                    item_id = item.get("id", "")
                    if item_id == sutta_id or self._id_in_range(sutta_id, item_id):
                        return Sutta(
                            id=item_id,
                            title_pali=data.get("name_pali"),
                            collection=nikaya,
                            segments=[
                                Segment.from_dict(s, include_tokens=include_tokens and lemmatized)
                                for s in item.get("segments", [])
                            ],
                        )
            else:
                # Single text file (like some KN texts)
                return Sutta.from_dict(data, include_tokens=include_tokens and lemmatized)

        return None

    def list_nikayas(self) -> list[str]:
        """List available nikāyas."""
        return list(NIKAYAS.keys())

    def get_nikaya_info(self, nikaya: str) -> Optional[NikayaInfo]:
        """Get metadata for a nikāya."""
        if nikaya not in NIKAYAS:
            return None

        meta = NIKAYAS[nikaya]
        suttas = self.list_suttas(nikaya)

        # Count segments
        segment_count = sum(s.segment_count or 0 for s in suttas)

        return NikayaInfo(
            id=nikaya,
            name_pali=meta["name_pali"],
            name_eng=meta["name_eng"],
            sutta_count=len(suttas),
            segment_count=segment_count,
        )

    def list_suttas(self, nikaya: str, lemmatized: bool = False) -> list[SuttaInfo]:
        """List all suttas in a nikāya.

        Args:
            nikaya: Nikāya ID (dn, mn, sn, an, kn)
            lemmatized: Whether to use lemmatized data

        Returns:
            List of SuttaInfo objects
        """
        data_dir = self._get_data_dir(lemmatized) / nikaya
        if not data_dir.exists():
            return []

        # Try to use index file for faster loading (DN/MN only)
        index_path = data_dir / "_index.json"
        if index_path.exists():
            result = self._list_suttas_from_index(index_path)
            if result:
                return result

        # Fallback: scan individual files (used for SN/AN/KN and when no index)
        return self._list_suttas_from_files(data_dir, nikaya)

    def _list_suttas_from_index(self, index_path: Path) -> list[SuttaInfo]:
        """Load sutta list from pre-built index file (fast path).

        Only handles indexes with a 'suttas' key (DN/MN) where each entry
        is an individual sutta. Returns empty for SN/AN/KN indexes which
        have collection-level keys (samyuttas/nipatas/texts) — the caller
        falls through to _list_suttas_from_files() for those.
        """
        data = self._load_json(index_path)
        suttas = []

        if "suttas" in data:
            for s in data["suttas"]:
                suttas.append(SuttaInfo(
                    id=s["id"],
                    title_pali=s.get("title_pali"),
                    title_eng=s.get("title_eng"),
                    vagga=s.get("vagga"),
                    pts=s.get("pts"),
                    segment_count=s.get("segments"),
                ))

        return suttas

    def _list_suttas_from_files(self, data_dir: Path, nikaya: str) -> list[SuttaInfo]:
        """Load sutta list by scanning individual files (slow fallback)."""
        suttas = []

        for path in sorted(data_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue  # Skip index files

            data = self._load_json(path)

            # DN/MN/Vinaya/Abhidhamma: one text per file
            if nikaya in FLAT_COLLECTIONS:
                segment_count = len(data.get("segments", []))
                suttas.append(SuttaInfo(
                    id=data["id"],
                    title_pali=data.get("title_pali"),
                    title_eng=data.get("title_eng"),
                    vagga=data.get("vagga"),
                    pts=data.get("pts"),
                    segment_count=segment_count,
                ))

            # SN/AN: multiple suttas per file
            elif nikaya in NESTED_COLLECTIONS:
                for sutta_data in data.get("suttas", []):
                    segment_count = len(sutta_data.get("segments", []))
                    suttas.append(SuttaInfo(
                        id=sutta_data["id"],
                        title_pali=data.get("name_pali"),
                        vagga=data.get("vagga"),
                        pts=data.get("pts"),
                        segment_count=segment_count,
                    ))

            # KN: items or single text
            elif nikaya == "kn":
                if "items" in data:
                    for item in data["items"]:
                        segment_count = len(item.get("segments", []))
                        suttas.append(SuttaInfo(
                            id=item["id"],
                            title_pali=data.get("name_pali"),
                            segment_count=segment_count,
                        ))
                else:
                    segment_count = len(data.get("segments", []))
                    suttas.append(SuttaInfo(
                        id=data["id"],
                        title_pali=data.get("name_pali") or data.get("title_pali"),
                        title_eng=data.get("name_eng") or data.get("title_eng"),
                        segment_count=segment_count,
                    ))

        return suttas

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
        """
        sutta = self.get_sutta(sutta_id, lemmatized=lemmatized)
        if not sutta:
            return []

        segments = sutta.segments

        # Filter by range if specified
        if from_id or to_id:
            filtered = []
            in_range = from_id is None

            for seg in segments:
                if from_id and seg.id == from_id:
                    in_range = True

                if in_range:
                    filtered.append(seg)

                if to_id and seg.id == to_id:
                    break

            segments = filtered

        return segments
