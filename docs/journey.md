# Project journey — how this got built

Short chronological log of what we did, what broke, and how we fixed it. This is the honest trace — not a post-hoc tidy-up.

## v0 — design before coding

Wrote the spec first (`docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md`), then the task-by-task plan (`docs/superpowers/plans/2026-04-21-razorpay-qa-pipeline.md`). Architectural choice: three distinct generator modules per category (not one with a switch), deterministic validator between generation and judging, six per-dimension micro-judges rather than one monolithic rubric, hand-labelled injected-failure set to validate the judge itself.

Reason for distinct generators: A/B/C fail in different ways. A fails on citation scope; B fails on vague or non-load-bearing clarifiers; C fails on faked silence. A single prompt cannot capture those failure modes cleanly.

## v1 — first real run

`$7.81, 38 min, 251 LLM calls` → 39 rows (A=15, B=15, C=9).

Category C came in short: two long-form C answers contained unescaped `"` inside a verbatim excerpt and failed JSON parse. Added `json_repair` as a fallback. Wrote `tools/topup.py` to bring C up to 15 without re-running the whole pipeline.

After C top-up: 45 rows, `$9.50` cumulative. Judge validation: **100% injected-failure catch rate** against the 10 committed hand-labels.

## v1 audit — independent pass found the real quality ceiling

Ran a fresh auditor subagent — not the project's own judges — against the PS category criteria verbatim. Result:

| Category | v1 pass |
|---|---|
| A | 14/15 |
| B | **2/15** |
| C | 15/15 |
| **Total** | **31/45 = 69%** |

Root causes:

1. **B regen seed bug.** Every B candidate that failed validator called `regen_one(feedback)`, which invoked `mod.generate(seed=42+999=1041)`. The seed was constant — every regen picked the same top-scoring clause pair. Seven B rows ended up with identical `seed_clause_ids` `(Part A §3.2 tax, Part B Part IA §1.4(c)(i) late-interest)`. The axis `tax vs. late-fee` wasn't load-bearing — both apply concurrently.

2. **B prompt was too permissive.** Rules said "name the axis specifically" and "explain what would change" — but didn't force the model to verify the two branches had different conclusions before emitting. The LLM happily invented plausible-sounding axes to satisfy the output format.

3. **A scope mismatch (A-007).** Generator was handed a scoped clause (PA-CB outward INR 25 lakh cap) and wrote a domestic-sounding question. Prompt didn't warn about scope.

4. **C thematic duplication.** Same clause could be picked multiple times. Four thematic duplicate pairs.

5. **Our own judges missed most of this** — `category_fit.category_correctness` flagged only 2 of the 13 B fails. The judge rubric was looser than the PS criteria. Honest reading: the judges were trained on outputs the generator could reliably produce; they didn't catch what the PS specifically warned against.

## v2 — prompt rewrites + regen

Patched (commit `af6f858`):
- `prompts/gen_b_v1.md`: 4-step chain-of-thought. Step 1 identify axis, Step 2 draft two branch conclusions, Step 3 divergence check — if conclusions converge, emit `{"reject": true, "reason": ...}` and stop. Step 4 emit.
- `prompts/gen_c_v1.md`: silence-verification step. Before claiming silence, check if another ToS clause answers directly.
- `prompts/gen_a_v1.md`: scope-awareness. If the anchor clause is scoped (PA-CB outward, offline devices, gaming merchants), the question must stay inside that scope.
- `pipeline/generators/b.py::_select_pairs`: accept `exclude_pair_ids`; enforce max 2 uses per clause across the batch.
- `pipeline/generators/c.py::_select_candidates`: accept `exclude_clause_ids`.
- `tools/topup.py`: added `--drop-ids`, pass exclusion sets into generators, make the regen seed unique per candidate (`args.seed + 4242 + idx * 37`).

