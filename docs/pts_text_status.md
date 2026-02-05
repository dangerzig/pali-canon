# PTS Text Extraction: Status and Recommendations

## Summary

A pilot project was conducted to extract text from OCR'd PTS Dīgha Nikāya editions. The OCR quality proved insufficient for word-level textual analysis, though the work provides valuable insights for future approaches.

## Current Text Source Quality

| Source | Quality | Diacritics | Notes |
|--------|---------|------------|-------|
| SC Canonical (current) | Excellent | ✓ | Proper Unicode, pre-segmented |
| VRI/CST | Excellent | ✓ | Proper Unicode, continuous text |
| GRETIL PTS Edition | Good | ✓ | Proper Unicode (manually transcribed by Dhammakaya Foundation) |
| PTS OCR (`data/pts-text/`) | Poor | ✗ | Missing diacritics, ligature errors |

## OCR Quality Analysis

The `src/analyze_pts_ocr.py` script analyzed all 34 DN suttas:

- **0/34** suttas rated "good" quality (≥70/100)
- **1/34** sutta rated "moderate" quality (DN 32)
- **33/34** suttas rated "poor" quality (<50/100)
- **Average quality score**: 35.9/100
- **Average word ratio**: 1.66× (66% more words than expected due to OCR noise)

### Key Issues

1. **Missing Diacritics** (65-89% of words affected)
   - `abbhantarānaṃ` → `abbhantaranam`
   - `bhagavā` → `bhagava`

2. **Ligature Errors** (5-138 per sutta)
   - `abhiññā` → `abhififia` (ñ misread as fi)
   - `pañca` → `pafica`

3. **Word Fragments** (54-1,182 per sutta)
   - Broken words from line/page breaks: `abh`, `abhik`, `abbhok`

4. **Critical Apparatus** retained in text
   - Footnotes, variant readings, manuscript sigla

## Recommendations

### Short-term (Current Project)

1. **Continue using SC canonical text** for lemmatization
   - Already achieving 97.5% coverage
   - Good quality Unicode with proper diacritics
   - Pre-segmented with translation-aligned IDs

2. **Use PTS text for page mapping only**
   - Map SC segments to approximate PTS page ranges
   - Don't rely on word-level accuracy

### Medium-term (GRETIL Source - TESTED)

GRETIL transcriptions were downloaded and tested (see `src/download_gretil_dn.py`):

| Metric | Value |
|--------|-------|
| Suttas extracted | 33/34 (97%) |
| Average word ratio (GRETIL/SC) | 1.17 |
| Average vocabulary overlap | 42.8% |
| Good quality (ratio 0.85-1.15) | 10 suttas |
| Moderate quality (ratio 0.7-1.3) | 18 suttas |

**Source details:**
- URL: https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/
- Digitized by Dhammakaya Foundation (1989-1996)
- License: CC BY-SA 4.0
- Proper Unicode with all diacritics

**Results stored in:** `data/gretil-parsed/dn/`

**Next step:** Create hybrid edition by aligning GRETIL PTS text with SC segment IDs

### Long-term (Full PTS Authority)

1. **Re-OCR PTS PDFs** with modern tools
   - Tesseract 5.x with Pāli training data
   - Google Cloud Vision API
   - Human verification for critical texts

2. **Collate with manuscript evidence**
   - Record PTS critical apparatus in structured format
   - Note manuscript sigla (B, S, K, M, etc.)

## Files Created

| File | Purpose |
|------|---------|
| `src/parse_pts_dn.py` | PTS text extraction (boundary detection) |
| `src/compare_pts_sc.py` | PTS vs SC word comparison |
| `src/analyze_pts_ocr.py` | OCR quality metrics |
| `data/pts-parsed/dn/*.json` | Extracted sutta text (poor quality) |
| `data/pts-parsed/dn/_comparison.json` | Word-level comparison data |
| `data/pts-parsed/dn/_ocr_quality.json` | Quality metrics per sutta |

## Conclusion

The PTS text extraction pilot successfully:
- Established a parsing pipeline for PTS volumes
- Identified sutta boundaries across 3 volumes
- Revealed systematic OCR quality issues

However, the OCR quality is insufficient for word-level textual analysis. The existing SC canonical text (based on Chaṭṭha Saṅgāyana) should remain the primary source for lemmatization. For a true PTS-based edition, the GRETIL transcriptions offer a viable alternative with proper Unicode and CC BY-SA licensing.

---

*Analysis completed: February 2026*
