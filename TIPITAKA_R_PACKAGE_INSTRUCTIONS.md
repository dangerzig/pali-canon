# Tipitaka R Package — Data Generation

This document explains how to regenerate the data files for the [tipitaka R package](https://github.com/dangerzig/tipitaka) from the pali-canon Python library.

## Overview

The tipitaka R package (v1.0.0, submitted to CRAN Feb 2026) contains:

**VRI original datasets** (unchanged from v0.1.x):
- `tipitaka_raw`, `tipitaka_long`, `tipitaka_wide` — VRI Chattha Sangayana data

**Critical edition datasets** (new in v1.0.0):
- `tipitaka_raw_critical` — Full text per nikaya
- `tipitaka_suttas_raw` — Full text per sutta (5,764 suttas)
- `tipitaka_long_critical` — Lemma frequencies by nikaya
- `tipitaka_long_words` — Surface form frequencies by nikaya
- `tipitaka_wide_critical` — Lemma x nikaya frequency matrix
- `tipitaka_suttas_long` — Lemma frequencies by sutta
- `tipitaka_suttas_wide` — Lemma x sutta sparse matrix (dgCMatrix)

**Functions**: `pali_sort()`, `pali_lt()`, `pali_gt()`, `pali_eq()`, `search_lemma()`

## Step 1: Generate CSV files from Python

```bash
cd ~/pali
PYTHONPATH=src python -c "
from pali import Canon
canon = Canon()
canon.export_tipitaka_data('../tipitaka/data-raw/critical/')
"
```

This generates 7 CSV files in `../tipitaka/data-raw/critical/`:

| File | Description | Rows |
|------|-------------|------|
| `tipitaka_raw.csv` | Text per nikaya | 5 |
| `tipitaka_suttas_raw.csv` | Text per sutta | 5,764 |
| `tipitaka_long.csv` | Lemma frequencies by nikaya | ~70K |
| `tipitaka_long_words.csv` | Surface form frequencies by nikaya | ~105K |
| `tipitaka_wide.csv` | Lemma frequency matrix by nikaya | 5 |
| `tipitaka_suttas_long.csv` | Lemma frequencies by sutta | ~5M |
| `tipitaka_suttas_wide.csv` | Lemma frequency matrix by sutta | ~5.7K |

## Step 2: Build R .rda files

```bash
cd ~/tipitaka
Rscript data-raw/critical.R
```

This reads the CSVs and creates compressed `.rda` files in `data/`. Note that `tipitaka_suttas_wide` is built as a sparse `dgCMatrix` from `tipitaka_suttas_long` (not from the wide CSV) to reduce size from 815MB to 1.3MB.

## Step 3: Regenerate docs and check

```bash
cd ~/tipitaka
Rscript -e 'devtools::document()'
Rscript -e 'devtools::check()'
```

Should pass with 0 errors, 0 warnings, 0 notes (or only a size NOTE).

## Step 4: Knit README

```bash
Rscript -e 'devtools::install()'  # new datasets must be loadable
Rscript -e 'rmarkdown::render("README.Rmd")'
```

## Key Design Decisions

- **Sparse matrix**: `tipitaka_suttas_wide` is 99.3% zeros, stored as `dgCMatrix` from the Matrix package (in Depends, not Imports, for LazyData S4 compatibility)
- **Backward compatibility**: All VRI datasets preserved unchanged; `sati_sutta_long` and `sati_sutta_raw` removed (replaced by extracting from critical edition)
- **Five witnesses**: PTS/GRETIL (base text), SuttaCentral, VRI, BJT, Thai Royal Edition
- **Corrections**: Where SC=VRI=BJT disagree with PTS and PTS reading is not in DPD
- **Lemmatization**: DPD-based, 99.78% token-level coverage
