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

### A. (#1) `critical/` output is summary-only, not a real apparatus — HIGH, LARGE
`build_critical_complete.py` emits `id`/`witnesses`/`word_count`, not selected
readings + apparatus. The real collation lives under `data/collation/` but is
not assembled into the named critical edition.
- Define a critical-edition JSON schema: selected reading, rejected readings,
  witness support, confidence, apparatus notes, provenance.
- Build it from canonical text + collation output; add an end-to-end test from
  witnesses to edition.
- Effort: large (new schema + builder + tests). Highest scholarly value.

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

### D. (#6) Tests not tiered (full suite ~7–9 min, corpus-coupled) — MEDIUM
- Add small deterministic fixtures for unit tests; mark full-corpus tests
  `slow`/`corpus`; run fast tests per-change, corpus acceptance on release.
- Add golden-file tests for canonical/lemmatized/collation/export samples.
- Effort: medium; big developer-velocity payoff.

### E. (#8) Packaging / external-data setup not reproducible — MEDIUM
- Add `pyproject.toml` (metadata, Python version, runtime deps, optional
  `analysis` extras for pandas/scipy, dev/test deps).
- Add a bootstrap/validation command that reports exactly which external data
  (DPD, DPPN, sandhi rules) is missing.
- Effort: medium.

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
