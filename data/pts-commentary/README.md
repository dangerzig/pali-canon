# CST commentaries (aṭṭhakathā), organized by PTS volumes

The **Chaṭṭha Saṅgāyana (CST/VRI) text** of the Vinaya & Abhidhamma
commentaries, **segmented to match Pali Text Society volume boundaries**. As
with the canon (`../pts-canon`), this aligns *structure* (volume boundaries),
**not text** — it is not the PTS edition's readings. Build:
`../../build_pts_commentary.py`. Plan: `../../commentary-pts-plan.md`. Provenance
per volume: `MANIFEST.csv`.

The **Sutta commentaries** are PTS-organized separately, in
`pali-commentary/data/raw-pts` (`.att` files), and are not duplicated here.

## Contents (10 volumes — the complete Vinaya & Abhidhamma aṭṭhakathā)

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

- **Text conservation: PASS** — output words == CST source words (514,421). No
  text lost (asserted globally; the vin01a 3-way split is also checked to sum
  exactly).
- **1:1 colophon-confirmed: PASS** — each 1:1 source ends with its expected
  division colophon (e.g. `Mahāvagga-aṭṭhakathā niṭṭhitā`).
- **Split anchors: PASS** — each anchor occurs exactly once; Vol II opens at the
  2nd Pārājika, Vol III opens at the Saṅghādisesa and ends at the Nissaggiya
  colophon.

## Out of scope

- **ṭīkās** (Vinaya Sāratthadīpanī, Abhidhamma Mūlaṭīkā): these two have **no PTS
  roman edition**, so there is no PTS volume structure to align to. (PTS *did*
  publish a few sub-commentaries — Dīgha Līnatthapakāsinī, 3 vols; Aṅguttara
  Sāratthamañjūsā, 3 vols but only the first 7 nipātas; Abhidhammatthavibhāvinī
  on the medieval Saṅgaha — all Sutta-side or on a non-canonical manual, none on
  the Vinaya/Abhidhamma commentaries here. The DN/AN ṭīkās could be
  PTS-organized later if desired.)
- **Pañcappakaraṇaṭṭhakathā flag:** PTS also issued the Kathāvatthu commentary
  separately (Minayeff, *JPTS* 1889); CST fuses all five, so this is one unit.
