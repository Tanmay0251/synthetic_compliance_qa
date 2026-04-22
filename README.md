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

## Results

45 rows, 15 per category, all schema-valid. Generator: Claude Sonnet 4.6. Judge: Claude Opus 4.7 (deliberately stronger than the generator).

| | Composite mean (1–5) | Independent PS audit |
|---|---|---|
| A | 4.91 | 15 / 15 |
| B | 4.83 | 14 / 15 |
| C | 4.67 | 15 / 15 |
| **Total** | | **44 / 45 (97.8%)** |

Source: Razorpay ToS, 1,040 MD lines. **100% of the ToS is indexed** in the clause map (151 entries). Real PageIndex reasoning tree built via VectifyAI's open-source library, 41 section nodes, 99.9% text coverage.

Judge-validation on 10 committed hand-labels: **100% injected-failure catch rate** across the 5 failure types. Per-dim Cohen's κ: citation accuracy 1.00, clarifier-quality sub-dims 0.80–1.00, grounding.factual_support 0.78, ambiguity_framing.recommends_escalation **0.52** (judge over-credits soft escalation — acknowledged gap).

Six micro-judges rather than one monolithic rubric:
- `GroundingJudge`, `CategoryFitJudge`, `ClarityJudge`, `CitationAccuracyJudge` — all categories
- `ClarifierQualityJudge` (4 sub-dims) — B only
- `AmbiguityFramingJudge` — C only, specifically to block judge-rubber-stamps-on-"I don't know"

Judge-validation runs two mechanisms: (1) committed hand-labels with injected failures (`eval/hand_labels.jsonl`); (2) cross-model κ via `--cross-model-judge gpt-5` (code ready, gated on OPENAI_API_KEY).

Full numbers: `eval_summary.md`. Per-row worst items with concrete code/rubric fixes: `failure_catalogue.md`. End-to-end build arc (v1 69% → v2 89% → v3 96%): `docs/journey.md`.

## v5 (if I had another day)

- **Kill the last B-class** — add a "concurrent-obligations" guard to the B prompt (if both clauses impose binding obligations that apply simultaneously with no carve-out, reject the pair). That's the one-slot defect that persists across v2/v3/v4.
- **Tighten `ambiguity_framing.recommends_escalation`** to require a named mechanism, not just a recipient — current κ 0.52.
- **Deeper PageIndex tree** — rerun with lower token-per-node limit so depth goes from 1 (Parts → sections) to 2 (Parts → sections → sub-clauses).
- **Active-learning loop**: failure catalogue → prompt updates → next run, automated rather than manual per-round.

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
