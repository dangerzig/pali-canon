# Plan: organize the commentaries (aṭṭhakathā) by PTS volume

Companion to `pts-tipitaka-plan.md`. Same method as the canon: take the
**CST/VRI commentary text** and segment it to **PTS volume boundaries**, using
**GRETIL's PTS-paginated digitization** as the boundary reference. This aligns
*structure* (volume boundaries), not text — it is not the PTS edition's readings.

## What's already done

The **Sutta-piṭaka commentaries are already PTS-organized** in
`pali-commentary/data/raw-pts` (45 `.att` files), split into numbered PTS
volumes by `reorganise_pts.py` (e.g. `jaa1`–`jaa6` = Jātaka-aṭṭhakathā 6 vols,
`mna1`–`mna5` = Papañcasūdanī, `dhpa1`–`dhpa4` = Dhammapada-aṭṭhakathā, plus DN
comm `s010xa`, KN comms `s05xxa`, Manorathapūraṇī `mp1`–`mp5`, etc.). They ride
along into `pts-canon` only when we add a commentary basket; for now they sit in
raw-pts. **No further work needed on Sutta commentaries** beyond the same
GRETIL cross-check we owe the Sutta canon volumes.

So this plan covers only the **Vinaya and Abhidhamma commentaries**, whose CST
files live in `pali-canon/data/vri-raw` and are *not* yet PTS-organized.

## The commentaries to organize (CST source → PTS target)

CST file → division was read directly from each file's closing colophon.

### Vinaya — Samantapāsādikā (Buddhaghosa, comm. on the whole Vinaya)

