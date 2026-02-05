# Pāli Canon Critical Edition - Code Architecture

## Overview

This project creates a digital critical edition of the complete Pāli Tipiṭaka by collating three independent textual witnesses:
- **GRETIL**: PTS (Pali Text Society) edition transcriptions
- **VRI**: Vipassana Research Institute Chaṭṭha Saṅgāyana (CST4)
- **SuttaCentral**: Mahāsaṅgīti edition with modern segmentation

## Codebase Statistics

- **Total Lines**: ~9,200 lines of Python
- **Files**: 33 Python modules
- **Language**: Python 3.10+
- **Dependencies**: Standard library only (json, re, pathlib, sqlite3, difflib)

---

## Directory Structure

```
pali/
├── src/                    # All Python source code
│   ├── parse_*.py          # Source text parsers
│   ├── build_*.py          # Pipeline builders
│   ├── lemmatize_*.py      # Lemmatization tools
│   └── *.py                # Analysis and utility scripts
├── data/
│   ├── vri-raw/            # Raw VRI CST files
│   ├── vri-parsed/         # Parsed VRI JSON
│   ├── gretil-pts/         # Raw GRETIL HTML files
│   ├── gretil-parsed/      # Parsed GRETIL JSON
│   ├── canonical/          # SuttaCentral source files
│   ├── critical/           # Output: critical edition files
│   ├── lemmatized/         # Output: lemmatized texts
│   ├── dpd/                # Digital Pāli Dictionary database
│   └── dppn/               # Dictionary of Pāli Proper Names
└── docs/                   # Documentation and papers
```

---

## Pipeline Architecture

### Stage 1: Parsing Source Texts

```
Raw Sources → Parsers → Normalized JSON
```

| Parser | Input | Output | Description |
|--------|-------|--------|-------------|
| `parse_gretil_complete.py` | `*.htm` | `gretil-parsed/*.json` | Parse GRETIL PTS HTML files |
| `parse_vri_complete.py` | `*.mul.txt` | `vri-parsed/*.json` | Parse VRI CST text files |
| `build_canonical_*.py` | SC bilara | `canonical/*.json` | Process SuttaCentral data |

**Output JSON format:**
```json
{
  "file": "filename.htm",
  "text": "Cleaned Pāli text...",
  "word_count": 12345
}
```

### Stage 2: Building Critical Editions

```
Parsed JSON → Critical Builder → Critical Edition JSON
```

| Builder | Witnesses | Coverage |
|---------|-----------|----------|
| `build_critical_complete.py` | 2-3 | Full Tipiṭaka |

**Critical edition output format:**
```json
{
  "id": "mn1",
  "witnesses": ["SC", "GRETIL", "VRI"],
  "word_count": 5432
}
```

### Stage 3: Lemmatization

```
Canonical JSON → Lemmatizer → Lemmatized JSON
```

| Tool | Input | Output |
|------|-------|--------|
| `lemmatize_canon.py` | `canonical/*.json` | `lemmatized/*.json` |

Uses:
- Digital Pāli Dictionary (DPD) SQLite database
- Dictionary of Pāli Proper Names (DPPN)

**Lemmatized segment format:**
```json
{
  "id": "mn1:1.1",
  "pali": "Evaṃ me sutaṃ",
  "tokens": [
    {"word": "evaṃ", "lemma": "evaṃ", "pos": "ind"},
    {"word": "me", "lemma": "ahaṃ", "pos": "pron"},
    {"word": "sutaṃ", "lemma": "suṇāti", "pos": "pp", "root": "√su"}
  ]
}
```

---

## Key Modules

### Parsing Layer

#### `parse_gretil_complete.py` (453 lines)
Parses complete GRETIL archive:
- Vinaya Piṭaka (5 texts)
- Sutta Piṭaka (5 nikāyas)
- Abhidhamma Piṭaka (11 texts)

Key functions:
- `clean_html_text()`: Strip HTML, normalize whitespace
- `parse_vinaya()`: Handle Vinaya-specific file patterns
- `parse_sutta_nikaya()`: Generic nikāya parser
- `parse_kn()`: Special handling for Khuddaka (22 texts)
- `parse_abhidhamma()`: Abhidhamma with Paṭṭhāna variants

#### `parse_vri_complete.py` (292 lines)
Parses VRI Chaṭṭha Saṅgāyana files:
- Handles `.mul.txt` (mūla/root text) files
- BOM stripping and encoding normalization
- Word count using Pāli character regex

### Building Layer

#### `build_critical_complete.py` (842 lines)
Master builder for entire Tipiṭaka:

