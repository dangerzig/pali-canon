#!/usr/bin/env python3
"""Release gate: run the project's acceptance checks and fail on any problem.

Runs (each must pass):
  - byte-compile of src/tests/scripts
  - corpus structure validator
  - external-data presence check
  - critical-edition schema guard (every data/critical/**/*_critical.json has the
    current apparatus schema)

Usage:  PYTHONPATH=src python scripts/release_check.py
Exits non-zero (and prints what failed) if any check fails.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CRITICAL_DIR = REPO / "data" / "critical"
REQUIRED_CRITICAL_KEYS = {"schema_version", "apparatus", "apparatus_count", "provenance"}


def _run(label: str, cmd: list[str]) -> bool:
    print(f"\n=== {label} ===")
    result = subprocess.run(cmd, cwd=REPO,
                            env={"PYTHONPATH": "src", "PATH": __import__("os").environ["PATH"]})
    ok = result.returncode == 0
    print(f"  -> {'OK' if ok else 'FAILED'} ({label})")
    return ok


def check_critical_schema() -> bool:
    print("\n=== critical-edition schema guard ===")
    if not CRITICAL_DIR.is_dir():
        print("  -> SKIP (no data/critical/)")
        return True
    bad = []
    n = 0
    for p in CRITICAL_DIR.rglob("*_critical.json"):
        n += 1
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            bad.append(f"{p}: unreadable ({e})")
            continue
        missing = REQUIRED_CRITICAL_KEYS - set(d)
        if missing:
            bad.append(f"{p}: missing {sorted(missing)}")
    if bad:
        print(f"  -> FAILED: {len(bad)}/{n} critical files off-schema")
        for b in bad[:10]:
            print(f"     {b}")
        return False
    print(f"  -> OK ({n} critical files, all on-schema)")
    return True


def main() -> int:
    checks = [
        _run("byte-compile", [sys.executable, "-m", "compileall", "-q",
                              "src", "tests", "scripts"]),
        _run("corpus validator", [sys.executable, "scripts/validate_corpus.py"]),
        _run("data check", [sys.executable, "src/pali_check_data.py"]),
        check_critical_schema(),
    ]
    print()
    if all(checks):
        print("RELEASE CHECK: PASSED")
        return 0
    print("RELEASE CHECK: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
