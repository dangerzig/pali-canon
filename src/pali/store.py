"""JSON file store for accessing Pāli Canon data."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .models import Sutta, Segment, SuttaInfo, NikayaInfo

# Default data directory (relative to package)
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Nikāya metadata
NIKAYAS = {
    "dn": {"name_pali": "Dīgha Nikāya", "name_eng": "Long Discourses"},
    "mn": {"name_pali": "Majjhima Nikāya", "name_eng": "Middle Length Discourses"},
    "sn": {"name_pali": "Saṃyutta Nikāya", "name_eng": "Connected Discourses"},
    "an": {"name_pali": "Aṅguttara Nikāya", "name_eng": "Numerical Discourses"},
    "kn": {"name_pali": "Khuddaka Nikāya", "name_eng": "Minor Collection"},
}

# Collections with nested sutta structure
NESTED_COLLECTIONS = {"sn", "an"}

# Collections with items structure (KN)
ITEMS_COLLECTIONS = {"kn"}

# KN text prefixes (texts in Khuddaka Nikāya have their own ID prefixes)
KN_TEXT_PREFIXES = {
    "kp", "dhp", "ud", "iti", "snp", "vv", "pv", "thag", "thig",
    "tha-ap", "thi-ap", "bv", "cp", "ja", "mnd", "cnd", "ps",
    "ne", "pe", "mil",
}


class Store:
    """Access layer for JSON data files."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize store with data directory.

        Args:
            data_dir: Path to data directory. Defaults to package data dir.
        """
        self.data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self.canonical_dir = self.data_dir / "canonical"
        self.lemmatized_dir = self.data_dir / "lemmatized"
        self._index_cache = {}

    def _get_data_dir(self, lemmatized: bool) -> Path:
        """Get appropriate data directory."""
        return self.lemmatized_dir if lemmatized else self.canonical_dir

    @lru_cache(maxsize=100)
    def _load_json(self, path: Path) -> dict:
        """Load and cache JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _id_in_range(self, sutta_id: str, range_id: str) -> bool:
        """Check if sutta_id falls within a range like 'dhp1-20'.

        Args:
            sutta_id: The ID to check (e.g., "dhp5")
            range_id: A range ID (e.g., "dhp1-20")

        Returns:
            True if sutta_id is within the range
        """
        import re

        # Extract prefix and number from sutta_id (e.g., "dhp5" -> "dhp", 5)
        match = re.match(r"([a-z]+)(\d+)$", sutta_id)
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

        # For SN/AN: file is the samyutta/nipata (sn1.json contains sn1.1, sn1.2, etc.)
        elif nikaya in NESTED_COLLECTIONS:
            # Normalize: handle both "sn1.1" and "1.1" formats
            if not sutta_id.startswith(nikaya):
                sutta_id = f"{nikaya}{sutta_id}"
            # Extract samyutta/nipata number (e.g., "sn1.1" -> "sn1")
            parts = sutta_id.split(".")
            if len(parts) >= 1:
                collection_file = parts[0]  # "sn1" or "an1"
                path = data_dir / f"{collection_file}.json"
                if path.exists():
                    return path

        # For KN: each text has its own file (dhp.json, snp.json, etc.)
        # KN texts have their own prefixes, not "kn" prefix
        elif nikaya == "kn":
            # Don't normalize - KN texts use their own prefixes (dhp, snp, etc.)
            for f in data_dir.glob("*.json"):
                if f.name.startswith("_"):
                    continue  # Skip index files
                # Check if sutta_id starts with the file's text ID
                if sutta_id.startswith(f.stem):
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
        """
        # Parse sutta_id to get nikaya
        # Check KN text prefixes FIRST (they're more specific than "sn", "an", etc.)
        nikaya = None
        for prefix in KN_TEXT_PREFIXES:
            if sutta_id.startswith(prefix):
                nikaya = "kn"
                break

        # Then check standard nikaya prefixes
        if not nikaya:
            for n in NIKAYAS:
                if sutta_id.startswith(n):
                    nikaya = n
                    break

        if not nikaya:
            return None

        path = self._find_sutta_file(nikaya, sutta_id, lemmatized)
        if not path:
            return None

        data = self._load_json(path)

        # For DN/MN: the file IS the sutta
        if nikaya in ("dn", "mn"):
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

        suttas = []

        for path in sorted(data_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue  # Skip index files

            data = self._load_json(path)

            # DN/MN: one sutta per file
            if nikaya in ("dn", "mn"):
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
