# Pāli Canon Python Library — API Reference

## Status

This document describes the Canon API. Features marked with **[IMPLEMENTED]** are working; features marked **[PLANNED]** are not yet built.

## Overview

A Python library for accessing the critical edition data, supporting:
- **[IMPLEMENTED]** Hierarchical navigation (nikaya → sutta → segment)
- **[PLANNED]** Edition selection (PTS, VRI, SC) with optional corrections
- **[IMPLEMENTED]** Lemmatized text with token-level annotations
- **[IMPLEMENTED]** Vocabulary statistics and document-term matrices for analysis
- **[IMPLEMENTED]** Export to pandas DataFrames, CSV, and LaTeX/PDF
- **[IMPLEMENTED]** R package data export (7 CSV files)

## Installation

```bash
# Local development (no pip install needed)
cd ~/pali-canon
PYTHONPATH=src python -c "from pali import Canon; Canon()"
```

## Basic Usage [IMPLEMENTED]

```python
from pali import Canon

# Initialize (loads indexes, not full data)
canon = Canon()

# Get a sutta
sutta = canon.get_sutta("dn1")
sutta = canon.get_sutta("dn1", lemmatized=True)

# Access segments
for segment in sutta.segments:
    print(segment.id, segment.pali)
    if segment.tokens:
        for token in segment.tokens:
            print(f"  {token.word} → {token.lemma} ({token.pos})")

# Get plain text
text = canon.get_text("dn1")

# Get segment range
segments = canon.get_segments("dn1", from_id="dn1:1.1.1", to_id="dn1:1.5.0")

# List available texts
canon.list_nikayas()           # ['dn', 'mn', 'sn', 'an', 'kn', 'vinaya', 'abhidhamma']
canon.list_suttas("dn")        # [SuttaInfo(id='dn1', title='Brahmajālasutta', ...), ...]
```

## Edition Selection [PLANNED]

Not yet implemented. Currently returns SC Mahāsaṅgīti text (canonical) or lemmatized version.

```python
# Future API:
sutta = canon.get_sutta("dn1", edition="pts")
sutta = canon.get_sutta("dn1", edition="critical")
witnesses = canon.get_witnesses("dn1")
```

## Search [IMPLEMENTED]

```python
# Search by lemma
results = canon.search_lemma("dhamma")
print(results.total)
print(results.by_nikaya)       # {'dn': 892, 'mn': 1456, ...}
for occ in results.occurrences[:10]:
    print(occ.segment_id, occ.word, occ.pos)

# Full-text search (SQLite FTS5)
results = canon.search_text("evaṃ me sutaṃ")
for r in results[:10]:
    print(f"{r.segment_id}: {r.snippet}")

# Get all lemmas
all_lemmas = canon.get_all_lemmas()

# [PLANNED] Find by PTS reference
# segment = canon.find_by_pts("D", "i", 1)
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

## Vocabulary & Analysis Export [IMPLEMENTED]

```python
# Document-term matrix (for clustering, topic modeling)
matrix, doc_ids, terms = canon.document_term_matrix("dn")
# Returns: (scipy.sparse.csr_matrix, doc_ids, term_list)

# With options
df = canon.document_term_matrix("dn",
    unit="sutta",           # or "segment"
    terms="lemmas",         # or "words"
    min_df=2,               # minimum document frequency
    as_dataframe=True       # returns pandas DataFrame
)

# Export to CSV
canon.export_dtm("dn", "dn_dtm.csv")
canon.export_vocabulary("dn", "dn_vocab.csv")
```

## R Package Export [IMPLEMENTED]

```python
# Generate all 7 CSV files for tipitaka R package
canon.export_tipitaka_data("../tipitaka/data-raw/critical/")

# Individual exports
canon.export_tipitaka_raw("tipitaka_raw.csv")
canon.export_tipitaka_suttas_raw("tipitaka_suttas_raw.csv")
canon.export_tipitaka_long("tipitaka_long.csv")
canon.export_tipitaka_long("tipitaka_long_words.csv", use_lemmas=False)
canon.export_tipitaka_wide("tipitaka_wide.csv")
```

## Critical Apparatus [PLANNED]

Not yet exposed via the Canon API. Collation data exists in `data/collation/`.

```python
# Future API:
apparatus = canon.get_apparatus("dn1")
for variant in apparatus.variants:
    print(f"{variant.segment_id}: {variant.readings}")
