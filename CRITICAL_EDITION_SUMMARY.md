# Complete Pāli Tipiṭaka Critical Edition

## Project Status: COMPLETE

The digital critical edition now covers the **entire Pāli Canon** (Tipiṭaka).

---

## Source Data

| Source | Edition | Total Words |
|--------|---------|-------------|
| GRETIL | PTS (Pali Text Society) | 3,243,906 |
| VRI | Chaṭṭha Saṅgāyana (CST4) | 2,618,883 |
| SuttaCentral | Mahāsaṅgīti | 2,837,350 |
| BJT | Buddha Jayanti Tipitaka | 3,514,083 |
| Thai | Syām Raṭṭha (Royal Thai Edition) | ~2,642,000 |

---

## Critical Edition Coverage

### Vinaya Piṭaka (5 witnesses: SC/GRETIL/VRI/BJT/Thai)
- **5 texts** (Suttavibhaṅga 1-2, Mahāvagga, Cullavagga, Parivāra)
- SC: 420,556 words
- GRETIL: 376,093 words
- VRI: 419,054 words
- BJT: 537,956 words

### Sutta Piṭaka (5 witnesses: SC/GRETIL/VRI/BJT/Thai)

| Nikāya | Units | SC Words | GRETIL Words | VRI Words | BJT Words |
|--------|-------|----------|--------------|-----------|-----------|
| Dīgha (DN) | 34 suttas | 143,999 | 175,065 | 144,180 | 215,796 |
| Majjhima (MN) | 152 suttas | 247,338 | 249,813 | 248,810 | 294,554 |
| Saṃyutta (SN) | 56 files | 265,006 | 279,549 | 267,747 | 551,483 |
| Aṅguttara (AN) | 11 files | 300,638 | 334,147 | 302,871 | 451,769 |
| Khuddaka (KN) | 20 texts | 639,897 | 1,090,590 | 523,567 | 643,865 |
| **TOTAL** | | **1,596,878** | **2,129,164** | **1,487,175** | **2,157,467** |

### Abhidhamma Piṭaka (5 witnesses: SC/GRETIL/VRI/BJT/Thai)
- **11 texts** (Dhammasaṅgaṇī, Vibhaṅga, Dhātukathā, Puggalapaññatti, Kathāvatthu, Yamaka 1-2, Paṭṭhāna 1-3 + Duka)
- SC: 819,916 words
- GRETIL: 554,423 words
- VRI: 712,654 words
- BJT: 818,660 words

---

## Grand Totals

| Witness | Total Words |
|---------|-------------|
| SC | 2,837,350 |
| GRETIL | 3,059,680 |
| VRI | 2,618,883 |
| BJT | 3,514,083 |
| Thai | ~2,642,000 |

---

## Lemmatization Statistics

Lemmatization covers the SC Mahāsaṅgīti Sutta Piṭaka text (1.6M words):

- Total word tokens: 1,606,474
- Unique word forms: 127,026
- Words identified: 124,270
- Sandhi decompositions: 42,449
- Custom lemmas: 160 applied (193 entries in database)
- **Unique word coverage: 97.8%**
- **Token-level coverage: 99.78%**

The high token-level coverage reflects that high-frequency words are well-covered, while remaining unknown forms are predominantly rare words (hapax legomena) from verse texts.

---

## Collation Statistics

Word-level collation across witnesses, with automatic classification of differences.

Note: some collation files cap entries at 1,000 per category per text, so totals below are lower bounds.

### Sutta Piṭaka (5 witnesses: SC/GRETIL/VRI/BJT/Thai)

| Nikāya | Texts | Errors | Variants |
|--------|-------|--------|----------|
| DN | 34 | 4,355 | 9,135 |
| MN | 150 | 4,555 | 11,534 |
| SN | 1,564 | 15,617 | 10,411 |
| AN | 843 | 5,164 | 26,433 |
| KN | 17 | 8,532 | 10,683 |

### Vinaya & Abhidhamma (5 witnesses: SC/GRETIL/VRI/BJT/Thai)

| Piṭaka | Texts | Errors | Variants |
|--------|-------|--------|----------|
| Vinaya | 5 | 4,580 | 5,000 |
| Abhidhamma | 7 | 5,145 | 5,409 |

### Classification Methodology

**Errors** are applied only when:
1. Multiple witnesses (SC, VRI, BJT) agree against PTS (GRETIL), AND
2. PTS reading is NOT a valid Pāli word (absent from DPD)

**Variants** are recorded when both readings are valid Pāli words.

See `data/collation/pts_corrections_catalog.json` for DN/MN/SN correction catalog.

---

## Files Created

### Source Scripts
- `src/parse_gretil_complete.py` - Parse all GRETIL PTS texts
- `src/parse_vri_complete.py` - Parse all VRI CST texts
- `src/parse_bjt.py` - Parse all BJT texts
- `src/split_bjt.py` - Split BJT volumes into per-sutta files
- `src/parse_thai.py` - Parse Thai Royal Edition from E-Tipitaka
- `src/split_thai.py` - Split Thai volumes into per-sutta files
- `src/build_critical_complete.py` - Build critical editions
- `src/generate_final_summary.py` - Generate statistics

### Data Directories
- `data/gretil-parsed/` - Parsed GRETIL texts (Vinaya, 5 Nikāyas, Abhidhamma)
- `data/vri-parsed/` - Parsed VRI texts (Vinaya, 5 Nikāyas, Abhidhamma)
- `data/bjt-parsed/` - Parsed BJT texts (all piṭakas: volumes + per-sutta files)
- `data/thai-parsed/` - Parsed Thai Royal Edition (all piṭakas)
- `data/critical/` - Critical edition files (all collections)
- `data/lemmatized/` - Lemmatized SC texts
- `data/collation/` - Word-level collation with variant classification

### Summaries
- `data/_FINAL_PROJECT_SUMMARY.json` - Complete project statistics
- `data/critical/_complete_tipitaka_summary.json` - Critical edition summary
- `data/collation/pts_corrections_catalog.json` - Cataloged PTS transcription errors

---

## This Represents

- **Vinaya Piṭaka** - Monastic discipline
- **Sutta Piṭaka** - Discourses of the Buddha
  - Dīgha Nikāya (long discourses)
  - Majjhima Nikāya (middle-length discourses)
  - Saṃyutta Nikāya (connected discourses)
  - Aṅguttara Nikāya (numerical discourses)
  - Khuddaka Nikāya (minor texts)
- **Abhidhamma Piṭaka** - Systematic philosophy

---

*Last updated: February 2026*