Dropped the 14 audit-flagged rows (1A + 13B) plus 4 thematic-duplicate C rows. Regenerated. Cost: `+$2.63`.

Re-audited:

| Category | v1 | v2 |
|---|---|---|
| A | 14/15 | 15/15 |
| B | 2/15 | **10/15** |
| C | 15/15 | 15/15 |
| **Total** | 31/45 | **40/45 = 89%** |

The recycled tax-vs-interest pair was completely gone. Eight B candidates self-rejected during generation with the divergence-check prompt — exactly the mechanism we wanted.

## v2 audit — 5 B rows still failed, different reason

The v2 auditor found a subtler pattern on the 5 remaining B fails: **the question itself contained the fact that pins the axis value**.

Example: B-012 asked about "a fine from a card association that Razorpay is going to recover from our settlement". The axis was "recovery mechanism — card-network penalty (§2.25) vs. Permissible-Deduction (chargeback)". But the question already said "card-network fine", so §2.25 was clearly the applicable clause. Direct Category A, not B.

## v3 — axis-first construction

Patched (`prompts/gen_b_v1.md` again):
- Step 2 became "draft the question WITHOUT revealing the axis value". Explicit examples of pre-revealing phrases.
- Added: branches must cite DIFFERENT excerpts. If both would cite the same clause text, the "axis" is a factual pre-condition already inside one clause — reject.

Dropped the 5 v2-flagged B rows. Regenerated. Cost: `+$1.46`.

Re-audited:

| Category | v1 | v2 | v3 |
|---|---|---|---|
| A | 14/15 | 15/15 | 15/15 |
| B | 2/15 | 10/15 | **13/15** |
| C | 15/15 | 15/15 | 15/15 |
| **Total** | 31/45 | 40/45 | **43/45 = 96%** |

Two remaining B fails:
- **B-006** — not regenerated between rounds; v2 audit marked it pass, v3 audit caught a pre-revealed axis the v2 auditor had missed.
- **B-015** — regenerated in v3 with the new prompt, but hit a different failure class (concurrent obligations presented as alternatives — the same class as the original v2 B-007, not explicitly guarded by the v3 prompt).

Round-3 regen produced 5 self-rejects during generation (prompt working as intended).

## v3 audit — 2 remaining fails, and a coverage problem