```

## LaTeX/PDF Export [IMPLEMENTED]

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
@dataclass(slots=True)
class Sutta:
    id: str
    title_pali: str | None
    title_eng: str | None
    collection: str | None
    vagga: str | None
    pts: str | None
    segments: list[Segment]

@dataclass(slots=True)
class Segment:
    id: str
    pali: str
    tokens: list[Token] | None

@dataclass(slots=True)
class Token:
    word: str
    lemma: str | None
    pos: str | None
    root: str | None
    sandhi: list[str] | None
    components: list[dict] | None
```

## Architecture

### Module Structure
```
src/pali/
├── __init__.py          # Public API (Canon class)
├── models.py            # Data classes (Sutta, Segment, Token, etc.)
├── store.py             # JSON file access layer
├── text.py              # Text utilities (tokenization, normalization)
├── search.py            # Lemma/text search
├── index.py             # SQLite indexes for search
├── vocab.py             # Vocabulary statistics & R package export
├── export.py            # LaTeX/PDF export
├── custom_lemmas.py     # Custom lemma lookups
└── custom_lemmas.yaml   # Custom lemma mappings
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

## Implementation Status

### Phase 1: Python Core Library — COMPLETE
- `Canon` class with basic navigation
- `get_sutta()`, `get_text()`, `list_nikayas()`, `list_suttas()`
- Lemmatized text access with token-level analysis

### Phase 2: Python Search — COMPLETE
- SQLite FTS5 index for full-text search
- `search_lemma()`, `search_text()`, `get_all_lemmas()`
- PTS reference lookup: NOT YET IMPLEMENTED

### Phase 3: Python Analysis Export — COMPLETE
- `get_vocabulary()` with DataFrame support
- `document_term_matrix()` with sparse matrix output
- R package CSV export (`export_tipitaka_data()`)

### Phase 4: Python Print Export — COMPLETE
- `to_latex()`, `export_latex()`, `export_pdf()`

### Phase 5: R Package Update — COMPLETE
- tipitaka v1.0.0 submitted to CRAN (Feb 2026)
- 7 new critical edition datasets + `search_lemma()` function
- Backwards compatible with v0.1.x

### Future Work
- Edition selection (PTS, VRI, SC, critical) via `get_sutta()` parameter
- Critical apparatus API (`get_apparatus()`, `get_witnesses()`)
- PTS reference lookup (`find_by_pts()`)
- TF-IDF weighting in document-term matrix
- PyPI package publication

## R Package: tipitaka v1.0.0 — COMPLETE

The [tipitaka R package](https://github.com/dangerzig/tipitaka) was updated to v1.0.0 and submitted to CRAN (Feb 2026).

### Datasets

**Preserved from v0.1.x:**
- `tipitaka_raw`, `tipitaka_long`, `tipitaka_wide` — VRI data
- `tipitaka_names`, `sutta_pitaka`, `vinaya_pitaka`, `abhidhamma_pitaka`
- `pali_alphabet`, `pali_stop_words`

**New in v1.0.0 (from critical edition):**
- `tipitaka_raw_critical` — Text per nikaya
- `tipitaka_suttas_raw` — Text per sutta (5,777 rows)
- `tipitaka_long_critical` — Lemma frequencies by nikaya
- `tipitaka_long_words` — Surface form frequencies by nikaya
- `tipitaka_wide_critical` — Lemma x nikaya frequency matrix
- `tipitaka_suttas_long` — Lemma frequencies by sutta
- `tipitaka_suttas_wide` — Sparse dgCMatrix (sutta x lemma)

**Removed:** `sati_sutta_long`, `sati_sutta_raw` (replaced by critical edition extraction)

### Functions
- `pali_lt()`, `pali_gt()`, `pali_eq()`, `pali_sort()` — Pali string operations (C++)
- `search_lemma()` — Search for lemma occurrences across suttas

### Data Generation

```bash
# Step 1: Generate CSVs from Python
cd ~/pali-canon && PYTHONPATH=src python -c "
from pali import Canon
Canon().export_tipitaka_data('../tipitaka/data-raw/critical/')
"

# Step 2: Build .rda files
cd ~/tipitaka && Rscript data-raw/critical.R
```

See [TIPITAKA_R_PACKAGE_INSTRUCTIONS.md](../TIPITAKA_R_PACKAGE_INSTRUCTIONS.md) for full details.

## Verification

```python
from pali import Canon
canon = Canon()

# Basic access
sutta = canon.get_sutta("dn1")
print(sutta.title_pali)

# Lemmatized access
sutta = canon.get_sutta("dn1", lemmatized=True)
print(sutta.segments[0].tokens[:3])

# Search
results = canon.search_lemma("buddha")
print(results.total)

# R package export
canon.export_tipitaka_data("/tmp/test_export/")
```
