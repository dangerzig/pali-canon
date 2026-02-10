#!/usr/bin/env python3
"""
Automated test runner for all validation scripts.

Runs all test scripts in the scripts/ directory and reports
overall status. Use as a pre-commit check or CI smoke test.

Usage:
    python scripts/run_tests.py           # Run all tests
    python scripts/run_tests.py --quick   # Run only quick tests

Exit codes:
    0: All tests passed
    1: One or more tests failed
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

# Test scripts in order of execution (quick tests first)
TEST_SCRIPTS = [
    ("test_custom_lemmas.py", "Custom Lemmas", True),   # quick
    ("test_collation.py", "Collation Data", True),      # quick
    ("test_lemmatization.py", "Lemmatization", False),  # slower
    ("validate_corpus.py", "Corpus Validation", False), # slower
]


def run_test(script_name: str, description: str) -> tuple[bool, float]:
    """Run a test script and return (success, duration)."""
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"  FAIL: {script_name} not found")
        return False, 0.0

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        duration = time.time() - start
        success = result.returncode == 0

        if success:
            print(f"  PASS: {description} ({duration:.1f}s)")
        else:
            print(f"  FAIL: {description} ({duration:.1f}s)")
            # Show last few lines of output on failure
            output = result.stdout + result.stderr
            lines = output.strip().split('\n')
            if len(lines) > 10:
                print("    ...")
            for line in lines[-10:]:
                print(f"    {line}")

        return success, duration

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        print(f"  TIMEOUT: {description} ({duration:.1f}s)")
        return False, duration

    except Exception as e:
        duration = time.time() - start
        print(f"  ERROR: {description} - {e}")
        return False, duration


def run_pytest(quick_only: bool) -> tuple[bool, float]:
    """Run pytest unit tests and return (success, duration)."""
    project_root = SCRIPTS_DIR.parent
    start = time.time()
    try:
        cmd = [sys.executable, "-m", "pytest", str(project_root / "tests"),
               "-m", "not slow", "-q"]
        if not quick_only:
            cmd = [sys.executable, "-m", "pytest", str(project_root / "tests"), "-q"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(project_root),
        )
        duration = time.time() - start
        success = result.returncode == 0

        if success:
            # Show summary line from pytest output
            lines = result.stdout.strip().split('\n')
            summary = lines[-1] if lines else ""
            print(f"  PASS: Unit Tests ({duration:.1f}s) — {summary}")
        else:
            print(f"  FAIL: Unit Tests ({duration:.1f}s)")
            output = result.stdout + result.stderr
            lines = output.strip().split('\n')
            if len(lines) > 10:
                print("    ...")
            for line in lines[-10:]:
                print(f"    {line}")

        return success, duration

    except FileNotFoundError:
        duration = time.time() - start
        print("  SKIP: Unit Tests (pytest not installed)")
        return True, duration  # Don't fail if pytest not available


def main():
    quick_only = "--quick" in sys.argv

    print("=" * 60)
    print("PĀLI CANON TEST RUNNER")
    print("=" * 60)
    print()

    if quick_only:
        print("Running quick tests only (--quick mode)")
        tests = [(s, d, q) for s, d, q in TEST_SCRIPTS if q]
    else:
        print("Running all tests")
        tests = TEST_SCRIPTS

    print()

    passed = 0
    failed = 0
    total_time = 0.0

    # Run pytest unit tests first
    success, duration = run_pytest(quick_only)
    total_time += duration
    if success:
        passed += 1
    else:
        failed += 1

    # Run data validation scripts
    for script_name, description, _is_quick in tests:
        success, duration = run_test(script_name, description)
        total_time += duration
        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {total_time:.1f}s")
    print()

    if failed > 0:
        print("RESULT: FAIL")
        return 1
    else:
        print("RESULT: PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
