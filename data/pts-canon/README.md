# CST canonical Tipiṭaka, organized by PTS volumes

This is the **Chaṭṭha Saṅgāyana (CST/VRI) text** of the canonical Pāli Tipiṭaka
(mūla only), **segmented to match Pali Text Society volume boundaries**.

It is **NOT the PTS edition's text.** The PTS edition has its own readings; this
aligns *structure* (volume boundaries), not text. PTS volume boundaries are
taken from the GRETIL/Dhammakaya PTS-based digitization (which carries PTS page
markers). Build: `~/pali-canon/build_pts_canon.py`. Provenance per volume:
`MANIFEST.csv`.

## Contents (55 volumes)
- **Sutta (40):** from `pali-commentary/data/raw-pts` (`.mul`), already
  PTS-organized by `reorganise_pts.py`.
- **Vinaya (5):** Mahāvagga, Cullavagga, Suttavibhaṅga I–II, Parivāra
  (CST 5 mūla files → PTS 5 volumes, reordered).
- **Abhidhamma (10):** Dhammasaṅgaṇī, Vibhaṅga, Dhātukathā, Puggalapaññatti,
  Kathāvatthu, Yamaka I–II, Paṭṭhāna (Tika / Duka / combined).

## Verification status
- **Text conservation: PASS** — output words == CST source words, per basket
  (Vinaya+Abhidhamma 1,220,873; Sutta 1,487,175). No text lost.
- **Vinaya III/IV boundary: VERIFIED** against GRETIL — CST Pārājikapāḷi /
  Pācittiyapāḷi split matches PTS Vol III / IV exactly (both end / begin at the
  Nissaggiya → Pācittiya boundary).
- **Yamaka I/II boundary: derived from GRETIL** — PTS Vol II begins at the
  Cittayamaka (8th yamaka); split there (mid-CST-file).

## Known TODO (expert verification needed)
1. **Paṭṭhāna fine PTS sub-volume boundaries.** Emitted at 3 clean CST-grounded
   divisions (Tika / Duka / combined). The full PTS Paṭṭhāna subdivides the
   Tikapaṭṭhāna into Parts I–III and arranges the Duka and combined paṭṭhānas
   across volumes; those boundaries fall mid-CST and are intricate. FLAGGED.
2. **Sutta volume boundaries** were set by `reorganise_pts.py` from structural
   headings, not cross-checked against GRETIL's volume/page markers. A
   confirmation pass against GRETIL (`an_vol*`, etc.) is outstanding.
3. **Abhidhamma single-volume books** assume CST file = PTS volume; not yet
   confirmed against GRETIL page counts.
4. **Kathāvatthu** kept as one unit (PTS paginates it continuously); the 2-volume
   physical binding split is not reproduced.
