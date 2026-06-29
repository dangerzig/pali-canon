# Lemmatizer fix audit: quotative splits + verb homographs

Branch: `lemmatizer-quotative-homograph-fix`. Implements the two fixes scoped in
`lemmatizer-fix-plan.md` and audits their blast radius before regeneration.

## What changed in `src/lemmatize_canon.py`

1. **Bug A — reconstruction-based quotative guard.** A two-piece `host + iti`
   DPD deconstruction is now accepted only if forward sandhi of `host + iti` can
   actually produce the surface word (`_iti_surface_forms` / `_select_deconstruction`).
   This rejects DPD's phonologically impossible `jānaṃ + iti` for the verb
   `jānāti` (which would surface as `jānanti`/`jānamiti`), while keeping valid
   quotatives (`vimuttaṃ + iti` → `vimuttamiti`, `hoti + iti` → `hotīti`). When
   the primary deconstruction is a quotative split, the first quotative
   alternative that reconstructs wins (`atthā+iti` rejected → `atthī+iti` for
   `atthīti`); no reconstructing split is ever dropped, and we never fall back to
   a non-quotative alternative the primary outranks (avoids `visesīti` →
   bogus `vise + asīti`). If no quotative split reconstructs, fall through to
   headword lookup.

2. **Bug B — POS-gated homograph override.** `_apply_headword_to_token` overrides
   DPD's first-listed headword only when ALL hold: headword[0] is not itself a
   finite verb; headword[0]'s lemma is not this surface (so a word that is its
   own first-class noun/participle citation keeps that reading); the surface is a
   present `-ti`/`-tī` form; and a later headword is a present verb (`pos == pr`)
   whose lemma is the surface (or its metrically-shortened final). This fixes
   `jānāti` (listed under adj `ja` before verb `jānāti`) without touching
   pronouns/nouns.

The naive forms of both fixes were rejected during planning (Bug B naive form
changed 18% of tokens; Bug A naive ṃ-guard over-rejected). The tightenings here
are justified by the blast-radius measurement below — in particular Bug B was
narrowed from "any finite verb" to "present verb whose surface is not already a
first-class citation", because the broad form mis-tagged hundreds of common
nouns/pronouns that are homographs of aorist/optative entries (`muni`, `sappi`,
`assa`, `bhave`, `assaji`, …).

## Audit method

Per-word lemmatization is deterministic and cached, so a per-type diff weighted
by corpus frequency fully determines the per-token diff. The on-disk
`data/lemmatized/` was found to predate the current DPD (e.g. `brāhmaṇosmī` is
split there but has no row in the current DPD), so it would conflate unrelated
drift. The audit therefore compares **old code vs new code on the same current
DPD**, over the full corpus vocabulary (153,715 distinct words, 2,847,446
tokens) extracted from `data/lemmatized/`.

Method (run with throwaway harnesses, not committed): dump every vocabulary
word's `(lemma, pos, root, sandhi)` under the new code; `git stash` the fix and
dump again under the old code; diff the two dumps weighted by corpus frequency;
and assert the Bug A invariants (every accepted quotative split reconstructs via
`_iti_surface_forms`; no reconstructing split dropped except the intended -nti
verbs). Re-running the dumps reproduces the numbers below exactly.

## Results (clean old-code vs new-code, same DPD)

- **Changed types: 90 (0.059%). Changed tokens: 2,305 (0.0809%)** — under the
  plan's ~0.2% ceiling.
- **Hold-out common forms unchanged:** so, taṃ, me, bhagavā, ayaṃ, yo, ahaṃ,
  tvaṃ, naṃ, tena, tassa, imaṃ, yaṃ, kiṃ, no, vo, mayaṃ, etaṃ, idaṃ, assa,
  muni, sappi, joti, bhave, namhi — all identical to baseline.

| category | types | tokens | nature |
|---|---|---|---|
| sandhi → lemma (split rejected) | 11 | 1,639 | `jānāti` (1592) + `jānātī` (37) corrected to verb; rest f≤2, sensible base lemma |
| sandhi host changed | 69 | 527 | non-reconstructing host replaced by a reconstructing one (mostly `-āna+iti` → `-āni+iti`, the neuter plural before iti) |
| lemma/pos changed | 10 | 139 | present verbs un-mistagged: maññatī, ramatī, pareti, jāyatī, pekkheti, nadatī, bhavatī, sumbhati, nibbattatī, niccharatī |

### Bug A invariants (verified by `_verify_bugA.py`)
- Accepted two-piece quotative splits in the new output: **4,175; non-reconstructing: 0.**
- Changes that dropped a *reconstructing* old split: **0.** (Every host change
  replaced a non-reconstructing host with a reconstructing one — a strict
  improvement.)

### Bug B
- All 10 lemma/pos changes are genuine present verbs previously mistagged as
  participle/adj/noun/pronoun. **Zero pronoun/common-noun regressions.**

## Acceptance criteria (all met)
- Bug A: 100% of accepted quotative splits reconstruct; `jānāti`-class no longer
  split. ✓
- Bug B: `jānāti`-class corrected to the verb; zero pronoun/noun regressions. ✓
- Total token change 0.0809% < 0.2%; every changed type accounted for. ✓

## Known limitation / out of scope: the `-nti` finite-verb class

The reconstruction guard cannot, by design, catch a *different* pre-existing
class: surface words that are themselves **finite verbs ending in `-nti`** for
which DPD offers a `…ṃ + iti` deconstruction that *does* reconstruct. Example:
`santi` ("they are", 3pl pr) → DPD `["saṃ + iti"]`, and `saṃ + iti` legitimately
surfaces as `santi`, so the split is phonologically valid and is accepted — even
though `santi` is overwhelmingly the verb. Measured: **99 types / 1,817 tokens**
of `-nti` words split as quotatives whose surface is a DPD finite verb (largest:
`santi` 760, `bhavissanti` 449, `siyanti` 144, `gamissanti` 39, `desessanti` 26).

These are **pre-existing** (unchanged by this fix) and were not in scope (the
plan explicitly resists scope creep into general homograph disambiguation).
Fixing them would require POS-gating the *sandhi* decision (reject a quotative
split when the surface is itself a finite verb and the host is not), analogous to
the `ambiguous` guard in `pali-commentary/src/build_sandhi_edition.py`, with its
own audit. Recommended as a separate follow-up.
