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

- Total word tokens: 1,618,486
- Unique word forms: 127,033
- Words identified: 123,859
- Coverage: **97.5%**
- Sandhi decompositions: 42,440

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

### Summaries
- `data/_FINAL_PROJECT_SUMMARY.json` - Complete project statistics
- `data/critical/_complete_tipitaka_summary.json` - Critical edition summary

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

*Generated: February 4, 2026*
