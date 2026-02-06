# Code Review

## Scope
Reviewed repository structure, documentation, and core library modules under `src/pali`, plus representative pipeline scripts in `src/` and tests in `scripts/`.

## Findings (Ordered by Severity)

- **High:** `Vocabulary.get_vocabulary()` reports `coverage` as 1.0 for any non-empty input because `total_tokens` is computed from `lemma_counts` and `tokens_with_lemma` is set equal to that value. Tokens without lemmas are never counted, so the metric is misleading. `src/pali/vocab.py`.

- **Medium:** `Store.get_sutta()` can return a range item for a specific KN sutta ID (for example, `dhp5` returns the `dhp1-20` item). This may be intentional, but it means callers asking for a specific sutta ID may get a larger collection with a different `Sutta.id` than requested. If consumers assume a one-to-one mapping, this is surprising and can lead to subtle downstream errors. `src/pali/store.py`.

- **Medium:** `list_suttas()` loads every JSON file and parses full contents just to extract metadata and segment counts. On large corpora, this is expensive and memory-heavy (even with the 100-entry JSON cache), and it’s invoked by `get_nikaya_info()`. This can be slow in interactive contexts or when called repeatedly. `src/pali/store.py`.

- **Low:** Search index build is correct but not transactional or batched. For large corpora, building the index is likely slow and can leave a partially built database if interrupted. Consider explicit transactions or `executemany` if performance or durability becomes an issue. `src/pali/index.py`.

- **Low:** There is no top-level `README.md` or installation guide. The docs are rich, but the most obvious entrypoint for new users is missing. `docs/ARCHITECTURE.md` and `docs/methodology.md` are strong, but they are not discoverable without a README. 

- **Low:** The “tests” are scripts in `scripts/` and are run manually, not under a test runner. This is fine for a research pipeline but increases the chance regressions slip in unnoticed. `scripts/test_lemmatization.py`, `scripts/test_custom_lemmas.py`, `scripts/validate_corpus.py`.

## Architecture Notes

- Clear separation between the core library (`src/pali`) and pipeline scripts (`src/*.py`). The API design in `src/pali/__init__.py` is approachable and well-documented.
- Data model is clean and memory-conscious (`slots=True` in `src/pali/models.py`).
- Search and export functionality are organized and mostly orthogonal to the storage layer, which keeps the API usable without requiring the full pipeline.
- Documentation quality is unusually strong for a research codebase. The methodology document ties design choices to scholarly goals, which makes maintenance and review easier.

## Open Questions / Assumptions

- Is the KN range-return behavior in `Store.get_sutta()` intentional for all KN texts, or should `get_sutta("dhp5")` attempt to return just that sutta?
- Is the `coverage` metric intended to mean “percentage of tokens that have lemmas,” or was it only intended to mean “coverage among tokens that are already lemma-annotated”?
- Are you expecting people to install this as a package, or is this strictly a repo-local tool? That affects whether a `pyproject.toml`/`README.md` is expected.

## Residual Risks / Gaps

- No automated test runner; quality depends on manual execution of scripts.
- Performance of index build and repeated metadata listing may become a bottleneck for large-scale usage.
