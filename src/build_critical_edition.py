#!/usr/bin/env python3
"""Assemble apparatus-bearing critical editions from collation output.

The previous data/critical/ output was summary-only (id, witnesses, word_count).
This builder turns the per-sutta collation files under data/collation/ — which
already record, at every divergent position, each witness's reading plus a
selected ("preferred") reading, a confidence, a type, and a note — into a real
critical apparatus with provenance.

Output: data/critical/<nikaya>/<id>_critical.json, schema below
(see docs/critical_edition_schema.md). Run:  PYTHONPATH=src python src/build_critical_edition.py
"""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COLLATION_DIR = DATA_DIR / "collation"
CRITICAL_DIR = DATA_DIR / "critical"

SCHEMA_VERSION = 1
WITNESS_KEYS = ("gretil", "sc", "vri", "bjt", "thai")
WITNESS_LABELS = {
    "gretil": "GRETIL/PTS", "sc": "SC", "vri": "VRI", "bjt": "BJT", "thai": "Thai",
}
# Collation categories that contribute apparatus entries (matches are omitted —
# an apparatus only records divergences from the selected reading).
APPARATUS_CATEGORIES = ("errors", "variants", "uncertain")

logger = logging.getLogger(__name__)


def _apparatus_entry(entry: dict) -> dict:
    """Turn one collation divergence into a critical-apparatus entry."""
    readings = {w: entry.get(w) for w in WITNESS_KEYS}
    selected = entry.get("preferred")
    # Distinct attested readings other than the selected one.
    rejected = sorted({r for r in readings.values() if r and r != selected})
    return {
        "position": entry.get("position"),
        "type": entry.get("type"),
        "selected": selected,
        "confidence": entry.get("confidence"),
        "witnesses": readings,
        "rejected": rejected,
        "notes": entry.get("notes"),
    }


def build_sutta_critical(collation: dict, edition_id: str, source_path: Path,
                         dpd_source: Optional[str], generated_at: str) -> dict:
    """Build the critical-edition dict for one sutta from its collation."""
    apparatus = []
    for category in APPARATUS_CATEGORIES:
        for entry in collation.get(category, []):
            apparatus.append(_apparatus_entry(entry))
    apparatus.sort(key=lambda e: (e["position"] is None, e["position"]))

    word_counts = collation.get("word_counts", {})
    witnesses = [WITNESS_LABELS[w] for w in WITNESS_KEYS if word_counts.get(w)]

    return {
        "id": edition_id,
        "schema_version": SCHEMA_VERSION,
        "nikaya": collation.get("nikaya"),
        "witnesses": witnesses,
        "word_counts": word_counts,
        "apparatus_count": len(apparatus),
        "apparatus": apparatus,
        "provenance": {
            "generated_at": generated_at,
            "builder": "build_critical_edition.py",
            "collation_source": str(source_path.relative_to(DATA_DIR.parent)),
            "dpd_validation_source": dpd_source,
            "collation_stats": collation.get("stats"),
        },
    }


def _dpd_source() -> Optional[str]:
    """Best-effort DPD validation provenance (shared with collation)."""
    try:
        from collate_nikaya import get_dpd_validation_source
        return get_dpd_validation_source()
    except Exception:
        return None


def build(collations: Optional[list[str]] = None) -> int:
    """Build critical editions for all (or selected) collation files.

    Returns the number of critical files written.
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    dpd_source = _dpd_source()
    written = 0
    nikaya_dirs = sorted(d for d in COLLATION_DIR.iterdir() if d.is_dir())
    for nik_dir in nikaya_dirs:
        out_dir = CRITICAL_DIR / nik_dir.name
        for coll_file in sorted(nik_dir.glob("*_collation.json")):
            if coll_file.name.startswith("_"):
                continue
            edition_id = coll_file.name.replace("_collation.json", "")
            if collations and edition_id not in collations:
                continue
            collation = json.loads(coll_file.read_text(encoding="utf-8"))
            edition = build_sutta_critical(
                collation, edition_id, coll_file, dpd_source, generated_at)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{edition_id}_critical.json").write_text(
                json.dumps(edition, ensure_ascii=False, indent=2), encoding="utf-8")
            written += 1
        logger.info("Built %s critical editions for %s", written, nik_dir.name)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s",
                        datefmt="%H:%M:%S")
    parser = argparse.ArgumentParser(description="Build critical-apparatus editions")
    parser.add_argument("--only", nargs="*", help="Only these edition ids (e.g. dn1)")
    args = parser.parse_args()
    n = build(collations=args.only)
    print(f"Wrote {n} critical editions to {CRITICAL_DIR}")


if __name__ == "__main__":
    main()
