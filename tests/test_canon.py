"""Tests for pali.Canon — top-level API integration tests."""

import pytest
from conftest import requires_data, slow

from pali import Canon, Sutta, Segment, SuttaInfo, NikayaInfo

try:
    import pandas
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


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

    def test_close_clears_resources(self, data_dir):
        from pali import Canon
        c = Canon(data_dir)
        # Force search initialization
        c._get_search()
        assert c._search is not None
        c.close()
        assert c._search is None
        assert c._vocab is None
        assert c._exporter is None

    def test_export_vocabulary(self, canon, tmp_path):
        output = tmp_path / "vocab.csv"
        canon.export_vocabulary("dn", str(output))
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "lemma,count" in content

    @pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed")
    def test_export_dtm(self, canon, tmp_path):
        output = tmp_path / "dtm.csv"
        canon.export_dtm("dn", str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_export_latex(self, canon, tmp_path):
        output = tmp_path / "dn1.tex"
        canon.export_latex("dn1", str(output))
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "\\begin{document}" in content

    @slow
    def test_export_pdf_returns_bool(self, canon, tmp_path):
        output = tmp_path / "dn1.pdf"
        result = canon.export_pdf("dn1", str(output))
        assert isinstance(result, bool)

    @slow
    def test_export_tipitaka_raw(self, canon, tmp_path):
        import csv
        csv.field_size_limit(10 * 1024 * 1024)
        output = tmp_path / "raw.csv"
        canon.export_tipitaka_raw(str(output))
        assert output.exists()
        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "book" in reader.fieldnames

    @slow
    def test_export_tipitaka_data_creates_all_files(self, canon, tmp_path):
        outdir = tmp_path / "export"
        canon.export_tipitaka_data(str(outdir))
        expected = [
            "tipitaka_raw.csv",
            "tipitaka_suttas_raw.csv",
            "tipitaka_long.csv",
            "tipitaka_long_words.csv",
            "tipitaka_wide.csv",
            "tipitaka_suttas_long.csv",
            "tipitaka_suttas_wide.csv",
        ]
        for filename in expected:
            assert (outdir / filename).exists(), f"Missing: {filename}"
            assert (outdir / filename).stat().st_size > 0, f"Empty: {filename}"
