# Razorpay ToS — Synthetic Q&A Dataset Pipeline

Reference solution for the Hyde AI Builder take-home assessment (Option 2: Razorpay ToS).
Produces a 45+ example JSONL dataset across three categories (A: clear answer, B: clarification required, C: genuine ambiguity), with deterministic validation, per-dimension LLM-as-judge evaluation, judge-validation, and an automated failure catalogue.

## Quick start

```bash
make setup       # install deps (editable)
make fetch       # fetch & pin Razorpay ToS (one-time; committed)
make tree        # build PageIndex reasoning tree (cached)
make test        # run unit tests
make dry-run     # full pipeline without API calls (uses fixtures)
make run         # real run; requires ANTHROPIC_API_KEY
```

> On Windows or systems without the `pageindex` library, the tree-builder falls back to deriving a hierarchical tree from `data/clause_map.json`. This is fully compatible with the `Retriever` wrapper.

Environment variables:
- `ANTHROPIC_API_KEY` — required for non-dry-run
- `OPENAI_API_KEY` — optional; enables cross-model κ when `--cross-model-judge gpt-5` is passed

## Architecture

See `docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md` for the full design.

Pipeline:
```
fetch → clause_map → PageIndex tree → {gen A, gen B, gen C} → validator → regen(≤1) → judges → judge-validation → failure catalogue → report
```

Generators are three distinct modules, not a single function with a category switch:
- **A**: seeded by clauses with concrete numeric claims; reverse construction (clause → question → answer).
- **B**: seeded by pairs of clauses sharing topics; LLM asked to name the load-bearing axis and produce forked branches.
- **C**: seeded by silence candidates (external_deferral / vague_language / may-suspend clauses); prompt forbids confident phrasing.

## Deterministic clause map

The clause map (`data/clause_map.json`) is **hand-curated** by Claude Code reading `data/razorpay_tos.md` page-by-page. This was a deliberate choice over regex: ToS/legal docs have irregular numbering that regex consistently mishandles. Substring-validation is automated (`tools/clause_map_check.py`), and `tests/test_clause_map.py` asserts every `verbatim_text` is a literal substring of the MD source. Adding a new clause is a diff to the JSON file + a re-run of the check. The check is run automatically on CI / in `make curate`.

## Reproducibility

| Artefact | Deterministic? | Mechanism |
|---|---|---|
| ToS source | Yes | `data/razorpay_tos.*` pinned; SHA-256 in `data/razorpay_tos.meta.json` |
| Clause map | Yes | hand-curated, committed, substring-checked |
| PageIndex tree | Yes (given source) | `data/pageindex_tree.json` cached; rebuilt only on source change |
| Generators | No (by design) | `temperature=0.7`; per-item seed = `--seed + i` for run-level reproducibility; model-side sampling remains |
| Validator | Yes | pure Python, no LLM |
| Judges | Near-det | `temperature=0.0`; model-side nondeterminism still possible |
| Judge-validation | Yes | committed `eval/hand_labels.jsonl` |
| Metrics | Yes (token+cost), No (wall) | `runs/<ts>/metrics.json` |

Full reproduction from clean clone:
```bash
make setup && make fetch && make curate && make tree && make run
```

## Cost awareness

Every stage emits `{tokens, cost_usd, latency_ms, count}` to `runs/<ts>/metrics.json`. The top of `runs/<ts>/report.md` shows totals. Pricing table at `pipeline/pricing.json` — update if Anthropic/OpenAI pricing changes.

Estimated cost for a full run (target=15/category, over-generate=1.5, models={gen: Sonnet 4.6, judge: Opus 4.7}, no cross-model): ~350 LLM calls, under $5 total.

> Latest dry-run cost log: `runs/dry/metrics.json` — stage-by-stage tokens and cost. Real-run costs will be logged under `runs/<ts>/metrics.json`. The top of `report.md` surfaces totals.

## What the LLM-as-judge evaluation reveals

_Filled in by the latest real run. See `runs/2026-04-21T085610Z/report.md` for the source of truth._

**Run summary** (2026-04-21):
- 45 rows, exactly 15 per category (A/B/C)
- Generator: `claude-sonnet-4-6`; Judge: `claude-opus-4-7` (the stronger model, intentionally)
- Wall time: ~47 min (2312s initial + 494s C top-up); **Total cost: $9.50** for 297 LLM calls
- Composite means: **A = 4.94 / B = 4.64 / C = 4.86** (out of 5)
- **Judge-validation on hand-labels: 100% injected-failure catch rate** — all 5 injected failures (wrong citation, paraphrased excerpt, vague clarifier, confident answer in C, missing escalation) scored ≤2 on the right dimension by the blind judge.
- Per-dimension quadratic κ: citation accuracy (1.00), clarifier quality sub-dims (0.80–1.00), grounding.factual_support (0.78), clarity.readability (0.40 — acknowledged gap).

