# CST commentaries (aṭṭhakathā), organized by PTS volumes

The **Chaṭṭha Saṅgāyana (CST/VRI) text** of the Vinaya & Abhidhamma
commentaries, **segmented to match Pali Text Society volume boundaries**. As
with the canon (`../pts-canon`), this aligns *structure* (volume boundaries),
**not text** — it is not the PTS edition's readings. Build:
`../../build_pts_commentary.py`. Plan: `../../commentary-pts-plan.md`. Provenance
per volume: `MANIFEST.csv`.

The **Sutta commentaries** are PTS-organized separately, in
`pali-commentary/data/raw-pts` (`.att` files), and are not duplicated here.

## Contents so far (6 volumes — the 1:1 mappings)

Each volume below is a single CST file equal to exactly one PTS volume,
**confirmed by the file's closing colophon** (the build asserts this):

**Abhidhamma (3):**
- `Atthasalini` — Atthasālinī, comm. on Dhammasaṅgaṇī (PTS 1 vol, Müller 1897)
- `Sammohavinodani` — Sammohavinodanī, comm. on Vibhaṅga (PTS 1 vol, Buddhadatta 1923)
- `Pancappakaranatthakatha` — comm. on the last 5 Abhidhamma books (PTS 1 vol, Buddhadatta 1956)

**Vinaya — Samantapāsādikā, clean tail (3):**
- `Samantapasadika_V_Mahavagga` — Mahāvagga-aṭṭhakathā (PTS Vol V)
- `Samantapasadika_VI_Cullavagga` — Cūḷavagga-aṭṭhakathā (PTS Vol VI)
- `Samantapasadika_VII_Parivara` — Parivāra-aṭṭhakathā (PTS Vol VII)

## Verification status

- **Text conservation: PASS** — output words == CST source words (343,695). No
  text lost.
- **Colophon-confirmed: PASS** — each source file ends with the expected
  division colophon (e.g. `Mahāvagga-aṭṭhakathā niṭṭhitā`).

## TODO

- **Samantapāsādikā Vols I–IV** (the Suttavibhaṅga aṭṭhakathā = CST `vin01a` +
  `vin02a1`): 3 internal PTS boundaries fall mid-CST-file and need GRETIL
  `samp_1pu`–`samp_4pu` page markers to locate. See the plan, step 3.
- **Pañcappakaraṇaṭṭhakathā flag:** PTS also issued the Kathāvatthu commentary
  separately (Minayeff, *JPTS* 1889); CST fuses all five, so this is one unit.
- **ṭīkās (Sāratthadīpanī, Mūlaṭīkā):** out of scope — no PTS roman edition to
  align to.
