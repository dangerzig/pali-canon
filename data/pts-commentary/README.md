# CST commentaries (aṭṭhakathā), organized by PTS volumes

The **Chaṭṭha Saṅgāyana (CST/VRI) text** of the Vinaya & Abhidhamma
commentaries, **segmented to match Pali Text Society volume boundaries**. As
with the canon (`../pts-canon`), this aligns *structure* (volume boundaries),
**not text** — it is not the PTS edition's readings. Build:
`../../build_pts_commentary.py`. Plan: `../../commentary-pts-plan.md`. Provenance
per volume: `MANIFEST.csv`.

The **Sutta commentaries** are PTS-organized separately, in
`pali-commentary/data/raw-pts` (`.att` files), and are not duplicated here.

Two **Sutta sub-commentaries** that *do* have a PTS roman edition are included
here as well (see below); the rest of the Sutta ṭīkās have no PTS edition.

## Contents — Vinaya & Abhidhamma aṭṭhakathā (10 volumes)

**Vinaya — Samantapāsādikā (PTS 7 vols, Takakusu & Nagai 1924–47):**
- `Samantapasadika_I_Bahiranidana_Parajika_I` — Bāhiranidāna + Pārājika I comm.
- `Samantapasadika_II_Parajika_II-IV` — Pārājika II–IV comm.
- `Samantapasadika_III_Sanghadisesa_Nissaggiya` — Saṅghādisesa … Nissaggiya comm.
- `Samantapasadika_IV_Pacittiya_Bhikkhunivibhanga` — Pācittiya … Bhikkhunīvibhaṅga comm.
- `Samantapasadika_V_Mahavagga` — Mahāvagga-aṭṭhakathā (PTS Vol V)
- `Samantapasadika_VI_Cullavagga` — Cūḷavagga-aṭṭhakathā (PTS Vol VI)
- `Samantapasadika_VII_Parivara` — Parivāra-aṭṭhakathā (PTS Vol VII)

**Abhidhamma (3):**
- `Atthasalini` — Atthasālinī, comm. on Dhammasaṅgaṇī (PTS 1 vol, Müller 1897)
- `Sammohavinodani` — Sammohavinodanī, comm. on Vibhaṅga (PTS 1 vol, Buddhadatta 1923)
- `Pancappakaranatthakatha` — comm. on the last 5 Abhidhamma books (PTS 1 vol, Buddhadatta 1956)

## Contents — Sutta sub-commentaries (ṭīkā) with a PTS edition (4 units)

**Dīgha-nikāya ṭīkā — Līnatthapakāsinī (PTS 3 vols, de Silva 1970, complete):**
- `Linatthapakasini_I_Silakkhandhavagga` — Sīlakkhandhavagga-ṭīkā (1:1, `s0101t`)
- `Linatthapakasini_II_Mahavagga` — Mahāvagga-ṭīkā (1:1, `s0102t`)
- `Linatthapakasini_III_Pathikavagga` — Pāthikavagga-ṭīkā (1:1, `s0103t`)

**Aṅguttara-nikāya ṭīkā — Sāratthamañjūsā (PTS partial, Peceṇko 1996–99):**
- `Saratthamanjusa_Ekanipata-tika` — **nipāta 1** (`s0401t`)
- `Saratthamanjusa_Dukanipata-tika` — **nipāta 2** (`s0402t` up to the
  Tikanipāta header; ends exactly at the Dukanipāta colophon)

The PTS edition covers **only nipātas 1–2 (Ekaka + Duka)**, per the editor's own
statement (Primož Peceṇko, *"Līnatthapakāsinī and Sāratthamañjūsā…"*, **JPTS
XXVII (2002), p. 78 n. 67**: "PTS edition by P. Peceṇko, Vols. I–III contain Eka-
and Dukanipāta-ṭīkā"). The PTS catalogue's "first seven chapters" refers to the
seven *sub-chapters* of the Ekanipāta-ṭīkā, **not** seven nipātas. Peceṇko
prints these two nipātas across 3 physical volumes (I, II = Eka; III = Duka,
approx.), but the page boundaries are unpublished, so the physical-volume split
is **FLAGGED**. **Nipātas 3–11** (rest of `s0402t`, plus `s0403t`, `s0404t`) are
**excluded** — no PTS edition.

## How the boundaries were set

- **7 of 10 are 1:1** — one CST file equals one PTS volume, **confirmed by the
  file's closing colophon** (asserted in the build): Samantapāsādikā IV–VII and
  all 3 Abhidhamma commentaries.
- **Samantapāsādikā I–III** come from splitting CST `vin01a` (the whole
  Suttavibhaṅga commentary) at two CST section headers. The split points were
  located using **GRETIL's PTS-paginated Samantapāsādikā** (`samp_Npu.htm`, each
  file = one PTS volume with `[page N]` markers):
  - PTS Vol II opens at **p.285** with the 2nd-Pārājika commentary → CST header
    `2. Dutiyapārājikaṃ`.
  - PTS Vol III opens at **p.517** with the Saṅghādisesa commentary → CST header
    `2. Saṅghādisesakaṇḍaṃ`.
  - PTS Vol IV opens at **p.735** with the Pācittiya commentary → start of CST
    file `vin02a1` (hence Vol IV is a clean 1:1).
  Corroboration: the three vin01a parts' CST char shares (37.7 / 31.2 / 31.1 %)
  track the PTS page shares of Vols I–III within pp.1–734 (38.7 / 31.6 / 29.7 %).

## Verification status

- **Text conservation: PASS** — output words == words of the emitted CST sources
  (773,154). No text lost (asserted globally; the vin01a 3-way split is also
  checked to sum exactly). Deliberate exclusion: AN ṭīkā nipātas 3–11 (rest of
  `s0402t`, `s0403t`, `s0404t`), which have no PTS edition.
- **1:1 colophon-confirmed: PASS** — each 1:1 source ends with its expected
  division colophon (e.g. `Mahāvagga-aṭṭhakathā niṭṭhitā`,
  `Sīlakkhandhavaggaṭīkā niṭṭhitā`).
- **Split anchors: PASS** — each anchor occurs exactly once; Vol II opens at the
  2nd Pārājika, Vol III opens at the Saṅghādisesa and ends at the Nissaggiya
  colophon. The AN Eka/Duka cut ends exactly at the Dukanipāta colophon.

## Out of scope (ṭīkās with no PTS roman edition)

- **Vinaya Sāratthadīpanī** (`vin*t`) and **Abhidhamma Mūlaṭīkā** (`abh*t`):
  no PTS roman edition, so no PTS volume structure to align to.
- **AN ṭīkā nipātas 3–11** (rest of `s0402t`, `s0403t`, `s0404t`): beyond the
  PTS Sāratthamañjūsā's coverage (which stops at Duka, nipāta 2).
- Other Sutta ṭīkās (Majjhima `s02*t`, Saṃyutta `s03*t`, etc.): no PTS edition.
- The one remaining PTS sub-commentary, **Abhidhammatthavibhāvinī**, is on the
  medieval Abhidhammatthasaṅgaha (a non-canonical manual), not a canonical
  commentary, so it is not part of this canon/commentary edition.
- **Pañcappakaraṇaṭṭhakathā flag:** PTS also issued the Kathāvatthu commentary
  separately (Minayeff, *JPTS* 1889); CST fuses all five, so this is one unit.
