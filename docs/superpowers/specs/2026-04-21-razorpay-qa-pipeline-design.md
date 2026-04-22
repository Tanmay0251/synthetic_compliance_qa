# Razorpay Q&A Synthetic Dataset Pipeline — Design

**Date:** 2026-04-21
**Owner:** Tanmay (reference solution for Hyde take-home scoring)
**Scope chosen:** Moderate (Approach 1 in brainstorming) — distinct per-category generators + deterministic validator + bounded regen + per-dimension micro-judges + cross-model judge-validation + automated failure catalogue.

---

## 1. Context and goal

Hyde's take-home asks for a synthetic training dataset for a Razorpay-ToS Q&A assistant, with three categories (A: clear answer, B: clarification required, C: genuine ambiguity), ≥15 examples per category, JSONL output, a custom schema, and an LLM-as-judge evaluation. The author's own prior feedback to Hyde made clear the rubric:

- **30% dataset quality per category**
- **30% evaluation rigor** (judge validation, failure catalogue, mitigation)
- **20% engineering judgment** (architecture, organisation)
- **20% production instincts** (reproducibility, cost awareness, video)

A weak submission curates 45 Q&As by hand, wraps them in a thin script, and gets a judge to rubber-stamp. A strong submission demonstrates the pipeline *as a system* — distinct paths per category, deterministic filtering, judge-validation, and honest self-surfaced failure modes.

This spec commits to the strong submission.

## 2. Non-goals

- No production deployment, no service, no web UI.
- No fine-tuning or training; we only produce data.
- No iterative regen loop beyond a single retry (out of scope for time/cost; flagged in "v2" section of video).
- No web scraping at run time — the ToS is fetched once, committed, and pinned.
- No embeddings-based retrieval (PageIndex is reasoning-tree-based by construction).

## 3. Architecture

```
                   ┌──────────────────────────────┐
                   │  data/razorpay_tos.{html,md} │  ← fetched & committed once
                   └──────────────┬───────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   clause_map.json           │  ← hand-curated by Claude Code
                    │   {id, title, text, span}   │    (page-by-page read)
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   PageIndex tree.json       │  ← built once, committed
                    │   (reasoning-tree, no embs) │
                    └─────────────┬──────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
      ┌────▼────┐            ┌────▼────┐            ┌────▼────┐
      │ Gen A   │            │ Gen B   │            │ Gen C   │
      │ clear   │            │ clarify │            │ ambig.  │
      └────┬────┘            └────┬────┘            └────┬────┘
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Deterministic Validator   │
                    │ (cite-resolve, grounding,   │
                    │  self-cont, dedup, struct)  │
                    └─────────┬─────────┬────────┘
                              │         │
                     pass ────┘         └──── fail (recoverable?)
                              │                 │
                              │        ┌────────▼────────┐
                              │        │ Bounded regen   │
                              │        │ (≤1 retry with  │
                              │        │ validator notes)│
                              │        └────────┬────────┘
                              │                 │
                              ▼◄────────────────┘ (re-validate)
                    ┌─────────────────────────────┐
                    │   Per-dimension Judges      │
                    │ grounding • category-fit •  │
                    │ clarifier-Q (B) • ambig-    │
                    │ framing (C) • clarity • cite│
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │   Judge-Validation           │
                    │  (10 human labels + cross-  │
                    │   model κ on 20% slice)     │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │ dataset.jsonl • eval.md •   │
                    │ failure_catalogue.md •      │
                    │ metrics.json                │
                    └─────────────────────────────┘
```

Every stage logs wall-clock, tokens, and cost to `runs/<timestamp>/metrics.json`.

## 4. Components

### 4.1 Source pinning (`tools/fetch_tos.py`)
Fetches `https://razorpay.com/terms` once, cleans HTML → Markdown via `trafilatura`, writes `data/razorpay_tos.html` (raw) + `data/razorpay_tos.md` (cleaned) + `data/razorpay_tos.meta.json` (URL, fetch timestamp, SHA-256). Pipeline reads the cleaned MD at run time; network not hit again. Re-running the fetcher is the explicit refresh path.

