# DN Pilot Project Summary

*Status Report for User Review*

## Objective

Extract and validate PTS Dīgha Nikāya text as a foundation for PTS-based canonical files.

## Work Completed

### 1. OCR'd PTS Text Analysis

**Source:** `data/pts-text/sutta/06-Digha-Nikaya-*.txt` (OCR from PTS PDFs)

**Script:** `src/parse_pts_dn.py`

**Findings:**
- All 34 suttas extracted with boundary detection
- OCR quality is **poor** (average score: 35.9/100)
- 65-89% of words missing diacritics
- Numerous ligature errors (ñ → fi)
- Significant word fragments from broken text

**Conclusion:** The OCR text is unsuitable for word-level analysis. It can only be used for approximate page reference mapping.

### 2. GRETIL PTS Edition

**Source:** GRETIL (Göttingen) - Dhammakaya Foundation transcription

**Script:** `src/download_gretil_dn.py`

**Findings:**
- 33/34 suttas extracted successfully
- Proper Unicode with all diacritics
- Average word ratio vs SC: 1.17 (reasonable)
- License: CC BY-SA 4.0

**Conclusion:** GRETIL provides a viable PTS source for building PTS-based canonical files.

### 3. Current Canonical Text (SC)

**Source:** SuttaCentral Mahāsaṅgīti edition

**Status:** Already lemmatized at 97.5% coverage

**Quality:** Excellent - proper Unicode, pre-segmented

## Data Created

| Directory | Contents |
|-----------|----------|
| `data/pts-parsed/dn/` | OCR-based sutta extractions (poor quality) |
| `data/pts-parsed/dn/_ocr_quality.json` | Quality metrics per sutta |
| `data/pts-parsed/dn/_comparison.json` | PTS vs SC word comparison |
| `data/gretil-pts/` | Downloaded GRETIL HTML files |
| `data/gretil-parsed/dn/` | GRETIL-based sutta extractions (good quality) |
| `data/gretil-parsed/dn/_summary.json` | Extraction summary |

## Scripts Created

| Script | Purpose |
|--------|---------|
| `src/parse_pts_dn.py` | Extract suttas from OCR'd PTS text |
| `src/compare_pts_sc.py` | Compare PTS and SC at word level |
| `src/analyze_pts_ocr.py` | Analyze OCR quality metrics |
| `src/download_gretil_dn.py` | Download and process GRETIL edition |

## Documentation Created

| File | Contents |
|------|----------|
| `docs/pts_text_status.md` | Detailed status and recommendations |
| `docs/methodology.md` | Updated with PTS extraction section |

## Recommendations

### For DN (Immediate)

1. **Use SC canonical text** for lemmatization (already done)
2. **Use GRETIL** for PTS reference alignment
3. **Create SC→PTS page mapping** by aligning segment boundaries

### For Other Collections (Future)

1. Download remaining GRETIL volumes (MN, SN, AN, KN)
2. Apply same extraction approach
3. Build unified PTS reference system

### For True PTS Authority (Long-term)

1. Re-OCR PDFs with modern tools or
2. Use GRETIL as primary PTS source
3. Systematically collate variants between editions

## Quality Summary

| Source | Quality | Diacritics | Coverage | Use Case |
|--------|---------|------------|----------|----------|
| SC Canonical | Excellent | ✓ | 100% | Primary text |
| GRETIL PTS | Good | ✓ | 97% | PTS reference |
| OCR PTS | Poor | ✗ | 100% | Page mapping only |

## Next Steps (Pending User Decision)

1. **Align GRETIL with SC segments** - Map PTS page references to SC segment IDs
2. **Expand to other nikāyas** - Download MN, SN, AN, KN from GRETIL
3. **Build variant apparatus** - Document textual differences between editions

---

*Report generated: February 2026*
