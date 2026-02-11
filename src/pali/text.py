"""Shared text utilities for Pāli text processing.

Canonical implementations of tokenization, word counting, nikāya detection,
and title normalization used throughout the pipeline. Import from here rather
than defining locally.
"""

import re
from pathlib import Path
from typing import Optional

# Canonical Pāli word pattern — matches sequences of Pāli characters
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Tokenize Pāli text into lowercase words.

    Args:
        text: Raw Pāli text

    Returns:
        List of lowercase Pāli words
    """
    return PALI_WORD_PATTERN.findall(text.lower())


def word_count(text: str) -> int:
    """Count Pāli words in text.

    Uses the Pāli regex rather than text.split() to exclude
    punctuation, numbers, and non-Pāli tokens from the count.

    Args:
        text: Raw Pāli text

    Returns:
        Number of Pāli words
    """
    return len(PALI_WORD_PATTERN.findall(text))


def tokenize_with_positions(text: str) -> tuple[list[str], list[int]]:
    """Tokenize text and return both word list and character positions.

    Args:
        text: Raw Pāli text

    Returns:
        Tuple of (lowercased words, character start positions)
    """
    words = []
    positions = []
    for m in PALI_WORD_PATTERN.finditer(text):
        words.append(m.group().lower())
        positions.append(m.start())
    return words, positions


# -------------------------------------------------------------------------
# Nikāya detection utilities
# -------------------------------------------------------------------------

# KN text prefixes (texts in Khuddaka Nikāya have their own ID prefixes)
KN_TEXT_PREFIXES = {
    "kp", "dhp", "ud", "iti", "snp", "vv", "pv", "thag", "thig",
    "tha-ap", "thi-ap", "bv", "cp", "ja", "mnd", "cnd", "ps",
    "ne", "pe", "mil",
}

# Vinaya text IDs (each is a standalone text in data/canonical/vinaya/)
VINAYA_TEXT_IDS = {
    "suttavibhanga1", "suttavibhanga2", "mahavagga", "cullavagga", "parivara",
}

# Abhidhamma text IDs (each is a standalone text in data/canonical/abhidhamma/)
ABHIDHAMMA_TEXT_IDS = {
    "dhammasangani", "vibhanga", "dhatukatha", "puggalapannatti",
    "kathavatthu", "yamaka1", "yamaka2", "patthana",
}

# Standard collection codes (includes all three piṭakas)
NIKAYA_CODES = ("dn", "mn", "sn", "an", "kn", "vinaya", "abhidhamma")

# Collections with nested sutta structure
NESTED_COLLECTIONS = {"sn", "an"}

# Collections with items structure (KN)
ITEMS_COLLECTIONS = {"kn"}

# Collections with flat segments (one text per file, like DN/MN)
FLAT_COLLECTIONS = {"dn", "mn", "vinaya", "abhidhamma"}


def parse_sutta_id(sutta_id: str) -> Optional[str]:
    """Determine which collection a text ID belongs to.

    Checks specific text ID sets first (KN, Vinaya, Abhidhamma),
    then standard nikāya prefixes.

    Args:
        sutta_id: Text ID (e.g., "dn1", "sn1.1", "dhp1", "mahavagga")

    Returns:
        Collection code ("dn", "mn", "sn", "an", "kn", "vinaya",
        "abhidhamma") or None
    """
    # Check Vinaya/Abhidhamma text IDs (exact match)
    if sutta_id in VINAYA_TEXT_IDS:
        return "vinaya"
    if sutta_id in ABHIDHAMMA_TEXT_IDS:
        return "abhidhamma"
    # Check KN text prefixes
    for prefix in KN_TEXT_PREFIXES:
        if sutta_id.startswith(prefix):
            return "kn"
    # Check standard nikāya prefixes
    for n in NIKAYA_CODES:
        if sutta_id.startswith(n):
            return n
    return None


def normalize_pali(text: str) -> str:
    """Normalize Pāli text for consistent processing.

    Standardizes niggahīta (ṁ → ṃ) and cleans up whitespace.

    Args:
        text: Raw Pāli text

    Returns:
        Normalized text
    """
    text = text.replace('ṁ', 'ṃ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_title(title: str) -> str:
    """Normalize a sutta title for fuzzy comparison.

    Strips 'sutta/suttaṃ' suffix, ordinal prefixes, and whitespace.

    Args:
        title: Raw sutta title

    Returns:
        Normalized title for comparison
    """
    t = title.lower().strip()
    t = re.sub(r'\s*sutta[ṃm]?\.?\s*$', '', t)
    t = re.sub(r'^(paṭhama|dutiya|tatiya|catuttha|pañcama)\s*', '', t)
    t = re.sub(r'\s+', '', t)
    return t


def iter_file_segments(data: dict, nikaya: str):
    """Iterate over segments in a canonical JSON file, regardless of structure.

    Yields (doc_id, segments_list) tuples. Handles all three structures:
    - DN/MN: flat segments → yields (sutta_id, segments)
    - SN/AN: nested suttas → yields (sutta_id, segments) per sutta
    - KN: items or flat → yields (item_id, segments) per item

    Args:
        data: Parsed JSON data from a canonical file
        nikaya: Nikāya code ("dn", "mn", "sn", "an", "kn")

    Yields:
        (doc_id, segments_list) tuples
    """
    if nikaya in FLAT_COLLECTIONS:
        yield (data["id"], data.get("segments", []))
    elif nikaya in NESTED_COLLECTIONS:
        for sutta_data in data.get("suttas", []):
            yield (sutta_data["id"], sutta_data.get("segments", []))
    elif nikaya == "kn":
        if "items" in data:
            for item in data["items"]:
                yield (item["id"], item.get("segments", []))
        else:
            yield (data["id"], data.get("segments", []))
