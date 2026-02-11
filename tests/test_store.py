"""Tests for pali.store — JSON data access layer."""

import pytest
from pathlib import Path
from conftest import requires_data

from pali.store import Store, NIKAYAS
from pali.models import Sutta, SuttaInfo, NikayaInfo


# =========================================================================
# Store initialization
# =========================================================================

class TestStoreInit:
    def test_default_data_dir(self):
        store = Store()
        assert store.data_dir.exists()

    def test_custom_data_dir(self, data_dir):
        store = Store(data_dir)
        assert store.data_dir == data_dir
        assert store.canonical_dir == data_dir / "canonical"
        assert store.lemmatized_dir == data_dir / "lemmatized"


# =========================================================================
# _id_in_range()
# =========================================================================

class TestIdInRange:
    def setup_method(self):
        self.store = Store()

    def test_in_range(self):
        assert self.store._id_in_range("dhp5", "dhp1-20") is True

    def test_at_start(self):
        assert self.store._id_in_range("dhp1", "dhp1-20") is True

    def test_at_end(self):
        assert self.store._id_in_range("dhp20", "dhp1-20") is True

    def test_out_of_range(self):
        assert self.store._id_in_range("dhp25", "dhp1-20") is False

    def test_wrong_prefix(self):
        assert self.store._id_in_range("snp1", "dhp1-20") is False

    def test_non_range_id(self):
        assert self.store._id_in_range("dhp5", "dhp") is False

    def test_invalid_sutta_id(self):
        assert self.store._id_in_range("123", "dhp1-20") is False


# =========================================================================
# _find_sutta_file()
# =========================================================================

@requires_data
class TestFindSuttaFile:
    def setup_method(self):
        self.store = Store()

    def test_dn(self):
        path = self.store._find_sutta_file("dn", "dn1", lemmatized=False)
        assert path is not None
        assert path.name == "dn1.json"

    def test_dn_without_prefix(self):
        path = self.store._find_sutta_file("dn", "1", lemmatized=False)
        assert path is not None
        assert path.name == "dn1.json"

    def test_mn(self):
        path = self.store._find_sutta_file("mn", "mn1", lemmatized=False)
        assert path is not None
        assert path.name == "mn1.json"

    def test_sn(self):
        path = self.store._find_sutta_file("sn", "sn1.1", lemmatized=False)
        assert path is not None
        assert path.name == "sn1.json"

    def test_an(self):
        path = self.store._find_sutta_file("an", "an1.1", lemmatized=False)
        assert path is not None
        assert path.name == "an1.json"

    def test_kn_dhp(self):
        path = self.store._find_sutta_file("kn", "dhp1", lemmatized=False)
        assert path is not None
        assert path.name == "dhp.json"

    def test_vinaya(self):
        path = self.store._find_sutta_file("vinaya", "mahavagga", lemmatized=False)
        assert path is not None
        assert path.name == "mahavagga.json"

    def test_abhidhamma(self):
        path = self.store._find_sutta_file("abhidhamma", "dhammasangani", lemmatized=False)
        assert path is not None
        assert path.name == "dhammasangani.json"

    def test_nonexistent(self):
        path = self.store._find_sutta_file("dn", "dn999", lemmatized=False)
        assert path is None


# =========================================================================
# get_sutta()
# =========================================================================

