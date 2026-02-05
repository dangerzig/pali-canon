# Pāli Canon Python Library Plan

## Overview

A Python library for accessing the critical edition data, supporting:
- Hierarchical navigation (pitaka → nikaya → vagga → sutta → segment)
- Edition selection (PTS, VRI, SC) with optional corrections
- Lemmatized text with token-level annotations
- Vocabulary statistics and document-term matrices for analysis
- Export to pandas DataFrames, numpy arrays, CSV, and LaTeX/PDF

## Installation

```bash
pip install pali-canon  # future PyPI package
# or
pip install -e .        # local development
```

## Basic Usage

```python
from pali import Canon

# Initialize (loads indexes, not full data)
canon = Canon()

# Get a sutta
sutta = canon.get_sutta("dn1")
sutta = canon.get_sutta("dn1", edition="pts", lemmatized=True)
sutta = canon.get_sutta("dn1", edition="critical", corrections=True)

# Access segments
for segment in sutta.segments:
    print(segment.id, segment.pali)
    if segment.tokens:
        for token in segment.tokens:
            print(f"  {token.word} → {token.lemma} ({token.pos})")

# Get segment range
segments = canon.get_segments("dn1", from_id="dn1:1.1.1", to_id="dn1:1.5.0")

# List available texts
canon.list_nikayas()           # ['dn', 'mn', 'sn', 'an', 'kn']
canon.list_suttas("dn")        # [SuttaInfo(id='dn1', title='Brahmajālasutta', ...), ...]
```

## Edition Selection

```python
# SuttaCentral Mahāsaṅgīti edition
sutta = canon.get_sutta("dn1", edition="sc")

# PTS edition (via GRETIL)
sutta = canon.get_sutta("dn1", edition="pts")

# VRI Chaṭṭha Saṅgāyana
sutta = canon.get_sutta("dn1", edition="vri")

# Critical edition (PTS with corrections applied)
sutta = canon.get_sutta("dn1", edition="critical")

# Get all witnesses for comparison
witnesses = canon.get_witnesses("dn1")
# {'sc': 'Evaṃ me sutaṃ...', 'pts': 'Evam me sutaṃ...', 'vri': 'Evaṃ me sutaṃ...'}
```

## Search

```python
# Search by lemma
results = canon.search_lemma("dhamma")
print(results.total)           # 4523
print(results.by_nikaya)       # {'dn': 892, 'mn': 1456, ...}
for occ in results.occurrences[:10]:
    print(occ.segment_id, occ.word_form, occ.context)

# Search by text
results = canon.search_text("evaṃ me sutaṃ")

# Find by PTS reference
segment = canon.find_by_pts("D", "i", 1)  # D i 1
```

## Vocabulary & Statistics

```python
# Vocabulary for a sutta
vocab = canon.get_vocabulary("dn1")
print(vocab.unique_lemmas)     # 1456
print(vocab.coverage)          # 0.977
print(vocab.top_lemmas[:10])   # [('bhagavant', 89), ('bhikkhu', 67), ...]

# Vocabulary for entire nikaya
vocab = canon.get_vocabulary("dn")

# As pandas DataFrame
df = canon.get_vocabulary("dn1", as_dataframe=True)
# columns: lemma, count, pos, forms
```

## Analysis Export

```python
# Document-term matrix (for clustering, topic modeling)
dtm = canon.document_term_matrix("dn")
# Returns: scipy.sparse matrix or pandas DataFrame

dtm = canon.document_term_matrix("dn",
    unit="sutta",           # or "segment"
    terms="lemmas",         # or "words"
    min_df=2,               # minimum document frequency
    as_dataframe=True
)

# TF-IDF weighted
tfidf = canon.document_term_matrix("dn", weighting="tfidf")

# Export to CSV for R
canon.export_dtm("dn", "dn_dtm.csv", format="csv")
canon.export_vocabulary("dn", "dn_vocab.csv")

# Export lemma frequencies per sutta
canon.export_lemma_counts("dn", "dn_lemma_counts.csv")
```

## Critical Apparatus

```python
# Get variants for a sutta
apparatus = canon.get_apparatus("dn1")
for variant in apparatus.variants:
    print(f"{variant.segment_id}: {variant.readings}")
    print(f"  Type: {variant.type}, Preferred: {variant.preferred}")

# Filter by type
errors = [v for v in apparatus.variants if v.type == "error"]
substantive = [v for v in apparatus.variants if v.type == "variant"]
```

## Print/Typeset Export

```python
# Generate LaTeX
latex = canon.to_latex("dn1")
latex = canon.to_latex(["dn1", "dn2"], title="Selected Suttas")

# Save LaTeX file
canon.export_latex("dn1", "dn1.tex")

# Generate PDF (requires XeLaTeX)
canon.export_pdf("dn1", "dn1.pdf")
canon.export_pdf("dn", "digha_nikaya.pdf", title="Dīgha Nikāya")
```

## Data Classes

```python
@dataclass
class Sutta:
    id: str
    title_pali: str
    title_eng: str
    collection: str
    vagga: str
    pts: str
    segments: list[Segment]

@dataclass
class Segment:
    id: str
    pali: str
    pts: str | None
    tokens: list[Token] | None

@dataclass
class Token:
    word: str
    lemma: str | None
    pos: str | None
    root: str | None
    sandhi: list[str] | None
```

## Architecture

