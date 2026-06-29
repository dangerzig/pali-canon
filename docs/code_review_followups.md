# Code-review follow-ups (from CODE_REVIEW_A_PLUS.md, 2026-06-29)

Triage of the project-wide review. Findings 4, 5, 7 are **done** on branch
`lemmatizer-quotative-homograph-fix`; the rest are scoped here as separate work.

## Done
- **#4 validate_corpus expects 5 nikāyas** — now validates all 7 collections
  (added Vinaya/Abhidhamma bounds). `scripts/validate_corpus.py` exits 0.
- **#5 lemmatizer cache ignores strategy pipeline** — `lookup_word` now tracks
  the pipeline the cache was built under and drops it on a switch, so legacy and
  enhanced lookups can't contaminate each other. Regression tests added.
- **#7 worktree / docs not release-clean** — plan/audit doc contradiction
  reconciled; scratch audit scripts removed from `src/`. (The `data/vri-raw`
  edits remain a separate, pre-existing question — see #B below.)

## Remaining — proposed as separate issues

### A. (#1) `critical/` output is summary-only — DONE (apparatus); running text remains
- Added `src/build_critical_edition.py`, which assembles a real critical
  apparatus from the collation output: per divergent position it records every
  witness's reading, the selected reading, rejected readings, confidence, type,
  and notes, plus provenance (collation source, DPD validation source, stats,
  build time). Schema in `docs/critical_edition_schema.md` (v1).
- Regenerated all of `data/critical/` (2,622 editions) — e.g. dn1 went from a
  3-field summary to 1,611 apparatus entries. `build_critical_complete.py` is
  marked superseded.
- Tests: `tests/test_critical_edition.py` (assembly, selected/rejected,
  provenance, file writing).
- REMAINING (follow-up): a single reconstructed *running* critical text (base
  token stream with selected readings applied) — a presentation layer on top of
  the apparatus; needs position→base-token mapping.

### B. (#2) DPD validation fails OPEN in collation — HIGH, SMALL/MEDIUM
`collate_nikaya.load_dpd_words()` returns an empty set when
`dpd_headwords.json` / `lemma_lookup.json` are absent, making `is_valid_word()`
return True for everything → bad PTS readings silently pass as valid variants.
- Fail CLOSED (raise) when validation data is missing, or query `dpd.db`
  directly (it is already a dependency).
- Record validation source + version in every collation summary.
- Effort: small-medium. Do this before any new collation runs — it is a silent
  scholarly-correctness risk.

### C. (#3) Search index has no stale-data detection — HIGH, MEDIUM
`SearchIndex.is_built()` only checks a table exists; `search_text()` swallows all
`OperationalError` as "no results".
- Add an `index_meta` table (schema version, code version, source-data hash,
  file/token counts, build timestamp); rebuild atomically on mismatch.
- Only suppress known malformed-query errors; surface index/DB errors.
- Effort: medium.

### D. (#6) Tests not tiered — DONE (markers); golden files remain
- Registered `slow` + `corpus` markers (pytest.ini, conftest); marked the heavy
  export/PDF/index-build tests. Fast tier `pytest -m "not slow and not corpus"`
  now runs ~4s (was ~3.5 min full). Tiers documented in pytest.ini.
- REMAINING (smaller follow-up): golden-file fixtures for representative
  canonical/lemmatized/collation/export outputs to lock formatting.

### E. (#8) Packaging / external-data setup — DONE
- Added `pyproject.toml`: package metadata, `requires-python >=3.10`, runtime dep
  (pyyaml), `analysis` extra (pandas/scipy/numpy), `dev` extra (pytest), src
  layout for the `pali` package, and a `pali-check-data` console script.
- Added `src/pali_check_data.py`: reports which external/generated data
  (dpd.db, sandhi rules, DPPN, canonical, lemmatized) is present/missing and
  exits non-zero if a required resource is absent. README updated.

### B′. `data/vri-raw/*` working-tree edits (20 files) — TRIAGE
Pre-existing modifications unrelated to the lemmatizer fix; never staged here.
Decide whether they are intentional source updates (commit with rationale) or
should be reverted. Owner decision required.

## Suggested order
1. **B** (fail-closed validation) — small, prevents silent bad data.
2. **C** (index staleness) — correctness of search results.
3. **D** (test tiering) — unblocks faster iteration on everything else.
4. **E** (packaging) — reproducibility for fresh clones/CI.
5. **A** (real critical edition) — largest; the headline scholarly deliverable.
6. **B′** — triage the vri-raw edits.
