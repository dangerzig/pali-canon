"""Tests for pali.export — LaTeX generation."""

import pytest
from conftest import requires_data

from pali.export import escape_latex, is_verse, format_verse, Exporter


# =========================================================================
# escape_latex()
# =========================================================================

class TestEscapeLatex:
    def test_ampersand(self):
        assert escape_latex("a & b") == r"a \& b"

    def test_percent(self):
        assert escape_latex("100%") == r"100\%"

    def test_dollar(self):
        assert escape_latex("$x$") == r"\$x\$"

    def test_hash(self):
        assert escape_latex("#1") == r"\#1"

    def test_underscore(self):
        assert escape_latex("a_b") == r"a\_b"

    def test_braces(self):
        assert escape_latex("{x}") == r"\{x\}"

    def test_empty(self):
        assert escape_latex("") == ""

    def test_pali_unchanged(self):
        text = "Evaṃ me sutaṃ"
        assert escape_latex(text) == text

    def test_backslash(self):
        assert escape_latex("a\\b") == r"a\textbackslash{}b"

    def test_backslash_with_braces(self):
        """Regression: backslash + braces must not double-escape."""
        assert escape_latex("\\{x}") == r"\textbackslash{}\{x\}"


# =========================================================================
# is_verse()
# =========================================================================

class TestIsVerse:
    def test_verse_text(self):
        # High comma/semicolon density suggests verse
        text = "Manopubbaṅgamā dhammā, manoseṭṭhā manomayā; manasā ce paduṭṭhena"
        assert is_verse(text) is True

    def test_prose_text(self):
        text = "Evaṃ me sutaṃ ekaṃ samayaṃ bhagavā sāvatthiyaṃ viharati"
        assert is_verse(text) is False

    def test_empty(self):
        assert is_verse("") is False

    def test_none(self):
        assert is_verse(None) is False


# =========================================================================
# format_verse()
# =========================================================================

class TestFormatVerse:
    def test_semicolon_to_line_break(self):
        result = format_verse("line one; line two")
        assert "\\\\\n" in result

    def test_comma_indentation(self):
        result = format_verse("half one, half two")
        assert "\\vin" in result


# =========================================================================
# Exporter.to_latex()
# =========================================================================

@requires_data
class TestExporterToLatex:
    @pytest.fixture
    def exporter(self, data_dir):
        return Exporter(data_dir)

    def test_single_sutta(self, exporter):
        latex = exporter.to_latex("dn1")
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex
        assert "Brahmajālasutta" in latex

    def test_multiple_suttas(self, exporter):
        latex = exporter.to_latex(["dn1", "dn2"])
        assert "\\tableofcontents" in latex

    def test_custom_title(self, exporter):
        latex = exporter.to_latex("dn1", title="Custom Title")
        assert "Custom Title" in latex

    def test_nonexistent_sutta(self, exporter):
        latex = exporter.to_latex("dn999")
        # Should still produce valid document structure
        assert "\\begin{document}" in latex


# =========================================================================
# Exporter.export_latex()
# =========================================================================

@requires_data
class TestExporterExportLatex:
    @pytest.fixture
    def exporter(self, data_dir):
        return Exporter(data_dir)

    def test_creates_file(self, exporter, tmp_path):
        output = tmp_path / "dn1.tex"
        exporter.export_latex("dn1", str(output))
        assert output.exists()

    def test_file_content(self, exporter, tmp_path):
        output = tmp_path / "dn1.tex"
        exporter.export_latex("dn1", str(output))
        content = output.read_text(encoding="utf-8")
        assert "\\begin{document}" in content
        assert "Brahmajālasutta" in content

    def test_custom_title(self, exporter, tmp_path):
        output = tmp_path / "custom.tex"
        exporter.export_latex("dn1", str(output), title="Test Title")
        content = output.read_text(encoding="utf-8")
        assert "Test Title" in content

    def test_multiple_suttas(self, exporter, tmp_path):
        output = tmp_path / "multi.tex"
        exporter.export_latex(["dn1", "dn2"], str(output))
        content = output.read_text(encoding="utf-8")
        assert "\\tableofcontents" in content


# =========================================================================
# Exporter.export_pdf()
# =========================================================================

@requires_data
class TestExporterExportPdf:
    @pytest.fixture
    def exporter(self, data_dir):
        return Exporter(data_dir)

    def test_returns_bool(self, exporter, tmp_path):
        output = tmp_path / "test.pdf"
        result = exporter.export_pdf("dn1", str(output))
        assert isinstance(result, bool)

    def test_keep_tex(self, exporter, tmp_path):
        output = tmp_path / "test.pdf"
        exporter.export_pdf("dn1", str(output), keep_tex=True)
        tex_path = tmp_path / "test.tex"
        # .tex file should exist regardless of whether PDF compiled
        assert tex_path.exists()
