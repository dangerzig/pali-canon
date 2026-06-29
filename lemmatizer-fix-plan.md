# Lemmatizer fix: scoped plan

Status: **planned, not started.** `src/lemmatize_canon.py` is currently at its
original (unmodified) state; two trial fixes were attempted and fully reverted
on 2026-06-28 after blast-radius measurement showed they were unsafe. This
document scopes a proper, audited fix.

## Motivation

While building the sandhi-resolved edition for the JPTS register paper
("Two Registers of Pāli Prose"), two genuine bugs surfaced in the shared
lemmatizer. They are small in volume but real, and the lemmatizer feeds the
2023 WSC paper, the `pali-strata` stratification paper, and the register
paper's robustness check, so a fix is worth doing carefully.

## The two bugs (precisely characterised)

### Bug A — spurious quotative splits
`_process_dpd_result` accepts DPD's first `deconstructor` value unconditionally,
*before* trying the headword. DPD sometimes offers a phonologically impossible
`host + iti` split for a word that is itself a finite verb:

- `jānāti` ("knows", pr) → split as `jānaṃ + iti`. But `jānaṃ + iti` would
  surface as `jānanti` or `jānamiti`, never `jānāti`. The split is impossible.

Volume: ~1,300 tokens (≈0.06% of the canon), the `jānāti`/`atthīti` class.

### Bug B — homograph lemma misselection
`_apply_headword_to_token` always takes `headword_ids[0]`. For most words this
is correct (the stem lemma is listed first), but for a few homographs the wrong
reading is first:

- `jānāti`: headwords list `ja` (adj) **before** `jānāti` (pr), so the verb is
  lemmatised as the adjective `ja`. The correct verb headwords (`jānāti 1/2/3/4`,
  pr) exist in the list but are not selected.

This is the bug that actually corrupts `jānāti`'s lemma; Bug A only stops the
spurious split.

## What we learned (why naive fixes fail)

Measured against the existing `data/lemmatized/` (138,431 distinct words,
2,268,987 tokens):

- **Naive Bug B fix** ("prefer the headword whose lemma == the word"):
  **catastrophic — changed 18% of all tokens, almost all WRONG.** DPD's
  `headword[0]` is correct for the common case, so this broke every pronoun and
  inflected form: `so`→`so` (should be `ta`), `taṃ`→`taṃ` (`ta`), `me`→`me`
  (`ahaṃ`), `bhagavā`→`bhagavā` (`bhagavant`). `jānāti` is the rare exception,
  not the rule.
- **Naive Bug A fix** (reject `…+iti` when ṃ-host and word doesn't end `nti`):
  ~0.09% of tokens, but **over-rejected** valid splits — `ṃ + iti` also
  surfaces as `…miti` (`vimuttaṃ + iti` → `vimuttamiti`) and lengthened `…ntī`
  (`desessantī`), which the guard wrongly killed. Roughly a wash.

Conclusion: both fixes must be far more precise, and **blast radius must be
measured before any regeneration.**

## Proper fix design

### Bug A — reconstruction-based guard (zero false positives)
Replace the "ends in nti" heuristic with a real forward-sandhi reconstruction:
accept a `host + iti` deconstruction only if `sandhi(host, iti)` can produce the
surface word, enumerating all legitimate outcomes:
- vowel-final host: final short vowel lengthens (`hoti`+`iti`→`hotīti`), or
  `o`/`e` host absorbs the `i` (`gammo`+`iti`→`gammoti`); allow the metrically
  lengthened variant too.
- niggahīta-final host: `ṃ + iti` → `…nti` **or** `…miti` (both attested);
  allow lengthened finals.
Reject only when no legitimate outcome matches the word (this rejects
`jānaṃ + iti` for `jānāti`, but keeps `vimuttaṃ + iti` for `vimuttamiti`).
Reuse the validated `peel_reconstructs` logic from
`pali-commentary/src/build_sandhi_edition.py`.

Acceptance: on the corpus, every *rejected* split must be genuinely
non-reconstructing, and every *accepted* split must reconstruct. Target the
`jānāti`/`atthīti` class with **zero** false rejections.

### Bug B — targeted homograph override (POS-gated)
Do NOT use a blanket "lemma == word." Override `headword[0]` only when ALL hold:
1. the word exactly matches a candidate headword's cleaned lemma (its own
   citation form), AND
2. that candidate is a **finite verb** (pos in pr/aor/fut/imp/opt/cond/perf/
   imperf), AND
3. the current `headword[0]` is **not** a finite verb (a non-verb homograph).
This fixes `jānāti` (verb vs adj) while leaving every pronoun/noun case
(`so`, `me`, `taṃ`, `bhagavā` — none of which are verb homographs) untouched.

Acceptance: blast radius restricted to verb-class homographs; **zero** changes
to the pronoun/common-noun forms that the naive fix broke (verify against an
explicit hold-out list: so, taṃ, me, bhagavā, ayaṃ, yo, ahaṃ, …).

## Audit plan (mirror the sandhi-edition rigor)

1. Re-lemmatize the full vocabulary with the fixed code; diff against existing
   `data/lemmatized/` per-type and per-token. Separate *intended* changes
   (`jānāti`-class) from *any* regressions.
2. Confirm the hold-out common-forms list is unchanged.
3. Manually review a stratified random sample of changed types.
4. Acceptance criteria, all required:
   - Bug A: 100% of accepted quotative splits reconstruct; jānāti-class no
     longer split.
   - Bug B: jānāti-class lemmas corrected to the verb; zero pronoun/noun
     regressions.
   - Total token change < ~0.2% and every changed type accounted for.

## Regeneration + downstream re-verification

Work on a branch in `~/pali-canon`; preserve the current `data/lemmatized/`
(copy aside) for diffing and rollback.

1. Regenerate: `data/lemmatized/`, `pali-commentary/data/lemmatized` and
   `lemmatized-pts` (the commentary lemmatizer wraps this same pipeline).
2. **Register paper**: re-run the lemmatised 99→98% check
   (`pali-commentary` exp); confirm unchanged or update the paper number.
3. **pali-strata**: re-run its analyses on the new lemmatised data; check the
   stratification results are stable; update if needed.
4. **2023 WSC paper**: published — no re-run, but note in its repo that the
   lemmatiser was corrected post-publication.

## Risks / rollback
- Branch + preserved old data → trivial rollback.
- Do not regenerate until the audit acceptance criteria pass.
- Keep the fix minimal and POS-gated; resist scope creep into general
  homograph disambiguation.

## Definition of done
Fixed `lemmatize_canon.py` on a merged branch; regenerated lemmatised data;
register paper's lemmatised number re-verified; pali-strata re-run and stable;
audit report committed alongside the code.