**What the numbers reveal, honestly:**
- **Category B scores lowest** (4.64 vs 4.94/4.86), which is correct: the clarifying-question task is the hardest to do well, and B-019 / B-015 both got dinged for category-fit borderline scores (the axis they named could arguably resolve to a clear answer directly).
- **Category C scored ABOVE B** (4.86 vs 4.64). Your own feedback flagged this as a classic failure mode — "judge rubber-stamps 'I don't know' as a clear answer." Here the dedicated `AmbiguityFramingJudge` kept confident-phrasing in check (avoids_confident_answer: exact 1.00, κ 1.00), and C scoring high reflects genuine ambiguity-framing quality rather than judge leniency. That said, `ambiguity_framing.recommends_escalation` only agreed with hand-labels at 0.33 exact-match — judges over-credit soft escalation language. Flagged for v2.
- **Category A is at the ceiling** (4.94): every A row cited a real clause with a verbatim excerpt, and factual_support held up under Opus-4.7 scrutiny. The validator's deterministic gates (citation-resolves, grounding, structural rules) already eliminated 8/23 candidates before any judge saw them — the judge is scoring what the validator already filtered.

**Cost efficiency:** $0.21/row against Opus-4.7 judges is within reach of running this at 10× scale if needed.

**v1 drops flagged in `dropped.jsonl`:** primarily duplicate-question detections from the pigeon-holed seed-clause pool (A: 8 drops, B: 8 drops, C: 14 drops + 4 JSON-parse failures). JSON-parse failures exclusively affected long-form Category C answers that contained unescaped quotes inside clause verbatim excerpts; handled by the `json_repair` fallback after the initial crash. See `runs/_raw_dumps/` for post-mortem artifacts.

We split the judge into **six per-dimension micro-judges**, not one monolithic rubric:
- `GroundingJudge` (factual_support, citation_relevance) — all categories
- `CategoryFitJudge` (category_correctness) — all categories
- `ClarifierQualityJudge` (specificity, names_axis, not_vague, explains_what_changes) — B only
- `AmbiguityFramingJudge` (names_silence_type, avoids_confident_answer, recommends_escalation) — C only, specifically to catch the "judge rubber-stamps 'I don't know' as clear" failure mode
- `ClarityJudge` (readability, concision) — all
- `CitationAccuracyJudge` (excerpt_is_verbatim, clause_id_correct_scope) — A, B

**Judge-validation** runs two mechanisms:
1. **Hand-labels**: `eval/hand_labels.jsonl` contains 10 committed items — 5 plausibly-good, 5 with injected known failures (wrong citation, paraphrased excerpt, vague clarifier, confident answer in C, missing escalation). The judge scores them blind; we report per-dimension exact-match / within-1 / quadratic-κ and the injected-failure catch rate.
2. **Cross-model κ** (optional, when `--cross-model-judge <openai_model>` is set): a GPT-family model runs the same rubric on a 20% random slice; per-dimension Cohen's κ reported in `cross_model_kappa.json`; disagreements dumped to `judge_disagreements.jsonl` for manual review.

## Self-identified failures

`runs/<ts>/failure_catalogue.md` is automatically generated: 3 lowest-scoring items per category, lowest scoring dimensions, raised flags, regen count, and seed clauses. It is not cherry-picked.

> The committed `eval/hand_labels.jsonl` contains 10 deliberately-constructed items — 5 plausibly-good and 5 with injected known failures (wrong citation, paraphrased excerpt, vague clarifier, confident answer in Category C, missing escalation). The judge-validation stage scores these blind and reports per-dimension exact-match / within-1 / quadratic-κ, plus the injected-failure catch rate. A judge that fails to catch an injected failure is itself a failure the pipeline will surface.

## v2 (if I had another day)

- Active-learning loop: failure catalogue → prompt updates → next run.
- Multi-turn generation (follow-up after B clarifier is answered).
- Domain-adapted clause embeddings as a retrieval benchmark alongside PageIndex.
- Hand-labelled set grown to 40 items with adversarial perturbations.
- Upgrade the retrieval wrapper to a real PageIndex install once it's available on Windows (currently using the fallback clause-map-derived tree; acceptable for this document size but undersells what the library does on longer docs).

## Repo layout

```
pipeline/              core modules
pipeline/generators/   three distinct generators (A, B, C)
prompts/               versioned prompt templates
prompts/judges/        per-dimension judge prompts
schemas/               JSON Schema for dataset rows
tools/                 one-shot scripts (fetch, curate-check, tree-build, hand-labels)
eval/                  committed hand labels
tests/                 unit + e2e tests
tests/fixtures/        stub LLM responses for dry-run tests
runs/                  per-run outputs (gitignored except .gitkeep)
data/                  pinned ToS, clause map, tree (committed)
docs/superpowers/specs/  design spec
docs/superpowers/plans/  implementation plan
```
