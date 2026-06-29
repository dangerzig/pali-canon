"""Tests for the pali-check-data external-data report (CODE_REVIEW finding 8)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pali_check_data


def test_passes_when_required_present(tmp_path, monkeypatch, capsys):
    (tmp_path / "dpd").mkdir()
    (tmp_path / "dpd" / "dpd.db").write_text("x")
    (tmp_path / "dpd" / "sandhi_rules.tsv").write_text("x")
    canon = tmp_path / "canonical"
    canon.mkdir()
    (canon / "dn1.json").write_text("{}")
    monkeypatch.setattr(pali_check_data, "DATA_DIR", tmp_path)
    assert pali_check_data.main() == 0
    assert "all required data present" in capsys.readouterr().out


def test_fails_when_required_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pali_check_data, "DATA_DIR", tmp_path)  # empty dir
    assert pali_check_data.main() == 1
    out = capsys.readouterr().out
    assert "MISSING" in out and "dpd/dpd.db" in out


def test_optional_missing_still_passes(tmp_path, monkeypatch):
    (tmp_path / "dpd").mkdir()
    (tmp_path / "dpd" / "dpd.db").write_text("x")
    (tmp_path / "dpd" / "sandhi_rules.tsv").write_text("x")
    (tmp_path / "canonical").mkdir()
    (tmp_path / "canonical" / "dn1.json").write_text("{}")
    # dppn/ and lemmatized/ absent (optional)
    monkeypatch.setattr(pali_check_data, "DATA_DIR", tmp_path)
    assert pali_check_data.main() == 0
