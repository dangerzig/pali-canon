# Complete Pāli Tipiṭaka Critical Edition

## Project Status: COMPLETE

The digital critical edition now covers the **entire Pāli Canon** (Tipiṭaka).

---

## Source Data

| Source | Edition | Total Words |
|--------|---------|-------------|
| GRETIL | PTS (Pali Text Society) | 3,243,906 |
| VRI | Chaṭṭha Saṅgāyana (CST4) | 2,418,765 |
| SuttaCentral | Mahāsaṅgīti | 1,596,896 |

---

## Critical Edition Coverage

### Vinaya Piṭaka (2 witnesses: GRETIL/VRI)
- **5 texts** (Suttavibhaṅga 1-2, Mahāvagga, Cullavagga, Parivāra)
- GRETIL: 376,093 words
- VRI: 218,936 words

### Sutta Piṭaka (3 witnesses: SC/GRETIL/VRI)

| Nikāya | Units | SC Words | GRETIL Words | VRI Words |
|--------|-------|----------|--------------|-----------|
| Dīgha (DN) | 34 suttas | 143,999 | 175,065 | 144,180 |
| Majjhima (MN) | 152 suttas | 247,338 | 249,813 | 248,810 |
| Saṃyutta (SN) | 56 files | 265,024 | 279,549 | 267,747 |
| Aṅguttara (AN) | 11 files | 300,638 | 334,147 | 302,871 |
| Khuddaka (KN) | 20 texts | 639,897 | 1,090,590 | 523,567 |
| **TOTAL** | | **1,596,896** | **2,129,164** | **1,487,175** |

### Abhidhamma Piṭaka (2 witnesses: GRETIL/VRI)
- **11 texts** (Dhammasaṅgaṇī, Vibhaṅga, Dhātukathā, Puggalapaññatti, Kathāvatthu, Yamaka 1-2, Paṭṭhāna 1-3 + Duka)
- GRETIL: 554,423 words
- VRI: 712,654 words

---

## Grand Totals

| Metric | Value |
|--------|-------|
| 3-witness editions (SC/GRETIL/VRI) | 1,596,896 words |
| 2-witness editions (GRETIL/VRI) | 930,516 words |
| **Total Critical Edition** | **2,527,412 words** |

---

## Lemmatization Statistics

- Total word tokens: 1,606,474
- Unique word forms: 127,026
- Words identified: 124,270
- Sandhi decompositions: 42,449
- Custom lemmas: 160 applied (187 entries in database)
- **Unique word coverage: 97.8%**
- **Token-level coverage: 99.78%**

The high token-level coverage reflects that high-frequency words are well-covered, while remaining unknown forms are predominantly rare words (hapax legomena) from verse texts.

---

## Collation Statistics

Word-level collation across witnesses, with automatic classification of differences:

### Sutta Piṭaka (3 witnesses: SC/GRETIL/VRI)

| Nikāya | Texts | Errors | Variants |
|--------|-------|--------|----------|
| DN | 34 | 4,355 | 9,200 |
| MN | 150 | 4,555 | 11,534 |
| SN | 1,564 | 15,617 | 10,411 |
| AN | 843 | 13 | 44 |
| KN | 17 | 12,366 | 17,677 |

### Vinaya & Abhidhamma (2 witnesses: GRETIL/VRI)

| Piṭaka | Texts | Errors | Variants |
|--------|-------|--------|----------|
| Vinaya | 3 | 3,227 | 12,132 |
| Abhidhamma | 3 | 4,614 | 9,887 |

### Classification Methodology

**Errors** are applied only when:
1. SC and VRI agree against PTS (GRETIL), AND
2. PTS reading is NOT a valid Pāli word (absent from DPD)

**Variants** are recorded when both readings are valid Pāli words.

See `data/collation/pts_corrections_catalog.json` for DN/MN/SN correction catalog.

---

## Files Created

### Source Scripts
- `src/parse_gretil_complete.py` - Parse all GRETIL PTS texts
- `src/parse_vri_complete.py` - Parse all VRI CST texts
- `src/build_critical_complete.py` - Build critical editions
- `src/generate_final_summary.py` - Generate statistics

### Data Directories
- `data/gretil-parsed/` - Parsed GRETIL texts (Vinaya, 5 Nikāyas, Abhidhamma)
- `data/vri-parsed/` - Parsed VRI texts (Vinaya, 5 Nikāyas, Abhidhamma)
- `data/critical/` - Critical edition files (all collections)
- `data/lemmatized/` - Lemmatized SC texts
- `data/collation/` - Word-level collation with variant classification

### Summaries
- `data/_FINAL_PROJECT_SUMMARY.json` - Complete project statistics
- `data/critical/_complete_tipitaka_summary.json` - Critical edition summary
- `data/collation/pts_corrections_catalog.json` - Cataloged PTS transcription errors

---

## This Represents

✓ **Vinaya Piṭaka** - Monastic discipline
✓ **Sutta Piṭaka** - Discourses of the Buddha
  - Dīgha Nikāya (long discourses)
  - Majjhima Nikāya (middle-length discourses)
  - Saṃyutta Nikāya (connected discourses)
  - Aṅguttara Nikāya (numerical discourses)
  - Khuddaka Nikāya (minor texts)
✓ **Abhidhamma Piṭaka** - Systematic philosophy

---

*Last updated: February 2026*
