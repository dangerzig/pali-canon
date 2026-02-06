# Code Review: Pali Canon Critical Edition Project

**Reviewer:** Claude
**Date:** February 5, 2026
**Codebase:** ~/pali

---

## Executive Summary

This is a well-engineered academic software project for creating a digital critical edition of the Pali Tipitaka. The codebase demonstrates strong domain expertise, clean architecture, and thoughtful design decisions. Overall code quality is **high**, with a few areas that could benefit from improvement.

**Overall Grade: B+**

---

## 1. Architecture & Design

### Strengths

**Clean Separation of Concerns**
The project follows a clear pipeline architecture:
- Parsing layer (`parse_*.py`) - extracts text from sources
- Building layer (`build_*.py`) - creates critical editions
- Lemmatization layer (`lemmatize_canon.py`) - adds morphological analysis
- API layer (`src/pali/`) - provides clean public interface

**Minimal Dependencies**
The decision to rely only on Python's standard library is excellent for:
- Long-term maintainability
- Easy installation for researchers
- Avoiding dependency conflicts

**Well-Designed Data Models** (`src/pali/models.py:7-117`)
The dataclass-based models are clean and appropriate:
```python
@dataclass
class Token:
    word: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    # ...
```

### Concerns

**Large Monolithic Functions**
`lemmatize_canon.py` is 983 lines with the `Lemmatizer` class spanning ~640 lines. The `lookup_word()` method (lines 485-761) is particularly long at ~275 lines. Consider extracting into smaller, focused methods.

**Duplicated Code Patterns**
The `build_critical_complete.py` file has repeated patterns for each nikaya:
- `build_dn_critical()` (lines 140-203)
- `build_mn_critical()` (lines 208-271)
- `build_sn_critical()` (lines 276-359)

These share ~80% of their logic and could be consolidated.

---

## 2. Code Quality

### Excellent Practices

**Comprehensive Docstrings**
The public API in `src/pali/__init__.py` has excellent documentation:
```python
def search_lemma(
    self,
    lemma: str,
    nikaya: Optional[str] = None,
    limit: int = 1000,
) -> LemmaSearchResult:
    """Search for all occurrences of a lemma.

    Searches the lemmatized corpus for all forms of a dictionary headword.
    On first call, builds a search index (takes a few minutes).

    Args:
        lemma: The lemma (dictionary form) to search for
        nikaya: Optional filter by nikaya (dn, mn, sn, an, kn)
        limit: Maximum occurrences to return (default 1000)
    ...
```

**Defensive Programming**
Good null-checking throughout:
```python
def has_useful_data(r):
    return r and (r['headwords'] or r['deconstructor'])
```

**Consistent Error Handling**
JSON parsing is wrapped properly:
```python
try:
    headword_ids = json.loads(row['headwords'])
except (json.JSONDecodeError, TypeError):
    pass
```

### Areas for Improvement

**Magic Numbers** (`lemmatize_canon.py:419`)
```python
MIN_PART_LEN = 4  # Good - named constant
# But then later:
if len(word) > 15:  # Line 726 - why 15?
```
Suggest extracting `15` to a named constant like `MIN_COMPOUND_LENGTH = 15`.

**Inconsistent Return Types** (`store.py:92-131`)
`_find_sutta_file()` returns `Optional[Path]` but some code paths might not explicitly return `None`:
```python
def _find_sutta_file(self, nikaya: str, sutta_id: str, lemmatized: bool) -> Optional[Path]:
    # ...
    elif nikaya == "kn":
        for f in data_dir.glob("*.json"):
            if sutta_id.startswith(f.stem):
                return f
    # No explicit return None here - relies on implicit None
    return None  # This line exists, good
```

**Hardcoded Path Assumptions** (`lemmatize_canon.py:21-25`)
```python
DATA_DIR = Path(__file__).parent.parent / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
DPD_DB = DATA_DIR / "dpd/dpd.db"
DPPN_FILE = DATA_DIR / "dppn/proper_names.json"
```
Consider making these configurable via environment variables or config file for flexibility.

---

## 3. Performance Considerations

### Good Practices

**LRU Caching** (`store.py:54-58`)
```python
@lru_cache(maxsize=100)
def _load_json(self, path: Path) -> dict:
    """Load and cache JSON file."""
```

**In-Memory Cache for Lookups** (`lemmatize_canon.py:160`)
```python
self.cache = {}  # word -> TokenInfo
```

### Potential Improvements

**Database Connection Management** (`lemmatize_canon.py:157-159`)
```python
def __init__(self, db_path: Path = DPD_DB, dppn_path: Path = DPPN_FILE):
    self.conn = sqlite3.connect(db_path)
```
The connection is opened but only closed if `close()` is explicitly called. Consider using a context manager pattern:
```python
def __enter__(self):
    return self

def __exit__(self, *args):
    self.conn.close()
```

**Repeated Regex Compilation**
In `build_critical_complete.py:36-41`:
```python
def tokenize(text):
    if not text:
        return []
    return re.findall(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+', text.lower())
```
This compiles the regex on every call. Pre-compile for better performance:
```python
PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷA-ZĀĪŪṬḌṆṄÑṂḶ]+')

def tokenize(text):
    if not text:
        return []
    return PALI_WORD_PATTERN.findall(text.lower())
```

---

## 4. Testing

### Current State

The project has a test suite in `scripts/` but it's more of a validation suite than unit tests:
- `validate_corpus.py` - integration tests
- `test_lemmatization.py` - sample-based testing
- `test_custom_lemmas.py` - consistency checks