```python
def main():
    results['vinaya'] = build_vinaya_critical()    # 2 witnesses
    results['dn'] = build_dn_critical()            # 3 witnesses
    results['mn'] = build_mn_critical()            # 3 witnesses
    results['sn'] = build_sn_critical()            # 3 witnesses
    results['an'] = build_an_critical()            # 3 witnesses
    results['kn'] = build_kn_critical()            # 2-3 witnesses
    results['abhidhamma'] = build_abhidhamma_critical()  # 2 witnesses
```

### Lemmatization Layer

#### `lemmatize_canon.py` (727 lines)
The most complex module. Features:

1. **DPD Integration**: SQLite queries against DPD headwords
2. **Sandhi Decomposition**: Uses DPD's deconstructor field
3. **Normalization Strategies**:
   - Orthographic variants (`-n` → `-ṃ`)
   - Metrical lengthening (final `ā` → `a`)
   - Internal metrical normalization
4. **Particle Splitting**: `dhammañca` → `dhammaṃ + ca`
5. **Pronoun-Verb Fusion**: `ahamanusāsissāmi` → `ahaṃ + anusāsissāmi`
6. **Compound Decomposition**: Greedy longest-match with backtracking
7. **DPPN Matching**: Proper noun identification

Key class:
```python
class Lemmatizer:
    def __init__(self, db_path, dppn_path)
    def tokenize(self, text) -> list[str]
    def lookup_word(self, word) -> TokenInfo
    def lemmatize_segment(self, segment) -> dict
```

### Analysis Layer

#### `generate_final_summary.py` (230 lines)
Aggregates statistics from all pipeline stages.

#### `analyze_unknown_words.py` (219 lines)
Categorizes words not found in DPD for potential contribution.

---

## Data Formats

### SuttaCentral Canonical Format

DN/MN (flat segments):
```json
{
  "id": "dn1",
  "segments": [
    {"id": "dn1:1.1", "pali": "..."}
  ]
}
```

SN/AN (nested suttas):
```json
{
  "id": "sn1",
  "suttas": [
    {
      "id": "sn1.1",
      "segments": [...]
    }
  ]
}
```

KN (nested items):
```json
{
  "id": "dhp",
  "items": [
    {
      "id": "dhp1-20",
      "segments": [...]
    }
  ]
}
```

### Critical Edition Format

```json
{
  "timestamp": "2026-02-04T18:15:07",
  "vinaya_pitaka": {...},
  "sutta_pitaka": {
    "dn": {...},
    "mn": {...},
    "sn": {...},
    "an": {...},
    "kn": {...},
    "totals": {...}
  },
  "abhidhamma_pitaka": {...},
  "grand_totals": {
    "sc_words": 1596896,
    "gretil_words": 3059680,
    "vri_words": 2418765
  }
}
```

---

## Dependencies

### External Data
- **DPD**: `data/dpd/dpd.db` (SQLite, ~400MB)
- **DPPN**: `data/dppn/proper_names.json`

### Python Standard Library
- `json`: Data serialization
- `re`: Pāli text tokenization
- `pathlib`: Cross-platform paths
- `sqlite3`: DPD database access
- `difflib.SequenceMatcher`: Text alignment
- `collections.Counter`: Statistics
- `dataclasses`: TokenInfo structure

---

## Future Extensions

### 1. REST API
```
GET /api/sutta/{id}           → Critical edition JSON
GET /api/sutta/{id}/lemmas    → Lemmatized version
GET /api/search?q={query}     → Full-text search
GET /api/variants/{id}        → Variant readings
```

### 2. LaTeX Typesetting
Generate print-ready critical apparatus:
```latex
\begin{criticalapparatus}
  \variant{1.1}{dhamma}{dhammo}{VRI}
\end{criticalapparatus}
```

### 3. TEI-XML Export
Standard scholarly edition format for interoperability.

### 4. Variant Alignment
Word-level alignment between witnesses for detailed apparatus.

---

## Running the Pipeline

```bash
# Parse all sources
python src/parse_gretil_complete.py
python src/parse_vri_complete.py

# Build critical editions
python src/build_critical_complete.py

# Run lemmatization
python src/lemmatize_canon.py

# Generate summary
python src/generate_final_summary.py
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Python code | 9,198 lines |
| Python modules | 33 files |
| GRETIL words | 3,243,906 |
| VRI words | 2,418,765 |
| SC words | 1,596,896 |
| Lemmatization coverage | 97.5% |
| Unique lemmas identified | 123,859 |

---

*Last updated: February 2026*
