# Code Review (Follow-Up)

## Scope
Focused on updated code changes in:
- `src/lemmatize_canon.py`
- `src/pali/custom_lemmas.py`
- `src/pali/models.py`
- `src/parse_gretil_sn.py`

Data and generated artifacts were not reviewed.

## What Changed (High-Level)
- Lemmatizer lookup pipeline refactored into strategy classes with a configurable ordered list.
- Custom lemma mappings moved from Python dicts to `custom_lemmas.yaml` with YAML loading and reload support.
- `dataclasses` now use `slots=True` for memory reductions.
- GRETIL SN parser now supports multiple reference formats in Vol 1 and optional numeric suffixes in Vol 2+.

## Findings (Ordered by Severity)

- **High:** `custom_lemmas.py` now depends on `PyYAML` (`import yaml`) but the repository still advertises “standard library only” and `requirements.txt` does not include `PyYAML`. This will cause runtime import errors for users who did not install it. Consider adding `PyYAML` as an optional dependency and documenting it, or implement a fallback. `src/pali/custom_lemmas.py`, `requirements.txt`.

- **Medium:** YAML config is loaded at import time with no error handling. If `custom_lemmas.yaml` is missing from packaging or a bad edit occurs, import will fail and the whole library becomes unusable. Consider catching `FileNotFoundError` and YAML parse errors and failing with a clearer message or a safe empty config. `src/pali/custom_lemmas.py`.

- **Low:** `DEFAULT_STRATEGIES` uses instantiated objects at module load. This is fine while strategies are stateless (they appear to be), but it makes it easy to accidentally add state later and create cross-request leakage. You may want to document that strategies must remain stateless, or build them per `Lemmatizer` instance. `src/lemmatize_canon.py`.

- **Low:** If `custom_lemmas.yaml` and `py.typed` are intended to be part of the distribution, they must be tracked and included in packaging metadata (not visible here). They appear as untracked in this workspace. If omitted, runtime will fail or type information won’t be discoverable. `src/pali/custom_lemmas.yaml`, `src/pali/py.typed`.

## Resolved / Improved Since Prior Review
- Lemmatizer lookup flow is now much clearer and easier to extend. The strategy pipeline isolates responsibilities and makes stats attribution explicit.
- GRETIL SN parsing is more robust to the mixed reference formats found in the raw source.
- `slots=True` reduces memory overhead for large-scale token processing.

## Previously Reported Issues Still Present (Not Modified)
- `Vocabulary.get_vocabulary()` computes `coverage` from lemma counts only, so coverage is always 1.0 when any tokens are counted. This is still misleading and should be recalculated using total token count, not only tokens with lemmas. `src/pali/vocab.py`.
- `Store.get_sutta()` may return a KN range item (e.g., `dhp1-20`) when asked for a specific sutta ID like `dhp5`. If this is intentional, it should be documented; if not, it should be corrected. `src/pali/store.py`.
- There is still no top-level `README.md`, which makes discovery and onboarding harder despite strong docs in `docs/`. 

## Open Questions / Assumptions
- Is the strategy pipeline expected to be user-configurable (custom ordering or custom strategies)? If yes, you may want to expose a public API rather than passing a list into `lookup_word()`.
- Should YAML edits be considered “safe” for non-developer users? If yes, a schema check or validation helper would reduce breakages.

## Residual Risks / Gaps
- Dependency mismatch (PyYAML) may cause production failures for users expecting standard-library-only installs.
- Packaging may omit runtime YAML assets unless explicitly included.

