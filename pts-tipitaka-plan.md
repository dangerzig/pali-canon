# PTS-organized digital Tipiṭaka: scoped plan

Status: **planned, not started.** Captures a standalone scholarly artifact that
emerged from the JPTS register-paper work: a digital Tipiṭaka segmented at
**PTS volume boundaries**.

## What this is (and is NOT)

A digital text of the Pāli canon (and, ideally, its commentaries) **segmented
to match the volume boundaries of the Pali Text Society editions**, so that each
file corresponds to one PTS volume and PTS volume/page references resolve
directly.

It is **NOT** "the PTS edition." We are not reproducing PTS's readings; the PTS
edition has its own textual decisions and will differ in subtle ways from
whatever source text we use (CST/VRI or GRETIL). We align **structure** (volume
boundaries), not text. The artifact must be labelled accordingly, e.g.
`cst-text-pts-volumes`, never "PTS Tipiṭaka".

Why it is valuable: PTS volume-and-page numbers are the citation standard in
Pāli studies, yet an openly-available digital text aligned to PTS volume
structure is scarce — and for the **commentaries** it does not exist at all.

## Current state (what already exists)

- `pali-commentary/src/reorganise_pts.py` already PTS-organizes the **Sutta
  basket** of the CST/VRI text (suttas + their aṭṭhakathā + ṭīkā), splitting/
  merging VRI files at structural headings to match PTS volumes. This is the
  template.
- `pali-canon/data/gretil-pts/` (GRETIL / Dhammakaya digitization) **already
  provides the canonical Vinaya and Abhidhamma organized by PTS volume**, with
  `[page NNN]` markers that are the PTS page numbers (reset per volume):
  - Vinaya: mahavagga (I), cullavagga (II), suttavibhanga1/2 (III–IV),
    parivara (V) — all 5 volumes.
  - Abhidhamma: dhammasangani, vibhanga, dhatukatha, puggalapannatti,
    kathavatthu, yamaka1/2, patthana1/2/3, patthana_duka — all 7 books across
    their PTS volumes.
- GRETIL's **commentary** holdings are limited to the Samantapāsādikā and the
  Visuddhimagga (per the register paper's footnote). No other commentaries.

So the boundary data we feared we'd have to reverse-engineer **largely exists
for the canon** — GRETIL did it. The hard, novel part is the commentaries.

## Tiers of work (difficulty)

### Tier 1 — Canonical Vinaya + Abhidhamma (LOW; days)
The boundaries are known from GRETIL. Two implementation choices (decide first):
- **(A) all-GRETIL**: use GRETIL's PTS-based text directly for all baskets → a
  consistent PTS-text edition. Downside: switches the canon away from the CST
  text the register paper uses (inconsistent with `raw-pts`).
- **(B) CST-text + GRETIL boundaries (recommended)**: keep CST/VRI text
  everywhere; use GRETIL's volume files and `[page NNN]` markers as the
  reference to locate the PTS volume split points in the CST Vinaya/Abhidhamma,
  then split with the `reorganise_pts.py` machinery. Consistent CST text,
  PTS-organized. The work is aligning CST structural divisions to GRETIL's
  volume/page boundaries (a one-time matching per text).

### Tier 2 — Sutta basket consistency check (LOW)
The existing Sutta reorganization split on structural headings, NOT PTS markers.
Cross-check it against GRETIL's Sutta volume/page markers (`an_vol1..`, etc.) to
confirm the boundaries are PTS-correct, and fix any that drifted. This also
retro-validates the register paper's `raw-pts`.

### Tier 3 — Commentaries + sub-commentaries for Vinaya/Abhidhamma (HARD; the prize)
No GRETIL boundaries. For each aṭṭhakathā/ṭīkā (Samantapāsādikā and its ṭīkā;
Atthasālinī, Sammohavinodanī, Pañcappakaraṇaṭṭhakathā, etc.) we need the PTS
volume ToC and must locate split points in the CST text and verify. This is the
genuinely novel scholarly contribution (no open PTS-organized digital
commentaries exist) and the bulk of the effort. Source the boundaries from PTS
catalogues / von Hinüber's Handbook / the PTS volumes themselves.

## Key decisions to make first
1. **Source text**: CST-text + GRETIL boundaries (B), or all-GRETIL (A).
   Recommend B for consistency with the register paper and because CST is the
   fuller, better-maintained text.
2. **Scope**: canon-only first (Tiers 1–2, near-term, high feasibility), with
   commentaries (Tier 3) as a separate follow-on — or commit to the whole thing.
3. **Identity vs the register corpus**: this artifact would *supersede* the
   ad-hoc `raw-full` cross-piṭaka corpus. If built, the register paper's
   cross-piṭaka experiment should consume it (uniform PTS organization across
   all baskets), removing the current Sutta-PTS / Vinaya-Abhidhamma-VRI mismatch.

## Verification plan (mirror the sandhi-edition rigor)
- Every PTS volume boundary must be justified by a GRETIL marker (Tiers 1–2) or
  a cited PTS ToC (Tier 3); record the source per boundary.
- Token-count / no-text-loss check on every split (sum of pieces == original).
- Round-trip: concatenating the PTS volumes of a text reproduces the source text.
- Spot-check a sample of volume start/end points against the PTS edition (or
  GRETIL page markers) by eye.

## Effort estimate
- Tiers 1–2 (canon, PTS-organized, CST text): ~a few days, mostly mechanical.
- Tier 3 (commentaries): weeks; reference-data assembly + verification dominate.

## Relationship to the register paper
Not required for the register paper. If built, it improves the secondary
cross-piṭaka analysis (uniform organization) and could be cited as a released
resource. The register paper's headline (107-doc Sutta `raw-pts`) is unchanged.

## Definition of done (canon phase)
A reproducible builder that emits the CST canonical Tipiṭaka split into
PTS-volume files (all three baskets) with a per-boundary provenance record and
passing verification; named honestly (`cst-text-pts-volumes` or similar); the
cross-piṭaka experiment switched to consume it.