### 4.2 Clause map (`data/clause_map.json`)
Human-curated (by Claude Code, reading the doc page-by-page). Schema:
```json
{
  "clauses": [
    {
      "clause_id": "Part A §3.4",
      "title": "Fees payable on refund",
      "verbatim_text": "...",
      "line_start": 142,
      "line_end": 156,
      "parent": "Part A §3",
      "topics": ["fees", "refunds"]
    }
  ],
  "meta": {"source_md_sha256": "...", "curated_at": "2026-04-21"}
}
```
Post-process script `tools/clause_map_check.py` validates every `verbatim_text` is still a substring of the current MD (fail-fast on source drift). Noted in README as deliberate choice: regex is unreliable on ToS structure; hand-curation gives deterministic citation resolution.

### 4.3 PageIndex wrapper (`pipeline/retrieval.py`)
Thin facade over the `pageindex` library. Builds the reasoning tree from the cleaned MD once, caches to `data/pageindex_tree.json`. Exposes:
```python
class Retriever:
    def query(self, nl_query: str, top_k: int = 5) -> list[ClauseHit]: ...
    def navigate(self, node_path: list[str]) -> list[ClauseHit]: ...
```
`ClauseHit` carries the PageIndex node ID + the resolved `clause_id` from the clause map (cross-walked by substring match on node text). This preserves the "no embeddings, reasoning-based" property PageIndex is chosen for while making the output citation-ready.

### 4.4 LLM client (`pipeline/llm.py`)
Model-agnostic client:
```python
class LLMClient(Protocol):
    def complete(self, system: str, messages: list[Msg], **opts) -> Response: ...
```
Concrete implementations: `AnthropicClient` (default, Claude Sonnet 4.6 for generation, Opus 4.7 for judge), `OpenAIClient` (for cross-model validation), `StubClient` (returns fixtures from `tests/fixtures/`, used for dry-run with zero API calls).

All calls wrapped in a `with stage_timer("gen.A", ...)` context manager that logs `{stage, model, input_tokens, output_tokens, latency_ms, cost_usd}` to the current run's metrics file. Cost computed from a committed `pipeline/pricing.json` table.

### 4.5 Generators — three distinct modules

Each lives in `pipeline/generators/{a,b,c}.py` and exports `generate(n: int, retriever, llm, seeds) -> list[Candidate]`. They differ meaningfully — not just a category parameter.

**Generator A — clear answer**
Input: list of "anchor clauses" (clauses that are self-contained and answerable). For each anchor, ask the LLM to produce a realistic engineer-voice question that the anchor answers unambiguously + a direct answer citing that clause. Retrieval is *reverse*: we start from a clause and ask the LLM to imagine a question; then we confirm retrieval of the same clause from the question works (grounding check).

**Generator B — clarification required**
Input: pairs of related-but-divergent clauses where the answer depends on which applies (e.g., Clause 4.1 pre-settlement vs 4.2 post-settlement fraud). Pair-selection uses `topics` overlap + a LLM pass that screens for "does the answer genuinely differ depending on context axis X?". For each qualifying pair, generate a question whose answer forks on that axis, a clarifying question naming the axis explicitly, and a forked answer sketch for each branch. Category B's known failure mode — hand-wavy clarifiers — is the primary thing this generator's prompt is written to avoid.

**Generator C — genuine ambiguity**
Input: "silence-candidates" harvested three ways: (i) topics present in seed questions but absent from any clause; (ii) clauses that defer to external regulation (e.g., "per RBI notification X") without defining boundaries; (iii) suspension/duration/threshold language that's qualitative ("may", "as determined") rather than quantitative. For each candidate, the generator produces a question that probes the silence, a response that names what *is* known, describes the silence specifically, and recommends escalation. Its prompt explicitly forbids confident answers and requires a named silence-type (`silent`, `vague_language`, `external_deferral`, `multi_rule_conflict`).

All three generators share: persona pool (CTO, backend engineer, product manager, ops, legal-adjacent PM), few-shot examples drawn from the 6 seed Q&As split by category, temperature 0.7, top_p 0.9, deterministic seed per candidate index for run-level reproducibility.

