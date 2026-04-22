# Evaluation summary

Dataset at `dataset.jsonl`. Full run artefacts in `runs/2026-04-21T085610Z/`. Build arc in `docs/journey.md`.

## Topline

- **45 schema-valid rows** (15 A, 15 B, 15 C). Generator: Claude Sonnet 4.6. Judge: Claude Opus 4.7.
- **Total cost: ~$14.55** across 3 generation rounds. 1.8h wall.
- **Independent PS-criteria audit: 43/45 pass (96%)**. v1 was 31/45 (69%) — fix arc documented.
- **Judge-validation: 100% injected-failure catch rate** on 10 committed hand-labels.

## Composite by category (own judges, 1–5)

| Category | Mean | Range | n |
|---|---|---|---|
| A | 4.93 | 4.86–5.00 | 15 |
| B | 4.78 | 4.64–4.91 | 15 |
| C | 4.83 | 4.60–4.90 | 15 |

B lowest by design — the hardest category. A is at ceiling because the structural validator filters aggressively before the judge sees anything. Raw per-dim scores + distributions in `runs/2026-04-21T085610Z/metrics.json` + `judge_validation.md`.

## Independent audit (PS criteria verbatim)

| Round | A | B | C | Total |
|---|---|---|---|---|
| v1 | 14 | 2 | 15 | 31 / 45 |
| v2 | 15 | 10 | 15 | 40 / 45 |
| v3 | 15 | 13 | 15 | **43 / 45** |

Each round dropped the previous audit's flagged rows, patched the generator that produced them, regenerated. Details per row in `audit/ps_category_audit_v3.md`.

The 2 remaining B fails and their specific root causes are named in `failure_catalogue.md`.

## Judge validation

10 hand-labelled items (committed `eval/hand_labels.jsonl`) — 5 plausibly-good + 5 with injected known failures (wrong citation, paraphrased excerpt, vague clarifier, confident C answer, missing escalation). Judge scored blind.

- Injected-failure catch rate: **100%** (5/5)
- Best-agreement dims (κ = 1.00): `citation_accuracy.*`, `clarifier_quality.not_vague`, `ambiguity_framing.avoids_confident_answer`
- Worst-agreement dim: `ambiguity_framing.recommends_escalation` (κ = 0.52) — judge over-credits soft escalation

## Self-identified weaknesses

Listed in `failure_catalogue.md` with concrete code/rubric fixes per failing dimension, not placeholders. The biggest remaining gap: the judge's `recommends_escalation` rubric is softer than PS-level strictness — it would need to require a named mechanism, not just a recipient.

## Reproducibility

- Source: pinned HTML + cleaned Markdown in `data/razorpay_tos.*`, SHA in `razorpay_tos.meta.json`.
- Clause map: hand-curated, 80 entries, substring-validated.
- Seeds: `--seed 42` initial; `1000 + ord(cat)` and `3000` for the two regen rounds.
- Generators: `temperature=0.7`, per-candidate deterministic sub-seed.
- Judges: `temperature=0` (model-side nondeterminism remains).

Full determinism table in `README.md`.
