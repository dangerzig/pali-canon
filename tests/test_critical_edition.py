"""Tests for the critical-apparatus builder (CODE_REVIEW finding 1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import build_critical_edition as bce


SYNTH_COLLATION = {
    "sutta": 1,
    "nikaya": "DN",
    "word_counts": {"gretil": 10, "sc": 10, "vri": 10, "bjt": 10, "thai": 0},
    "stats": {"total_positions": 10, "errors": 1, "variants": 1, "uncertain": 1},
    "errors": [{
        "position": 5, "gretil": "bhikkhusaṃghañ", "sc": "bhikkhusaṃghañca",
        "vri": "bhikkhusaṃghañca", "bjt": "bhikkhusaṃghaṃ", "thai": None,
        "type": "error", "confidence": 0.95, "preferred": "bhikkhusaṃghañca",
        "notes": "PTS reading not in DPD",
    }],
    "variants": [{
        "position": 2, "gretil": "a", "sc": "ā", "vri": "ā", "bjt": "a", "thai": None,
        "type": "variant", "confidence": 0.6, "preferred": "a", "notes": "variant",
    }],
    "uncertain": [{
        "position": 8, "gretil": "pi", "sc": None, "vri": None, "bjt": "pi",
        "thai": None, "type": "pts_addition", "confidence": 0.7, "preferred": "pi",
        "notes": "present in PTS only",
    }],
}


def _build():
    return bce.build_sutta_critical(
        SYNTH_COLLATION, "dn1", Path(bce.DATA_DIR / "collation" / "dn" / "dn1_collation.json"),
        "data/dpd/dpd.db", "2026-06-29T00:00:00Z")


class TestBuildSuttaCritical:
    def test_top_level_fields(self):
        ed = _build()
        assert ed["id"] == "dn1"
        assert ed["schema_version"] == bce.SCHEMA_VERSION
        assert ed["nikaya"] == "DN"
        # thai had 0 words -> excluded from witnesses
        assert ed["witnesses"] == ["GRETIL/PTS", "SC", "VRI", "BJT"]

    def test_apparatus_assembled_and_sorted(self):
        ed = _build()
        assert ed["apparatus_count"] == 3
        positions = [e["position"] for e in ed["apparatus"]]
        assert positions == sorted(positions)  # sorted by position: 2,5,8

    def test_selected_and_rejected(self):
        ed = _build()
        err = next(e for e in ed["apparatus"] if e["type"] == "error")
        assert err["selected"] == "bhikkhusaṃghañca"
        # rejected = distinct attested non-selected readings (None dropped)
        assert err["rejected"] == ["bhikkhusaṃghañ", "bhikkhusaṃghaṃ"]
        assert err["confidence"] == 0.95
        assert err["witnesses"]["thai"] is None

    def test_provenance(self):
        ed = _build()
        prov = ed["provenance"]
        assert prov["builder"] == "build_critical_edition.py"
        assert prov["collation_source"].endswith("dn1_collation.json")
        assert prov["dpd_validation_source"] == "data/dpd/dpd.db"
        assert prov["collation_stats"]["total_positions"] == 10
        assert prov["generated_at"] == "2026-06-29T00:00:00Z"


class TestBuildWritesFiles:
    def test_build_writes_critical_files(self, tmp_path, monkeypatch):
        import json
        # synthetic collation tree
        coll = tmp_path / "collation" / "dn"
        coll.mkdir(parents=True)
        (coll / "dn1_collation.json").write_text(json.dumps(SYNTH_COLLATION), encoding="utf-8")
        crit = tmp_path / "critical"
        monkeypatch.setattr(bce, "DATA_DIR", tmp_path)
        monkeypatch.setattr(bce, "COLLATION_DIR", tmp_path / "collation")
        monkeypatch.setattr(bce, "CRITICAL_DIR", crit)
        n = bce.build()
        assert n == 1
        out = crit / "dn" / "dn1_critical.json"
        assert out.exists()
        ed = json.loads(out.read_text(encoding="utf-8"))
        assert ed["apparatus_count"] == 3
