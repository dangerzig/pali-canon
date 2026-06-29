"""Shared fixtures for pali library tests."""

import sys
from pathlib import Path

import pytest

# Add src to path so we can import pali package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DATA_DIR = Path(__file__).parent.parent / "data"


def has_canonical_data():
    """Check if canonical data directory exists with content."""
    return (DATA_DIR / "canonical" / "dn" / "dn1.json").exists()


def has_lemmatized_data():
    """Check if lemmatized data directory exists with content."""
    return (DATA_DIR / "lemmatized" / "dn" / "dn1.json").exists()


requires_data = pytest.mark.skipif(
    not has_canonical_data(),
    reason="Canonical data files not present"
)

requires_lemmatized = pytest.mark.skipif(
    not has_lemmatized_data(),
    reason="Lemmatized data files not present"
)

# Reusable tier markers (registered in pytest.ini). Import from conftest so the
# fast tier (`-m "not slow and not corpus"`) is consistent across test modules.
slow = pytest.mark.slow
corpus = pytest.mark.corpus


@pytest.fixture
def data_dir():
    """Path to the data directory."""
    return DATA_DIR


@pytest.fixture
def store():
    """Store instance for data access."""
    from pali.store import Store
    return Store(DATA_DIR)


@pytest.fixture
def canon():
    """Canon instance with context manager cleanup."""
    from pali import Canon
    with Canon(DATA_DIR) as c:
        yield c
