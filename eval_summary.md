# Evaluation summary

Dataset at `dataset.jsonl`. Run artefacts in `runs/2026-04-22-v4/`. Full build arc in `docs/journey.md`.

## Topline

- **45 schema-valid rows** (15 A, 15 B, 15 C). Generator: Claude Sonnet 4.6. Judge: Claude Opus 4.7.
- **Total cost: ~$35** across four generation rounds (v1 + three fix-regen rounds; see `docs/journey.md` for per-round breakdown).
- **Independent PS-criteria audit: 44/45 (97.8%)**. v1 was 31/45 (69%); fix arc documented.
- **Judge-validation: 100% injected-failure catch rate** on 10 committed hand-labels.
- **Source coverage: 100%** of the Razorpay ToS is indexed in the clause map (151 entries); real PageIndex tree built via VectifyAI's open-source library.

## Composite by category (own judges, 1–5)

| Category | Mean | Range | n |
|---|---|---|---|
| A | 4.91 | 4.86–5.00 | 15 |
| B | 4.83 | 4.64–4.91 | 15 |
| C | 4.67 | 4.50–4.90 | 15 |

C's mean dropped from v3 (4.86 → 4.67) because v4's seeds reach further into previously-uncovered parts of the ToS (e-mandate, TokenHQ, RTO, cross-border) where the silence-vs-specification boundaries are harder; v3 was topically concentrated on the well-trodden fees/suspension area.

## Independent audit (PS criteria verbatim — not the project's own judges)

| Round | A | B | C | Total | Key fix |
|---|---|---|---|---|---|
| v1 | 14 | 2 | 15 | 31 / 45 | initial run |
| v2 | 15 | 10 | 15 | 40 / 45 | load-bearing-axis CoT; unique regen seeds; exclusion sets |
| v3 | 15 | 13 | 15 | 43 / 45 | axis-first construction; forbid pre-revealed axis |
| **v4** | **15** | **14** | **15** | **44 / 45** | real PageIndex tree + 100% ToS coverage + regen on 151-clause pool |

Each round dropped the previous audit's flagged rows, patched the generator that produced them, regenerated. Per-row details in `audit/ps_category_audit_v4.md`; delta vs prior rounds in `audit/improvement_delta.md`.

The one remaining B fail (B-004) is the "concurrent obligations presented as alternatives" class — both clauses bind every merchant simultaneously, so a Cat A answer listing both resolves the question. This class has survived one slot per round (v2 B-007 → v3 B-015 → v4 B-004) — the prompt needs a 4th guard clause for it.

## Judge validation

10 hand-labelled items in `eval/hand_labels.jsonl` — 5 plausibly-good + 5 with injected known failures (wrong citation, paraphrased excerpt, vague clarifier, confident C answer, missing escalation). Judges scored blind.

- Injected-failure catch rate: **100%** (5/5)
- Best-agreement dims (κ = 1.00): `citation_accuracy.*`, `clarifier_quality.not_vague`, `ambiguity_framing.avoids_confident_answer`
- Worst-agreement dim: `ambiguity_framing.recommends_escalation` (κ = 0.52) — judge over-credits soft escalation language

## Source + tree provenance

- **Razorpay ToS**: 150,946 chars / 1,040 MD lines, fetched from razorpay.com/terms via `tools/fetch_tos.py`, pinned with SHA-256 in `data/razorpay_tos.meta.json`.
- **Clause map** (`data/clause_map.json`): 151 entries, 100% line coverage (all 1,040 lines; every non-blank content line is inside a clause). Built as a merge of: (i) 80 hand-curated sub-clause entries (the high-granularity slice); (ii) 16 section-level entries from the real PageIndex tree; (iii) 55 gap-fill entries for remaining uncovered line ranges. Every `verbatim_text` is a literal substring of the source MD — substring-validation in `tools/clause_map_check.py`.
- **PageIndex tree** (`data/pageindex_tree.json`): built via **VectifyAI's open-source PageIndex library** (not the hosted API client). 41 section nodes, 99.9% text coverage, 41/41 titles verified correct against source line numbers, monotonic line ordering, zero duplicate node texts. Tree depth is 1 (Parts → sections); sub-clause hierarchy lives in the clause map.

## Self-identified weaknesses

Surfaced in `failure_catalogue.md` with concrete code/rubric fixes per failing dimension:

1. **B-004** — concurrent-obligations-as-alternatives class. Prompt needs a 4th guard: "if both clauses impose overlapping binding obligations with no carve-out, reject."
2. **`ambiguity_framing.recommends_escalation`** — judge over-credits soft escalation language (κ = 0.52). Rubric should require a named mechanism (dashboard ticket, §18 written notice, RBI informal guidance), not just a recipient.
3. **A-006 / A-009** — near-duplicate questions on the same device-return clause. Pass individually but wasted slots. Validator should add a "near-duplicate by seed clause + question Jaccard" check.
4. **C-001 / C-005** — similar near-duplicate on PA-Guidelines §6 "promptly" ambiguity.
5. **Sub-clause hierarchy in PageIndex tree**: depth 1 only. Forcing a deeper recursion would require running PageIndex with lower token-per-node limit and ~$2 extra.

## Reproducibility

```bash
make setup && make fetch && make curate && make tree
export ANTHROPIC_API_KEY=...
make run                                                        # ~$8, ~40 min
python tools/topup.py --run-dir runs/<ts> --target-per-category 15   # fill deficits
```

Seeds used across rounds: `42` (v1), `1000 + ord(cat)` (v1 C topup), `2000` (v2 regen), `3000` (v3 regen), `5000` (v4 regen), `6000` (v4 B fix). Generators: `temperature=0.7`, per-candidate sub-seed. Judges: `temperature=0` on Opus 4.7. Full determinism table in `README.md`.