### 4.6 Validator (`pipeline/validator.py`)
Deterministic, zero LLM calls. Each candidate runs through:

| Check | Logic | Applies to |
|---|---|---|
| `citation_resolves` | Every `clause_citations[i].clause_id` exists in clause_map; `verbatim_excerpt` is a substring of that clause's `verbatim_text` | A, B, C (if cited) |
| `grounding` | Any factual claim in the answer that contains a clause-specific entity (number, day-count, percentage, clause ref) must appear in at least one cited clause | A, B (branches) |
| `self_containment` | Question has no pronoun without antecedent; no reference to prior turn; regex + LLM-free heuristic | A, B, C |
| `duplicate` | Normalised-question hash + Jaccard ≥ 0.8 over tokenised question + same clause-ID set → reject later-generated | A, B, C |
| `struct_A` | Category A: ≥1 citation; answer has no hedging words from a committed stoplist (`might`, `unclear`, `depends`…) | A |
| `struct_B` | Category B: non-empty `clarifying_question`; non-empty `clarification_axis`; axis term appears verbatim in the clarifier | B |
| `struct_C` | Category C: `ambiguity_reason.type` ∈ allowed set; answer contains an escalation recommendation; `should_escalate == true` | C |

Each failure emits a structured reason. Recoverable failures (struct_*, grounding, citation) → one regen with the reason string injected into the generator prompt. Non-recoverable (duplicate, hard self-containment break) → drop + log.

### 4.7 Bounded regen (`pipeline/regen.py`)
Single retry only. Second failure → candidate goes to `runs/<ts>/dropped.jsonl` with reason. This is deliberate: unbounded regen masks prompt quality. The drop log feeds the failure catalogue.

### 4.8 Judges — per-dimension micro-judges (`pipeline/judge.py`)

| Judge | Dimensions scored (1–5) | Applies to |
|---|---|---|
| `GroundingJudge` | factual_support, citation_relevance | A, B, C |
| `CategoryFitJudge` | category_correctness | A, B, C |
| `ClarifierQualityJudge` | specificity, names_axis, not_vague, explains_what_changes | B |
| `AmbiguityFramingJudge` | names_silence_type, avoids_confident_answer, recommends_escalation | C |
| `ClarityJudge` | readability, concision | A, B, C |
| `CitationAccuracyJudge` | excerpt_is_verbatim, clause_id_correct_scope | A, B |

Each judge is a separate prompt with a tight rubric and returns `{score, rationale, triggered_failure_modes[]}`. Aggregation is not a mean — per user's feedback, weight is on *judgment signals*, so the run report shows each dimension's distribution separately and flags items below threshold (score ≤ 2 on any dimension) for the failure catalogue. A single composite score is reported for convenience but is not load-bearing.

Judge model: Claude Opus 4.7 (stronger than generator by design, to avoid the "judge too lenient" trap). Temperature 0 for judges.

### 4.9 Judge-validation (`pipeline/judge_validation.py`)
Two mechanisms:

