"""Tests for pali.Canon — top-level API integration tests."""

import pytest
from conftest import requires_data

from pali import Canon, Sutta, Segment, SuttaInfo, NikayaInfo


# =========================================================================
# Canon basics
# =========================================================================

@requires_data
class TestCanon:
    def test_context_manager(self, data_dir):
        with Canon(data_dir) as canon:
            nikayas = canon.list_nikayas()
            assert len(nikayas) > 0
        # After exit, search should be cleaned up
        assert canon._search is None

    def test_list_nikayas(self, canon):
        nikayas = canon.list_nikayas()
        assert nikayas == ["dn", "mn", "sn", "an", "kn", "vinaya", "abhidhamma"]

    def test_get_nikaya_info(self, canon):
        info = canon.get_nikaya_info("dn")
        assert isinstance(info, NikayaInfo)
        assert info.id == "dn"
        assert info.name_pali == "Dīgha Nikāya"
        assert info.sutta_count == 34

    def test_get_nikaya_info_invalid(self, canon):
        assert canon.get_nikaya_info("xyz") is None

    def test_list_suttas(self, canon):
        suttas = canon.list_suttas("dn")
        assert len(suttas) == 34
        assert all(isinstance(s, SuttaInfo) for s in suttas)

    def test_get_sutta(self, canon):
        sutta = canon.get_sutta("dn1")
        assert isinstance(sutta, Sutta)
        assert sutta.id == "dn1"
        assert sutta.title_pali == "Brahmajālasutta"
        assert sutta.segment_count > 0

    def test_get_sutta_not_found(self, canon):
        assert canon.get_sutta("dn999") is None

    def test_get_text(self, canon):
        text = canon.get_text("dn1")
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Evaṃ" in text

    def test_get_text_not_found(self, canon):
        assert canon.get_text("dn999") is None

    def test_get_segments(self, canon):
        segments = canon.get_segments("dn1")
        assert len(segments) > 0
        assert all(isinstance(s, Segment) for s in segments)
        assert segments[0].id.startswith("dn1:")

    def test_get_nikaya_info_vinaya(self, canon):
        info = canon.get_nikaya_info("vinaya")
        assert isinstance(info, NikayaInfo)
        assert info.id == "vinaya"
        assert info.sutta_count > 0

    def test_get_nikaya_info_abhidhamma(self, canon):
        info = canon.get_nikaya_info("abhidhamma")
        assert isinstance(info, NikayaInfo)
        assert info.id == "abhidhamma"
        assert info.sutta_count > 0

    def test_get_sutta_vinaya(self, canon):
        sutta = canon.get_sutta("mahavagga")
        assert isinstance(sutta, Sutta)
        assert sutta.id == "mahavagga"
        assert sutta.segment_count > 0

    def test_get_sutta_abhidhamma(self, canon):
        sutta = canon.get_sutta("dhammasangani")
        assert isinstance(sutta, Sutta)
        assert sutta.id == "dhammasangani"
        assert sutta.segment_count > 0

    def test_list_suttas_vinaya(self, canon):
        suttas = canon.list_suttas("vinaya")
        assert len(suttas) == 5

    def test_list_suttas_abhidhamma(self, canon):
        suttas = canon.list_suttas("abhidhamma")
        assert len(suttas) == 8

    def test_to_latex(self, canon):
        latex = canon.to_latex("dn1")
        assert isinstance(latex, str)
        assert "\\begin{document}" in latex
        assert "Brahmajālasutta" in latex
