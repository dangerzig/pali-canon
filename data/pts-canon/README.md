# CST canonical Tipiṭaka, organized by PTS volumes

This is the **Chaṭṭha Saṅgāyana (CST/VRI) text** of the canonical Pāli Tipiṭaka
(mūla only), **segmented to match Pali Text Society volume boundaries**.

It is **NOT the PTS edition's text.** The PTS edition has its own readings; this
aligns *structure* (volume boundaries), not text. PTS volume boundaries are
taken from the GRETIL/Dhammakaya PTS-based digitization (which carries PTS page
markers). Build: `~/pali-canon/build_pts_canon.py`. Provenance per volume:
`MANIFEST.csv`.

The CST source text is the VRI Latin distribution `tipitaka_text_latn`
(2020-04-12), held in `data/vri-raw`. Each `vri-raw` file is the cleaner of the
available extractions: `vin02m2`/`vin02m3` (Mahāvagga/Cullavagga) use the
2020-04-12 text, which is free of the footnote-apparatus that had been inlined
into an earlier copy (cross-references such as `udā. 11`, `kathā. 338`, and
embedded ṭīkā glosses); `s0516m`/`abh03m8` keep the earlier copy, which is free
of stray footnote-digit artifacts present in 2020-04-12.

## Contents (55 volumes)
- **Sutta (40):** from `pali-commentary/data/raw-pts` (`.mul`), already
  PTS-organized by `reorganise_pts.py`.
- **Vinaya (5):** Mahāvagga, Cullavagga, Suttavibhaṅga I–II, Parivāra
  (CST 5 mūla files → PTS 5 volumes, reordered).
- **Abhidhamma (10):** Dhammasaṅgaṇī, Vibhaṅga, Dhātukathā, Puggalapaññatti,
  Kathāvatthu, Yamaka I–II, Paṭṭhāna (Tika / Duka / combined).

## Verification status
- **Text conservation: PASS** — output words == CST source words, per basket
  (Vinaya+Abhidhamma 1,217,773; Sutta 1,487,175). No text lost. (The
  Vinaya+Abhidhamma count dropped from 1,220,873 after the Mahāvagga/Cullavagga
  source was de-contaminated of inlined footnote apparatus; see provenance note
  above.)
- **Vinaya: all 5 volumes VERIFIED** against GRETIL by matching closing
  colophons (Mahāvagga, Cullavagga, Suttavibhaṅga I–II, Parivāra). The III/IV
  split matches PTS exactly (Nissaggiya → Pācittiya boundary).
- **Abhidhamma single-volume books: VERIFIED** (Dhammasaṅgaṇī, Vibhaṅga — CST
  span == GRETIL PTS volume span; Dhātukathā/Puggalapaññatti/Kathāvatthu are
  likewise single-volume).
- **Yamaka I/II boundary: derived from GRETIL** — PTS Vol II begins at the
  Cittayamaka (8th yamaka); split there (mid-CST-file).
- **Sutta: AN Vol I VERIFIED** against GRETIL (both end at the Tikanipāta); the
  reorganise_pts boundaries align with PTS at the points checked.
- **Abhidhamma single-volume books VERIFIED against GRETIL** — Dhammasaṅgaṇī,
  Vibhaṅga, Dhātukathā, Puggalapaññatti and Kathāvatthu each close at the same
  point as GRETIL's single PTS volume (e.g. Vibhaṅga → Dhammahadayavibhaṅga;
  Puggalapaññatti → Dasakaniddesa; Kathāvatthu → 35th bhāṇavāra). So CST file =
  PTS volume holds for these.
- **Kathāvatthu = one unit, CONFIRMED** — GRETIL also carries it as a single
  continuously-paginated unit (35 bhāṇavāras); no content-bearing 2-volume split.
- **Paṭṭhāna top-level Tika/Duka division CONFIRMED consistent with GRETIL** —
  GRETIL separates the Tikapaṭṭhāna (Parts I–III) from the Dukapaṭṭhāna, matching
  our Tika / Duka / combined scheme at the major-division level.

## Known TODO (refinements; none affect text correctness)
1. **Paṭṭhāna fine PTS sub-volume boundaries.** Emitted at 3 clean CST-grounded
   divisions (Tika / Duka / combined), now confirmed consistent with GRETIL at
   that level. The finer split of the Tikapaṭṭhāna into Parts I–III (GRETIL ends
   them at Paccayavibhaṅgavāra and Kusalattika) falls mid-CST and it is not
   certain GRETIL's "Parts" equal PTS physical volumes; left FLAGGED rather than
   guessed.
2. **Sutta volume boundaries** were set by `reorganise_pts.py` from structural
   headings; AN Vol I is verified against GRETIL, but a full sweep of all 40
   Sutta volumes against GRETIL (`an_vol*`, `dn_vol*`, `jatak*`) is an
   outstanding confirmation (not a known defect).