1. **Hand-labels.** I pre-label 10 deliberately-seeded items (5 plausibly-good, 5 with injected known failures: wrong citation, vague clarifier, confident answer in C, etc.). The judge scores them blind. We report per-dimension judge-vs-human agreement (exact match %, ±1 tolerance %, and the delta on the injected-failure items specifically — a judge that misses injected failures is the failure mode we're testing for).
2. **Cross-model κ.** When OpenAI key is available, a GPT-family judge runs the same rubric on a 20% random slice. Cohen's κ per dimension. Disagreements written to `runs/<ts>/judge_disagreements.jsonl` for manual review.

If the judge misses the injected failures, that's stated plainly in the eval summary — this is what "self-identified failures" means.

### 4.10 Failure catalogue (`pipeline/failure_catalogue.py`)
Automated. Picks the 3 lowest-scoring items per category (ties broken by dimension severity). For each: quotes the item, names the failing dimension(s), traces which pipeline stage produced the failure (generator prompt? validator miss? judge false-positive?), and names the rubric-or-code change that would catch it. Output is `runs/<ts>/failure_catalogue.md`, folded into the README.

### 4.11 Run orchestrator (`run.py`)
Entry point. CLI:
```
python run.py \
  --target-per-category 15 \
  --over-generate 1.5 \
  --model-gen claude-sonnet-4-6 \
  --model-judge claude-opus-4-7 \
  --cross-model-judge gpt-5 \
  --seed 42 \
  --out runs/<timestamp>
```
Stages: `fetch_check → clause_map_check → tree_build → generate → validate → regen → judge → judge_validate → catalogue → report`. Every stage timed, every LLM call tracked. `--dry-run` swaps in `StubClient` and uses fixtures.

## 5. Data contracts

### 5.1 JSONL output schema (`schemas/dataset.schema.json`)
```json
{
  "id": "A-001",
  "category": "A",
  "question": "...",
  "persona": "backend_engineer",
  "user_context": null,
  "answer": "...",
  "clarifying_question": null,
  "clarification_axis": null,
  "answer_branches": null,
  "clause_citations": [
    {"clause_id": "Part A §3.4", "verbatim_excerpt": "...", "relevance": "direct"}
  ],
  "ambiguity": null,
  "confidence": "high",
  "should_escalate": false,
  "generation_meta": {
    "prompt_version": "gen-a-v1",
    "model": "claude-sonnet-4-6",
    "seed_clause_ids": ["Part A §3.4"],
    "retrieval_trace": [{"query":"...", "hits":["Part A §3.4","Part A §3.5"]}],
    "timestamp": "2026-04-21T09:00:00Z",
    "cost_usd": 0.0042,
    "tokens": {"input": 2300, "output": 410},
    "latency_ms": 1840,
    "regen_count": 0
  },
  "validator_report": {"passed": true, "checks": {"citation_resolves": "ok", "grounding": "ok"}},
  "judge_report": {
    "scores": {"grounding.factual_support": 5, "category_correctness": 5},
    "failure_flags": [],
    "composite": 4.9
  }
}
```
Fields specific to B: `clarifying_question`, `clarification_axis`, `answer_branches[{axis_value, answer, clause_citations}]`, `answer` is null.
Fields specific to C: `ambiguity.type ∈ {silent, vague_language, external_deferral, multi_rule_conflict}`, `ambiguity.what_is_known`, `ambiguity.what_is_missing`, `should_escalate = true`.

Schema is a real JSON Schema at `schemas/dataset.schema.json` and every emitted row is validated before write (fail-fast).

### 5.2 Per-run outputs (`runs/<timestamp>/`)
```
runs/2026-04-21T090000Z/
├── dataset.jsonl              # 45+ validated examples
├── dropped.jsonl              # validator-rejected with reasons
├── metrics.json               # per-stage timings, tokens, cost
├── judge_scores.jsonl         # raw judge outputs per item
├── judge_disagreements.jsonl  # cross-model mismatches
├── judge_validation.md        # human-vs-judge agreement summary
├── failure_catalogue.md       # 3 worst per category + root cause
└── report.md                  # top-level eval summary
```

## 6. Determinism and reproducibility

README includes an explicit table per user's feedback:

| Artefact | Deterministic? | Mechanism |
|---|---|---|
| ToS source | Yes | pinned file, SHA logged |
| Clause map | Yes | hand-curated, committed |
| PageIndex tree | Yes (given source) | cached JSON, rebuilt only on source change |
| Generators | No (by design) | temp 0.7; reproducibility via run-level `--seed` and per-item deterministic sub-seeds |
| Validator | Yes | pure Python |
| Judges | Near-det | temp 0 (model-side nondeterminism remains; reported) |
| Judge-validation | Yes | fixed hand-label set, committed |
| Metrics | Yes | wall-clock varies, tokens/cost don't |

Full reproduction from clean clone: `make setup && make fetch && make curate && make run`. README documents this.

## 7. Cost and latency controls

- Over-generation ratio capped at 1.5× target (≤23 per category at 15-target) to bound spend.
- Max tokens capped per call (gen: 1200, judge: 600).
- Cross-model judge slice capped at 20% (≤9 items), not full dataset.
- `pipeline/pricing.json` lets us estimate run cost before executing; CLI prints "estimated spend: $X.XX, proceed? [y/N]" unless `--yes`.
- Every run's total cost written to top of `report.md`.

Rough target: full 45-example run < $5 total (generator + validator + 6 micro-judges × 45 + 9 cross-model = ~350 LLM calls at Sonnet/Opus mix).

## 8. Repo layout

```
Take_Home/
├── README.md
├── Makefile
├── pyproject.toml
├── requirements.txt
├── schemas/
│   └── dataset.schema.json
├── data/
│   ├── razorpay_tos.html
│   ├── razorpay_tos.md
│   ├── razorpay_tos.meta.json
│   ├── clause_map.json
│   └── pageindex_tree.json
├── tools/
│   ├── fetch_tos.py
│   └── clause_map_check.py
├── pipeline/
│   ├── __init__.py
│   ├── llm.py
│   ├── pricing.json
│   ├── retrieval.py
│   ├── validator.py
│   ├── regen.py
│   ├── judge.py
│   ├── judge_validation.py
│   ├── failure_catalogue.py
│   ├── metrics.py
│   ├── schema.py
│   └── generators/
│       ├── a.py
│       ├── b.py
│       └── c.py
├── prompts/                      # versioned prompt templates
│   ├── gen_a_v1.md
│   ├── gen_b_v1.md
│   ├── gen_c_v1.md
│   └── judges/
│       ├── grounding_v1.md
│       ├── category_fit_v1.md
│       ├── clarifier_quality_v1.md
│       ├── ambiguity_framing_v1.md
│       ├── clarity_v1.md
│       └── citation_accuracy_v1.md
├── eval/
│   └── hand_labels.jsonl         # 10 committed items with human labels
├── tests/
│   ├── fixtures/                 # stub LLM responses
│   ├── test_validator.py
│   ├── test_clause_map.py
│   └── test_schema.py
├── runs/
│   └── .gitkeep
├── run.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-21-razorpay-qa-pipeline-design.md
└── video_script.md               # user-authored, out of scope here
```

## 9. Deliverables mapping

| Hyde deliverable | This repo produces |
|---|---|
| Synthetic dataset script | `run.py` + `pipeline/` |
| 45+ JSONL | `runs/<ts>/dataset.jsonl` (+ committed latest `dataset.jsonl` at root) |
| LLM-as-judge eval | `pipeline/judge.py` + `runs/<ts>/judge_scores.jsonl` |
| Eval summary | `runs/<ts>/report.md` + `failure_catalogue.md` + `judge_validation.md` |
| README with setup/run | `README.md` |
| 2-min video | User handles separately |

## 10. Known risks and mitigations

- **Judge leniency on Category C** (user's flagged failure mode: judge treats "I don't know" as clear). Mitigation: dedicated `AmbiguityFramingJudge` that specifically penalizes confident-sounding language, plus injected-failure items in hand-labels that confirm this judge isn't fooled.
- **Generator B produces vague clarifiers.** Mitigation: `clarification_axis` must be a named axis term that appears verbatim in the clarifying question — deterministic validator check, not a judge judgment.
- **PageIndex is overkill for a short doc.** Mitigation: use it as chosen, but write the retriever interface so swap-out is trivial; note the trade-off in README.
- **Cross-model judge adds dependency on OpenAI key.** Mitigation: gracefully skipped if key absent; `runs/<ts>/judge_validation.md` reports which mechanisms ran.
- **45 examples is small for κ to stabilize.** Mitigation: report κ with CI, don't overclaim.
- **Hand-labelled set can be gamed** (by me) since I'm both curating and evaluating. Mitigation: labels written *before* any judge is run; labels committed with a timestamp; injected-failure items are specifically constructed to stress-test the judge, not to flatter it.

## 11. Out of scope for v1 (flagged for video's "v2" section)

- Multi-turn generation (follow-ups after B-clarifier is answered).
- Active-learning loop where failure catalogue feeds back into generator prompt updates.
- Judge ensembling beyond 2 models.
- Domain-adapted clause embeddings as a retrieval alternative to benchmark against PageIndex.