CST: 5 files. PTS: **7 text volumes** (I–VII), ed. Takakusu & Nagai 1924–47
(Vol VIII = Kopp's indexes, 1977, no text). PTS pages run **continuously
1→~1535** across the 7 volumes.

| CST file | words | covers (colophon) | PTS target |
|---|---|---|---|
| `vin01a`  | 130,216 | Pārājikakaṇḍa-aṭṭhakathā (Bhikkhuvibhaṅga: Pārājika→Nissaggiya) | **Vols I, II, III** + into IV |
| `vin02a1` | 40,461 | rest of Ubhatovibhaṅga (Pācittiya … → Bhikkhunīvibhaṅga) | **Vol IV** (with vin01a tail) |
| `vin02a2` | 39,978 | Mahāvagga-aṭṭhakathā | **Vol V** (pp.951–1154) — clean 1:1 |
| `vin02a3` | 25,184 | Cūḷavagga-aṭṭhakathā | **Vol VI** (pp.1155–~) — clean 1:1 |
| `vin02a4` | 22,988 | Parivāra-aṭṭhakathā (closes the Samantapāsādikā) | **Vol VII** — clean 1:1 |

**Difficulty: the Suttavibhaṅga commentary (Vols I–IV) is the hard part.** The
3 internal boundaries — Vol I|II (≈ PTS p.285), II|III (≈ p.517), III|IV
(≈ p.735) — all fall **mid-CST-file** (Vols I–III are entirely inside `vin01a`;
the III|IV split and the `vin01a`→`vin02a1` join both land inside Vol IV). These
must be located in the CST text via GRETIL's `samp_Npu` page markers, exactly
like the canon's Kathāvatthu/Paṭṭhāna splits.

**Vols V, VI, VII are clean** — each equals one CST file (Mahāvagga, Cūḷavagga,
Parivāra commentary respectively), confirmed by colophon. These map 1:1 with no
mid-file split, like the Vinaya mūla volumes.

### Abhidhamma — three commentaries, all effectively 1:1

| CST file | words | commentary (colophon) | comments on | PTS edition | mapping |
|---|---|---|---|---|---|
| `abh01a` | 81,144 | **Atthasālinī** (Dhammasaṅgaha-aṭṭhakathā) | Dhammasaṅgaṇī | 1 vol, Müller 1897 (rev. Cousins 1979) | **1:1** |
| `abh02a` | 91,446 | **Sammohavinodanī** (Vibhaṅga-aṭṭhakathā) | Vibhaṅga | 1 vol, Buddhadatta 1923 (550 pp.) | **1:1** |
| `abh03a` | 85,671 | **Pañcappakaraṇaṭṭhakathā** (Abhidhammapiṭaka-aṭṭhakathā) | the remaining 5 books (Dhātukathā, Puggalapaññatti, Kathāvatthu, Yamaka, Paṭṭhāna) | 1 vol, Buddhadatta 1956 | **1:1**, with flag |

Each Abhidhamma commentary file = one PTS volume. No mid-file boundaries to find.
**Flag** on `abh03a`: PTS also issued the Kathāvatthu commentary separately
(Kathāvatthuppakaraṇa-aṭṭhakathā, Minayeff, *JPTS* 1889); CST keeps all five
commentaries fused in one file, so we emit one unit and note the alternative.

## Out of scope: the ṭīkās (sub-commentaries)

The CST also has the sub-commentaries — Vinaya **Sāratthadīpanī** (`vin01t1`,
`vin01t2`, `vin02t`) and the Abhidhamma **Mūlaṭīkā** (`abh01t`, `abh02t`,
`abh03t`). **PTS never published these in roman script**, so there is no PTS
volume structure to align them to. They are excluded from the PTS-organized
edition (they can only be kept in their native CST structure, which is a
different artifact). Same goes for any ṭīkā lacking a PTS roman edition.

## Boundary source

GRETIL hosts the **Samantapāsādikā by PTS volume** online:
`gretil.sub.uni-goettingen.de/gretil/2_pali/4_comm/samp_1pu.htm` … `samp_7pu.htm`
(plain) and `samp_1ou`…`samp_7ou` (annotated), carrying PTS page markers — the
same source family used for the canon. **Not** in the local `gretil-pts` mirror
(canon only), so the 7 `samp` files must be downloaded for the Vinaya commentary.
The Abhidhamma commentaries are 1:1 and need no GRETIL boundary file (only an
optional page-count sanity check).

## Build plan (proposed order, easy → hard)

1. **Abhidhamma commentaries (3 volumes, 1:1).** Extend the `ONE_TO_ONE`
   pattern from `build_pts_canon.py`: `abh01a`→Atthasālinī, `abh02a`→
   Sammohavinodanī, `abh03a`→Pañcappakaraṇaṭṭhakathā. Trivial; ship first.
2. **Vinaya commentary Vols V–VII (3 volumes, 1:1).** `vin02a2`→Vol V
   (Mahāvagga-aṭṭh.), `vin02a3`→Vol VI (Cūḷavagga-aṭṭh.), `vin02a4`→Vol VII
   (Parivāra-aṭṭh.). Colophon-confirmed; also 1:1.
3. **Vinaya commentary Vols I–IV (the Suttavibhaṅga aṭṭhakathā).** Download
   `samp_1pu`–`samp_4pu`, extract their PTS span / opening lemma, and locate the
   three cut points (Vol I|II, II|III, III|IV) inside `vin01a`+`vin02a1` by
   matching GRETIL volume-edge text to the CST text (anchor-phrase search, the
   Yamaka-Cittayamaka method). Emit Vols I–IV. **Flag** any boundary not
   crisply anchored, as we did for Paṭṭhāna.
4. **Verify** (per canon convention): per-basket text-conservation assertion
   (output words == CST source words, no loss); colophon match for the 1:1
   volumes; GRETIL volume-edge match for the four split Vinaya volumes; record
   provenance + boundary basis per volume in the manifest.
5. **Decide packaging:** add a `commentary` basket to `pts-canon` (alongside the
   already-PTS Sutta `.att`), or keep commentaries in a sibling `pts-commentary`
   dir. Lean sibling dir to keep "canon v1" clean and versioned separately.

## Effort estimate

- Steps 1–2 (six 1:1 volumes): quick, mirrors existing `ONE_TO_ONE` code.
- Step 3 (four split Vinaya volumes): the real work — download 4 GRETIL files,
  build the anchor-matching, verify 3 cut points. Comparable to the canon's
  Yamaka + Kathāvatthu boundary work combined.
- ṭīkās: none (out of scope).

Net: the commentary edition is **mostly 1:1** (9 of 13 Vin/Abh commentary
volumes map cleanly: 3 Abhidhamma + Vinaya Vols V–VII = 6 clean, plus the Sutta
commentaries already done). Only **4 Vinaya volumes** (the Suttavibhaṅga
aṭṭhakathā, Vols I–IV) need GRETIL-driven mid-file boundary location.