### Module Structure
```
src/pali/
├── __init__.py          # Public API (Canon class)
├── canon.py             # Main Canon class
├── models.py            # Data classes (Sutta, Segment, Token, etc.)
├── store.py             # JSON file access layer
├── search.py            # Lemma/text search
├── vocab.py             # Vocabulary statistics
├── export.py            # CSV, LaTeX, PDF export
└── index.py             # SQLite indexes for search
```

### Data Access
- JSON files loaded on demand from `data/canonical/`, `data/lemmatized/`
- LRU cache for recently accessed suttas
- SQLite index built on first search (cached in `data/index.db`)

### Dependencies
- **Required**: Standard library only for core functionality
- **Optional**:
  - `pandas` for DataFrame export
  - `scipy` for sparse matrices
  - `numpy` for numerical operations

## Implementation Phases

### Phase 1: Python Core Library
1. `Canon` class with basic navigation
2. `get_sutta()`, `list_nikayas()`, `list_suttas()`
3. Edition selection (sc, pts, vri, critical)
4. Lemmatized text access

### Phase 2: Python Search
1. SQLite index for lemma occurrences
2. `search_lemma()`, `search_text()`
3. PTS reference lookup

### Phase 3: Python Analysis Export
1. `get_vocabulary()` with DataFrame support
2. `document_term_matrix()`
3. CSV/RDS export for R

### Phase 4: Python Print Export
1. Integrate existing `typeset_critical.py`
2. `to_latex()`, `export_pdf()`

### Phase 5: R Package Update
1. Fork existing tipitaka package
2. Generate new data frames from Python
3. Add new API functions
4. Update documentation and vignettes
5. Submit to CRAN

## R Package: tipitaka v2

Adapt the existing [tipitaka R package](https://github.com/dangerzig/tipitaka) to use the new critical edition data while preserving backwards compatibility.

### Existing API (preserve)

```r
library(tipitaka)

# Data frames (existing)
tipitaka_raw      # Complete text, one row per volume
tipitaka_long     # word, n, total, freq, book
tipitaka_wide     # Word frequencies matrix (books × words)
tipitaka_names    # Book names
sutta_pitaka      # Sutta book names
vinaya_pitaka     # Vinaya book names
abhidhamma_pitaka # Abhidhamma book names
pali_alphabet     # Pali alphabet in order
pali_stop_words   # Stop words

# Functions (existing)
pali_lt(word1, word2)   # Less-than comparison
pali_gt(word1, word2)   # Greater-than comparison
pali_eq(word1, word2)   # Equality comparison
pali_sort(word_list)    # Sort by Pali alphabet
```

### New API (add)

```r
# Edition selection (default: critical)
tipitaka_raw_pts      # PTS edition text
tipitaka_raw_vri      # VRI edition text (= current tipitaka_raw)
tipitaka_raw_sc       # SuttaCentral edition text
tipitaka_raw_critical # Corrected PTS text

# Lemmatized data (NEW)
tipitaka_lemmas       # lemma, word, n, total, freq, book, pos
tipitaka_lemmas_wide  # Lemma frequencies matrix (books × lemmas)

# Finer granularity (NEW)
tipitaka_suttas       # One row per sutta (not just per volume)
tipitaka_suttas_long  # word, n, sutta, nikaya
tipitaka_suttas_wide  # Word frequencies (suttas × words)

# Critical apparatus (NEW)
tipitaka_variants     # segment_id, pts, vri, sc, type, preferred

# Helper functions (NEW)
get_sutta(id, edition = "critical", lemmatized = FALSE)
get_nikaya(nikaya, edition = "critical")
search_lemma(lemma)   # Find all occurrences
```

### Example: Clustering with Lemmas

```r
library(tipitaka)

# Old way (surface forms, VRI only)
dist_m <- dist(tipitaka_wide)
cluster <- hclust(dist_m)
plot(cluster)

# New way (lemmas, critical edition, sutta-level)
dist_m <- dist(tipitaka_suttas_wide)  # More granular
cluster <- hclust(dist_m)
plot(cluster)

# Or with lemmas for better clustering
dist_m <- dist(tipitaka_lemmas_wide)
cluster <- hclust(dist_m)
plot(cluster)
```

### Data Generation

The R package data will be generated from the Python library:

```python
# Python script to generate R package data
from pali import Canon

canon = Canon()

# Generate tipitaka_long equivalent
canon.export_long("tipitaka_long.rds", format="rds")

# Generate lemmatized version
canon.export_long("tipitaka_lemmas.rds", format="rds", lemmatized=True)

# Generate sutta-level data
canon.export_suttas_long("tipitaka_suttas_long.rds")

# Generate wide matrices
canon.export_wide("tipitaka_wide.rds")
canon.export_wide("tipitaka_lemmas_wide.rds", lemmatized=True)
```

### Implementation Approach

1. **Keep existing data as-is** for backwards compatibility
2. **Add new data frames** with `_lemmas`, `_suttas`, `_pts`, `_vri`, `_sc` suffixes
3. **Add new functions** for edition selection and lemma search
4. **Generate data from Python** during package build (not runtime)
5. **Update vignettes** to show new clustering workflows

## Verification

1. Install: `pip install -e .`
2. Test basic access:
   ```python
   from pali import Canon
   canon = Canon()
   sutta = canon.get_sutta("dn1")
   print(sutta.title_pali)
   ```
3. Test lemmatized access:
   ```python
   sutta = canon.get_sutta("dn1", lemmatized=True)
   print(sutta.segments[0].tokens)
   ```
4. Test search:
   ```python
   results = canon.search_lemma("buddha")
   print(results.total)
   ```
5. Test export:
   ```python
   canon.export_dtm("dn", "test_dtm.csv")
   ```
