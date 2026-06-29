# Critical-edition JSON schema (v1)

Produced by `src/build_critical_edition.py` into
`data/critical/<nikaya>/<id>_critical.json`, assembled from the per-sutta
collation files under `data/collation/`. Each file is a critical *apparatus* for
one text: at every position where the witnesses diverge it records the readings,
the selected reading, and the evidence/confidence for that choice.

## Top-level object

| field | type | description |
|---|---|---|
| `id` | string | edition id, e.g. `dn1` |
| `schema_version` | int | currently `1` |
| `nikaya` | string | collection code (`DN`, `MN`, …) |
| `witnesses` | string[] | witnesses present, e.g. `["GRETIL/PTS","SC","VRI","BJT","Thai"]` |
| `word_counts` | object | token count per witness (`gretil`, `sc`, `vri`, `bjt`, `thai`) |
| `apparatus_count` | int | number of apparatus entries |
| `apparatus` | object[] | the apparatus entries (below), sorted by `position` |
| `provenance` | object | how this edition was produced (below) |

Positions where all witnesses agree carry no apparatus entry — the apparatus
records only divergences (errors, variants, and uncertain readings).

## Apparatus entry

| field | type | description |
|---|---|---|
| `position` | int | token position in the aligned text |
| `type` | string | `error` (PTS reading invalid), `variant` (genuine textual variant), or one of the `uncertain` types (`pts_addition`, `pts_omission`, alignment artefacts) |
| `selected` | string\|null | the chosen reading for the critical text |
| `confidence` | float | 0–1 confidence in the selection |
| `witnesses` | object | each witness's reading (`gretil`/`sc`/`vri`/`bjt`/`thai`), `null` if absent at this position |
| `rejected` | string[] | distinct attested readings other than `selected` |
| `notes` | string | human-readable justification |

## Provenance

| field | type | description |
|---|---|---|
| `generated_at` | string | ISO-8601 UTC build time |
| `builder` | string | `build_critical_edition.py` |
| `collation_source` | string | repo-relative path of the source collation file |
| `dpd_validation_source` | string\|null | DPD source used to validate readings (see `collate_nikaya.get_dpd_validation_source`) |
| `collation_stats` | object | counts from collation: `total_positions`, `orthographic`, `errors`, `variants`, `uncertain`, `match`, … |

## Not yet included (follow-up)

A single reconstructed *running* critical text (base token stream with the
selected readings applied) is a presentation layer on top of this apparatus and
is not emitted yet; it requires mapping apparatus positions back onto a base
witness's token sequence.