@requires_data
class TestGetSutta:
    def setup_method(self):
        self.store = Store()

    def test_dn_sutta(self):
        sutta = self.store.get_sutta("dn1")
        assert sutta is not None
        assert sutta.id == "dn1"
        assert sutta.title_pali == "Brahmajālasutta"
        assert len(sutta.segments) > 0

    def test_sn_nested_sutta(self):
        sutta = self.store.get_sutta("sn1.1")
        assert sutta is not None
        assert sutta.id == "sn1.1"
        assert len(sutta.segments) > 0

    def test_kn_item_direct(self):
        sutta = self.store.get_sutta("dhp1-20")
        assert sutta is not None
        assert sutta.id == "dhp1-20"

    def test_kn_range_lookup(self):
        sutta = self.store.get_sutta("dhp5")
        assert sutta is not None
        assert sutta.id == "dhp1-20"  # Returns containing range

    def test_nonexistent_sutta(self):
        sutta = self.store.get_sutta("dn999")
        assert sutta is None

    def test_invalid_id(self):
        sutta = self.store.get_sutta("xyz")
        assert sutta is None

    def test_sutta_has_text(self):
        sutta = self.store.get_sutta("dn1")
        assert sutta.text  # Non-empty string

    def test_vinaya_sutta(self):
        sutta = self.store.get_sutta("mahavagga")
        assert sutta is not None
        assert sutta.id == "mahavagga"
        assert len(sutta.segments) > 0

    def test_abhidhamma_sutta(self):
        sutta = self.store.get_sutta("dhammasangani")
        assert sutta is not None
        assert sutta.id == "dhammasangani"
        assert len(sutta.segments) > 0


# =========================================================================
# list_suttas()
# =========================================================================

@requires_data
class TestListSuttas:
    def setup_method(self):
        self.store = Store()

    def test_dn_count(self):
        suttas = self.store.list_suttas("dn")
        assert len(suttas) == 34

    def test_dn_returns_sutta_info(self):
        suttas = self.store.list_suttas("dn")
        assert all(isinstance(s, SuttaInfo) for s in suttas)
        assert suttas[0].id == "dn1"

    def test_sn_returns_individual_suttas(self):
        suttas = self.store.list_suttas("sn")
        # Should be individual suttas (>100), not samyuttas (56)
        assert len(suttas) > 100

    def test_an_returns_individual_suttas(self):
        suttas = self.store.list_suttas("an")
        assert len(suttas) > 100

    def test_kn_returns_items(self):
        suttas = self.store.list_suttas("kn")
        # Should include items like dhp1-20, not just dhp
        ids = [s.id for s in suttas]
        assert "dhp1-20" in ids or any("dhp" in i for i in ids)

    def test_vinaya_count(self):
        suttas = self.store.list_suttas("vinaya")
        assert len(suttas) == 5

    def test_abhidhamma_count(self):
        suttas = self.store.list_suttas("abhidhamma")
        assert len(suttas) == 8

    def test_invalid_nikaya(self):
        suttas = self.store.list_suttas("xyz")
        assert suttas == []


# =========================================================================
# get_nikaya_info()
# =========================================================================

@requires_data
class TestGetNikayaInfo:
    def setup_method(self):
        self.store = Store()

    def test_dn(self):
        info = self.store.get_nikaya_info("dn")
        assert info is not None
        assert info.id == "dn"
        assert info.name_pali == "Dīgha Nikāya"
        assert info.name_eng == "Long Discourses"
        assert info.sutta_count == 34

    def test_invalid(self):
        info = self.store.get_nikaya_info("xyz")
        assert info is None

    def test_sutta_count_matches_list(self):
        info = self.store.get_nikaya_info("dn")
        suttas = self.store.list_suttas("dn")
        assert info.sutta_count == len(suttas)

    def test_vinaya(self):
        info = self.store.get_nikaya_info("vinaya")
        assert info is not None
        assert info.id == "vinaya"
        assert info.sutta_count == 5

    def test_abhidhamma(self):
        info = self.store.get_nikaya_info("abhidhamma")
        assert info is not None
        assert info.id == "abhidhamma"
        assert info.sutta_count == 8


# =========================================================================
# get_segments()
# =========================================================================

@requires_data
class TestGetSegments:
    def setup_method(self):
        self.store = Store()

    def test_all_segments(self):
        segments = self.store.get_segments("dn1")
        assert len(segments) > 0
        assert segments[0].id.startswith("dn1:")

    def test_range_filter(self):
        all_segs = self.store.get_segments("dn1")
        # Get first 3 segment IDs
        if len(all_segs) >= 3:
            from_id = all_segs[0].id
            to_id = all_segs[2].id
            filtered = self.store.get_segments("dn1", from_id=from_id, to_id=to_id)
            assert len(filtered) == 3

    def test_nonexistent_sutta(self):
        segments = self.store.get_segments("dn999")
        assert segments == []
