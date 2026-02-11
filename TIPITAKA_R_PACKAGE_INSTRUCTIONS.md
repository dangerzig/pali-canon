# Tipitaka R Packages — Data Generation

This document explains how to regenerate the data files for the R packages from the pali-canon Python library.

## Overview

There are two R packages:

### tipitaka (existing CRAN package)
Contains VRI original datasets (unchanged from v0.1.x):
- `tipitaka_raw`, `tipitaka_long`, `tipitaka_wide` — VRI Chattha Sangayana data

**Functions**: `pali_sort()`, `pali_lt()`, `pali_gt()`, `pali_eq()`

### tipitaka.critical (new companion package)
Contains the lemmatized critical edition of the complete Tipitaka:
- `texts` — Full surface and lemmatized text per text unit (5,777 units across all three pitakas)
- `lemmas()` — Lemma frequencies by text unit (computed on first use)
- `dtm()` — Lemma x text unit sparse frequency matrix (computed on first use)
- `search_lemma()` — Search for lemma occurrences

**Coverage**: All three pitakas (Sutta, Vinaya, Abhidhamma), 2.8M tokens, 98.0% unique-word coverage.

## Generating Data for tipitaka.critical

### Step 1: Generate texts CSV from Python

```bash
cd ~/pali
PYTHONPATH=src python -c "
from pali import Canon
canon = Canon()
canon.export_tipitaka_texts('../tipitaka.critical/data-raw/texts.csv')
"
```

This generates a single CSV with columns: `id`, `collection`, `pitaka`, `title`, `text`, `text_lemmatized`.

### Step 2: Build R .rda file

```bash
cd ~/tipitaka.critical
Rscript data-raw/build_data.R
```

### Step 3: Check

```bash
Rscript -e 'devtools::document()'
Rscript -e 'devtools::check()'
```

## Generating Data for tipitaka (legacy export)

The full export still works for regenerating all CSV formats:

```bash
cd ~/pali
PYTHONPATH=src python -c "
from pali import Canon
canon = Canon()
canon.export_tipitaka_data('../tipitaka/data-raw/critical/')
"
```

This generates 7 CSV files covering all three pitakas:

| File | Description | Rows |
|------|-------------|------|
| `tipitaka_raw.csv` | Text per collection | 7 |
| `tipitaka_suttas_raw.csv` | Text per text unit | 5,777 |
| `tipitaka_long.csv` | Lemma frequencies by collection | ~100K |
| `tipitaka_long_words.csv` | Surface form frequencies by collection | ~150K |
| `tipitaka_wide.csv` | Lemma frequency matrix by collection | 7 |
| `tipitaka_suttas_long.csv` | Lemma frequencies by text unit | ~8M |
| `tipitaka_suttas_wide.csv` | Lemma frequency matrix by text unit | ~5.8K |

## Key Design Decisions

- **Two packages**: `tipitaka` (minimal VRI data for CRAN) + `tipitaka.critical` (full critical edition)
- **Compute on load**: tipitaka.critical ships only text data; frequency tables and sparse matrix are computed on first use (~5 sec)
- **Five witnesses**: PTS/GRETIL (base text), SuttaCentral, VRI, BJT, Thai Royal Edition
- **Corrections**: Where SC=VRI=BJT disagree with PTS and PTS reading is not in DPD
- **Lemmatization**: DPD-based, 98.0% unique-word coverage across the complete Tipitaka
- **Sparse matrix**: The document-term matrix is 99%+ zeros, stored as `dgCMatrix` from the Matrix package