### Recommendations

**Add Unit Tests**
Consider adding pytest-based unit tests for:
- `Store._find_sutta_file()` with edge cases
- `Lemmatizer` normalization methods
- `Segment.from_dict()` / `Sutta.from_dict()`

**Add Property-Based Testing**
For Pali text processing, property-based testing (hypothesis) would be valuable:
```python
from hypothesis import given, strategies as st

@given(st.text(alphabet="aāiīuūṭḍṇṅñṃḷ"))
def test_tokenize_roundtrip(text):
    tokens = tokenize(text)
    # Properties to verify...
```

---

## 5. Specific Code Issues

### Issue 1: Potential Bug in Range Matching
**File:** `store.py:60-90`

```python
def _id_in_range(self, sutta_id: str, range_id: str) -> bool:
    """Check if sutta_id falls within a range like 'dhp1-20'."""
    match = re.match(r"([a-z]+)(\d+)$", sutta_id)
    if not match:
        return False
```

This doesn't handle IDs with dots like `sn1.1` or `an1.1.1`. The regex expects IDs ending in just digits.

### Issue 2: Unused Import
**File:** `lemmatize_canon.py:18`

```python
from dataclasses import dataclass, asdict
```
`asdict` is imported but never used.

### Issue 3: Inconsistent Logging
**File:** `build_critical_complete.py:27-33`

Uses custom `log()` function that writes to file and stdout. Other scripts use `print()`. Consider using Python's `logging` module consistently.

### Issue 4: Missing Type Annotations
**File:** `build_critical_complete.py`

Most functions lack type annotations, unlike the library code in `src/pali/`:
```python
def build_dn_critical():  # No return type hint
    """Build DN critical edition with 3 witnesses."""
```

Compare to the well-typed library:
```python
def get_sutta(
    self,
    sutta_id: str,
    lemmatized: bool = False,
    include_tokens: bool = True,
) -> Optional[Sutta]:
```

---

## 6. Documentation

### Strengths

- Excellent inline documentation in `src/pali/__init__.py`
- Clear docstrings on public methods
- Well-organized `custom_lemmas.py` with category explanations

### Suggestions

**Add Module-Level Docstrings**
`store.py` starts with a brief docstring but could explain the caching strategy and file layout assumptions.

**API Examples**
The docstrings include good examples but a standalone `examples/` directory with runnable scripts would help new users.

---

## 7. Security Considerations

### No Issues Found

The code:
- Doesn't accept user input from external sources
- Uses parameterized SQL queries (`sqlite3`)
- Doesn't execute shell commands
- Handles file paths safely with `pathlib`

---

## 8. Specific Recommendations

### High Priority

1. **Refactor `lookup_word()` in `lemmatize_canon.py`**
   - Extract each lookup strategy into its own method
   - Create a `LookupStrategy` interface/protocol
   - Chain strategies together

2. **Consolidate Critical Edition Builders**
   ```python
   def build_critical(nikaya: str, config: NikayaConfig) -> Summary:
       """Generic critical edition builder."""
   ```

3. **Add Context Manager to Lemmatizer**
   ```python
   with Lemmatizer() as lem:
       lem.lemmatize_segment(segment)
   ```

### Medium Priority

4. **Pre-compile all regex patterns**
   Move to module-level constants

5. **Add typing to pipeline scripts**
   Match the quality of the library code

6. **Replace print() with logging module**

### Low Priority

7. **Consider async for file I/O**
   When processing many files, could benefit from `asyncio` + `aiofiles`

8. **Add `__slots__` to dataclasses**
   For memory efficiency with large corpora:
   ```python
   @dataclass(slots=True)
   class Token:
   ```

---

## 9. Praise-Worthy Code

### The Custom Lemmas System (`custom_lemmas.py`)

Exceptionally well-organized with clear categories:
```python
# =============================================================================
# POTENTIAL DPD ADDITIONS
# =============================================================================
# These are legitimate Pāli words/forms that appear to be missing from DPD.
```

This thoughtful organization makes it easy to:
- Identify contributions to upstream DPD
- Distinguish metrical variants from true errors
- Maintain project-specific handling separately

### The Store Pattern (`store.py`)

Clean abstraction over the varied JSON formats:
- Handles DN/MN (flat), SN/AN (nested), KN (items)
- Transparent caching
- Good separation between file location and data parsing

---

## 10. Summary of Action Items

| Priority | Item | File(s) |
|----------|------|---------|
| High | Refactor `lookup_word()` to smaller methods | `lemmatize_canon.py` |
| High | Consolidate nikaya builders | `build_critical_complete.py` |
| High | Add context manager to Lemmatizer | `lemmatize_canon.py` |
| Medium | Pre-compile regex patterns | Multiple files |
| Medium | Add type annotations to scripts | `src/*.py` |
| Medium | Use logging module | All pipeline scripts |
| Low | Add `__slots__` to dataclasses | `models.py` |
| Low | Remove unused `asdict` import | `lemmatize_canon.py` |

---

## Conclusion

This is a mature, well-designed project that reflects deep domain expertise in both Pali studies and software engineering. The core library (`src/pali/`) is particularly well-crafted with excellent documentation and clean APIs.

The main areas for improvement are:
1. Breaking down large functions into smaller units
2. Reducing code duplication in pipeline scripts
3. Standardizing on logging and typing conventions

The project successfully achieves its goal of creating a research-ready digital critical edition, and the 99.77% lemmatization coverage is an impressive technical achievement.

---

*End of Code Review*