v3 auditor flagged B-006 (pre-revealed axis the v2 auditor had missed) and B-015 (concurrent obligations presented as alternatives — a new defect class that leaked through the v3 prompt's gaps).

Separately, when we audited the clause map itself we found the real problem: **only 19.1% of the ToS was indexed**. The 80 hand-curated clauses covered the seed-referenced slice (Part A §3, §4, §16 and a handful of Part B sections) but missed the bulk of the document — prohibited-merchant categories (lines 321–424), TokenHQ (Part III), RTO Protection (Part VI), E-Mandate reporting, SNRR accounts, most Device/POS provisions. Generators could only seed from the 19% slice, so the dataset was topically clustered even though within that slice it was clean. If this dataset were used as training data, the downstream model would be biased toward fees/refunds/suspension topics and blind to the rest of the ToS.

Two other defects surfaced at the same time:
- Every `parent` field in the clause map pointed to a non-existent ID (hallucinated during the original curation).
- The "PageIndex tree" was a fallback flat list of 80 siblings under a root, not a real reasoning tree — because the `pageindex` PyPI package is a hosted-API client, not a local library, and we'd been using the clause-map-derived fallback.

## v4 — real PageIndex + full coverage + regen

Three coordinated fixes:

1. **Real PageIndex tree.** Cloned [VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex) (the open-source implementation behind the paper), vendored into `third_party/PageIndex/`, invoked with `run_pageindex.py --md_path data/razorpay_tos.md --model anthropic/claude-sonnet-4-6`. Output: 41 section nodes, 99.9% text coverage, verified via audit — all 41 MD headings captured, 41/41 titles match source line numbers, monotonic ordering, no duplicates. Depth is 1 (Parts → sections), which is PageIndex's default for our MD; sub-clause hierarchy is in the clause map separately.
2. **100% clause-map coverage.** Merged in 16 section-level nodes from the tree for previously-uncovered regions + 55 gap-fill entries for remaining content spans. Final: 151 entries, all 1,040 MD lines covered, all 487 content lines inside a clause. Broken `parent` fields nulled out.
3. **Full regen on the expanded pool.** Seed 5000 + over-generate 2× → 45 rows with diverse coverage. Schema post-fix: generators now auto-fill `confidence` if the LLM drops it. B deficit closed via targeted topup (seed 6000) after dropping three B pairs that re-collided.

Cost: $9.68 (v4 initial) + $1.72 (v4 B topup) = $11.40. Wall: ~50 min.

Re-audited v4:

| Category | v1 | v2 | v3 | **v4** |
|---|---|---|---|---|
| A | 14/15 | 15/15 | 15/15 | **15/15** |
| B | 2/15 | 10/15 | 13/15 | **14/15** |
| C | 15/15 | 15/15 | 15/15 | **15/15** |
| **Total** | 31 | 40 | 43 | **44 / 45 (97.8%)** |

Topic diversity is genuinely broader — 16 distinct section buckets represented, devices/data/e-mandate/audit topics now have meaningful presence where v3 was fee/suspension-heavy.

## Why we stopped at 44/45

Every round caught the previous dominant failure class and — for the first three — introduced a new subtler one:
- v1: judge leniency + regen-seed bug + prompt generality → 31/45
- v2: added divergence check → 40/45 (fixed seed bug, killed recycled-pair flaw)
- v3: added axis-first + same-excerpt guard → 43/45 (killed pre-revealed-axis flaw, surfaced concurrent-obligations class)
- v4: real PageIndex tree + 100% map coverage + regen → 44/45 (added topic diversity, fixed schema-resilience, concurrent-obligations class persists at exactly 1 slot)

The one remaining fail (B-004) is the "concurrent obligations presented as alternatives" class. It has persisted across v2/v3/v4 at exactly one slot each time — named explicitly in `failure_catalogue.md` with the prompt-guard that would kill it. A v5 would add that guard. We stopped because the persistent-one-slot pattern is a stable, named, falsifiable weakness that shows up better in disclosure than in patching.

## Total spend

| Stage | Cost | Rows produced / kept |
|---|---|---|
| Warmup (`runs/warmup/`) | $0.96 | 5 |
| v1 initial + C top-up | $9.50 | 45 |
| v2 regen (18 rows) | $2.63 | 18 replacements |
| v3 regen (5 rows) | $1.46 | 5 replacements |
| Real PageIndex tree build | ~$0.50 | (tree only) |
| v4 full regen (45 rows) | $9.68 | 43 kept |
| v4 B topup (5 rows) | $1.72 | 5 replacements |
| **Total** | **~$26.45** | **45 final, 100% ToS coverage** |

Judge-validation rate on hand-labels has remained **100%** across all rounds — the injected-failure set was committed before the first judge run and never edited.

## What stuck around unchanged

These never needed revising through any of the three rounds:
- Source fetch + SHA pinning (`tools/fetch_tos.py`)
- 80-clause hand-curated map + substring validation (`data/clause_map.json`, `tools/clause_map_check.py`)
- Deterministic validator (`pipeline/validator.py`)
- Six micro-judges architecture (`pipeline/judge.py`)
- Judge-validation with injected failures (`pipeline/judge_validation.py`, `eval/hand_labels.jsonl`)
- Metrics + cost tracking (`pipeline/metrics.py`)
- JSON Schema for dataset rows (`schemas/dataset.schema.json`)

Their interfaces were right the first time. The quality gap was entirely in the generator prompts and regen seeding — which is where most take-home pipelines would quietly fail silently.
