# Code-review follow-ups

Status of the project-wide review (`CODE_REVIEW_A_PLUS.md`, 2026-06-29) and the
fix-verification pass (`CODE_REVIEW_FIX_VERIFICATION_2026-06-29.md`). Both report
files are gitignored; this curated list is the tracked record.

## Original findings 1–8 — all addressed

- **#1 critical/ was summary-only** — `src/build_critical_edition.py` builds a
  real apparatus (selected/rejected readings, witness support, confidence, type,
  notes, provenance) from collation. Schema: `docs/critical_edition_schema.md`.
  `data/critical/` regenerated (2,622 schema-valid editions + a summary);
  3,303 stale summary-only files (texts never collated) were removed, so the
  tree is now uniform. `build_critical_complete.py` marked superseded.
- **#2 DPD validation failed open** — `collate_nikaya.load_dpd_words()` fails
  CLOSED (tries json → lemma_lookup → `dpd.db`, else raises). The legacy
  `collate_variants.py` now delegates to it (was independently fail-open), and
  `run_full_pipeline.py` uses the apparatus builder.
- **#3 search index could go stale** — `index_meta` table + fingerprint
  (path + size + mtime, so same-size edits are caught); atomic build; narrowed
  error handling (re-raises index/DB errors).
- **#4 validate_corpus** — validates all 7 collections; exits 0.
- **#5 lemmatizer cache** — pipeline-aware; no legacy/enhanced contamination.
- **#6 test tiers** — `slow`/`corpus` markers; fast tier ~4s.
- **#7 release hygiene** — plan/audit reconciled; scratch scripts removed;
  code-review report files gitignored.
- **#8 packaging** — `pyproject.toml` + `pali-check-data` command.

## Verification-pass items — addressed

- Mixed-schema `data/critical/` → cleaned (uniform schema; stale files removed).
- `collate_variants.py` fail-open → delegates to the fail-closed loader.
- `run_full_pipeline.py` → uses `build_critical_edition`, not the summary builder.
- Docs (README, ARCHITECTURE) → point at `build_critical_edition.py`.
- Index fingerprint → now path + size + mtime (catches same-size edits).
- `scripts/release_check.py` → runs compile, validator, data check, and a
  critical-schema guard.

## Genuinely remaining (smaller follow-ups)

- **Running critical text** — a single reconstructed text (base token stream
  with selected readings applied) on top of the apparatus; needs
  position→base-token mapping.
- **Golden-file fixtures** — lock formatting of representative canonical /
  lemmatized / collation / critical / export outputs.
- **Legacy builders** — `build_critical.py` / `build_critical_complete.py` are
  marked superseded but still present; archive or remove once nothing references
  them.
- **CI / lockfile** — no CI config or pinned lockfile yet.
- **`data/vri-raw/*` (20 files)** — pre-existing working-tree edits, never
  staged; owner to decide commit vs revert.
- **Downstream re-verification of the lemmatizer fix** — regenerate
  `data/lemmatized/` and re-check the register-paper / `pali-strata` numbers.
