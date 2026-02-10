# Pāli Canon Critical Edition

A digital critical edition of the complete Pāli Tipiṭaka with multi-witness collation, lemmatization, and analysis tools.

## Overview

This project provides:
- **Five-witness collation** of the complete Tipiṭaka (SuttaCentral, GRETIL PTS, VRI CST, BJT, Thai Syām Raṭṭha)
- **Lemmatization** using the Digital Pāli Dictionary (DPD)
- **Vocabulary analysis** and document-term matrices for computational analysis
- **PTS correction catalog** documenting transcription errors in the PTS edition

## Quick Start

```python
from pali import Canon

# Initialize with data directory
canon = Canon("data")

# Load a sutta
sutta = canon.get_sutta("dn1")
print(sutta.title_pali)  # "Brahmajālasutta"

# Get lemmatized version with tokens
sutta = canon.get_sutta("dn1", lemmatized=True)
for segment in sutta.segments[:3]:
    print(segment.pali)

# Vocabulary statistics
vocab = canon.get_vocabulary("dn1")
print(f"Unique lemmas: {vocab.unique_lemmas}")
print(f"Top 10: {vocab.top_lemmas[:10]}")

# Search by lemma
results = canon.search_lemma("dhamma")
print(f"Found in {len(results)} segments")
```

## Data Coverage

| Piṭaka | Texts | Witnesses | Words |
|--------|-------|-----------|-------|
| **Vinaya** | 5 | SC, GRETIL, VRI, BJT, Thai | ~595K |
| **Sutta** | 273 units | SC, GRETIL, VRI, BJT, Thai | ~5.2M |
| **Abhidhamma** | 11 | SC, GRETIL, VRI, BJT, Thai | ~1.3M |

### Sutta Piṭaka Detail

| Nikāya | Suttas | SC | GRETIL | VRI | BJT | Thai |
|--------|--------|-----|--------|-----|-----|------|
| DN | 34 | 144K | 175K | 144K | 214K | 145K |
| MN | 152 | 247K | 250K | 249K | 292K | 249K |
| SN | 56 files | 265K | 280K | 268K | 559K | 265K |
| AN | 11 files | 301K | 334K | 303K | 466K | 300K |
| KN | 20 texts | 640K | 1.1M | 524K | 674K | 523K |

## Installation

Requires Python 3.10+.

```bash
# Clone the repository
git clone https://github.com/your-repo/pali.git
cd pali

# Install dependencies
pip install pyyaml

# Optional: for vocabulary analysis
pip install pandas scipy
```

## Project Structure

```
pali/
├── src/
│   ├── pali/              # Core library
│   │   ├── __init__.py    # Public API (Canon class)
│   │   ├── models.py      # Data models (Sutta, Segment, Token)
│   │   ├── store.py       # JSON file access
│   │   ├── vocab.py       # Vocabulary analysis
│   │   ├── index.py       # Search index
│   │   └── custom_lemmas.yaml  # Custom lemma mappings
│   ├── parse_*.py         # Source file parsers
│   ├── lemmatize_canon.py # Lemmatization pipeline
│   └── build_critical_complete.py  # Critical edition builder
├── data/
│   ├── canonical/         # SC Mahāsaṅgīti texts
│   ├── lemmatized/        # Lemmatized SC texts
│   ├── gretil-parsed/     # Parsed GRETIL PTS texts
│   ├── vri-parsed/        # Parsed VRI CST texts
│   ├── bjt-parsed/        # Parsed BJT texts
│   ├── thai-parsed/       # Parsed Thai Royal Edition texts
│   ├── critical/          # Critical edition output
│   └── collation/         # Collation results
└── docs/
    ├── methodology.md     # Scholarly methodology
    └── ARCHITECTURE.md    # Technical architecture
```

## Documentation

- **[Methodology](docs/methodology.md)** - Scholarly approach and editorial decisions
- **[Architecture](docs/ARCHITECTURE.md)** - Technical design and data flow
- **[Critical Edition Summary](CRITICAL_EDITION_SUMMARY.md)** - Complete statistics

## Key Features

### Lemmatization

99.78% token-level coverage using the Digital Pāli Dictionary, with custom lemmas for rare forms.

```python
# Get lemmatized tokens
sutta = canon.get_sutta("dn1", lemmatized=True)
for token in sutta.segments[0].tokens:
    print(f"{token.word} -> {token.lemma} ({token.pos})")
```

### Search

Full-text and lemma search across the canon:

```python
# Search by lemma
results = canon.search_lemma("nibbāna")

# Full-text search
results = canon.search_text("evaṃ me sutaṃ")
```

### Vocabulary Analysis

Document-term matrices for computational analysis:

```python
# Get vocabulary for a nikāya
vocab = canon.get_vocabulary(nikaya="dn")

# Export document-term matrix
canon.vocab.export_dtm("dn", "dn_dtm.csv")
```

## Sources

- **SuttaCentral (SC)**: Mahāsaṅgīti edition with segment IDs
- **GRETIL**: PTS (Pali Text Society) edition digitized by Göttingen
- **VRI**: Chaṭṭha Saṅgāyana Tipiṭaka (CST4) from Vipassana Research Institute
- **BJT**: Buddha Jayanti Tipitaka, Sri Lankan government edition (1957–1989)
- **Thai**: Syām Raṭṭha (Royal Thai Edition), from E-Tipitaka

## License

Data sources retain their original licenses. Code is available under MIT license.

## Acknowledgments

- SuttaCentral for the Mahāsaṅgīti edition
- Digital Pāli Dictionary (DPD) for lemmatization
- GRETIL for PTS digitization
- VRI for the Chaṭṭha Saṅgāyana edition
- Buddha Jayanti Tipitaka for the Sri Lankan edition
