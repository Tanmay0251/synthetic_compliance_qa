"""Top-up an existing run so every category meets its target.

Usage:
  python tools/topup.py --run-dir runs/<ts> --target-per-category 15
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.generators import a as gen_a, b as gen_b, c as gen_c
from pipeline.judge import judge_row
from pipeline.llm import make_client
from pipeline.metrics import MetricsCollector, cost_usd
from pipeline.regen import regen_if_needed
from pipeline.retrieval import Retriever
from pipeline.schema import validate_row
from pipeline.validator import Validator
from pipeline import failure_catalogue


GEN_MODULES = {"A": gen_a, "B": gen_b, "C": gen_c}


def _load_clause_by_id(data_dir: Path) -> dict:
    cm = json.loads((data_dir / "clause_map.json").read_text(encoding="utf-8"))
    return {c["clause_id"]: c for c in cm["clauses"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="existing runs/<ts>/ to top up in-place")
    ap.add_argument("--target-per-category", type=int, default=15)
    ap.add_argument("--over-generate", type=float, default=2.0, help="over-gen ratio for top-up (higher than initial, to compensate for JSON-parse drops)")
    ap.add_argument("--model-gen", default="claude-sonnet-4-6")
    ap.add_argument("--model-judge", default="claude-opus-4-7")
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    data_dir = ROOT / "data"
    dataset_path = run_dir / "dataset.jsonl"
    if not dataset_path.exists():
        print(f"ERROR: {dataset_path} not found", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter(r["category"] for r in rows)
    print(f"[topup] starting counts: {dict(counts)}")

    deficits = {cat: max(0, args.target_per_category - counts.get(cat, 0)) for cat in "ABC"}
    if all(v == 0 for v in deficits.values()):
        print("[topup] all categories at or above target — nothing to do")
        return 0
    print(f"[topup] deficits: {deficits}")

    # Start a fresh metrics file for the topup so we don't corrupt the original
    topup_metrics = MetricsCollector(run_dir / "topup_metrics.json")
    gen_llm = make_client(args.model_gen)
    judge_llm = make_client(args.model_judge)
    retriever = Retriever()
    validator = Validator(clause_map_path=data_dir / "clause_map.json", md_path=data_dir / "razorpay_tos.md")
    # Pre-register existing rows with the validator so duplicate detection respects them
    validator.reset()
    for r in rows:
        validator.check(r)  # populates seen_hashes / seen_clause_sets
    clause_by_id = _load_clause_by_id(data_dir)

    # Next free ID index per category
    next_idx = {cat: counts.get(cat, 0) + 1 for cat in "ABC"}
    dropped_path = run_dir / "dropped.jsonl"
    new_rows: list[dict] = []

    for cat, needed in deficits.items():
        if needed <= 0:
            continue
        mod = GEN_MODULES[cat]
        # Use existing validator state so duplicates from prior run are caught
        n_try = max(needed * 2, int(needed * args.over_generate))
        print(f"[topup] category {cat}: attempting {n_try} to get {needed}")
        with topup_metrics.stage(f"topup_gen.{cat}", model=gen_llm.model) as m:
            cands = mod.generate(n=n_try, retriever=retriever, llm=gen_llm, seed=args.seed + ord(cat))
            for cand in cands:
                gm = cand.row.get("generation_meta", {})
                m.input_tokens += gm.get("tokens", {}).get("input", 0)
                m.output_tokens += gm.get("tokens", {}).get("output", 0)
            m.count = len(cands)
            m.cost_usd = cost_usd(gen_llm.model, m.input_tokens, m.output_tokens)

        kept_for_cat = 0
        with topup_metrics.stage(f"topup_validate.{cat}", model=gen_llm.model) as m:
            for cand in cands:
                if kept_for_cat >= needed:
                    break
                def regen_one(feedback: str, c=cand, cat=cat):
                    results = GEN_MODULES[cat].generate(n=1, retriever=retriever, llm=gen_llm, seed=args.seed + 4242, regen_feedback=feedback)
                    return results[0] if results else None
                try:
                    final, result, _ = regen_if_needed(cand, validator, regen_one)
                except Exception as e:
                    with dropped_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps({"row": cand.row, "reasons": [f"topup_regen_crash: {e}"]}) + "\n")
                    continue
                final.row["validator_report"] = result.to_dict()
                if not result.passed:
                    with dropped_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps({"row": final.row, "reasons": result.reasons}) + "\n")
                    continue
                final.row["id"] = f"{cat}-{next_idx[cat]:03d}"
                next_idx[cat] += 1
                new_rows.append(final.row)
                kept_for_cat += 1
        print(f"[topup] category {cat}: kept {kept_for_cat}/{needed} (attempted {len(cands)})")

    if not new_rows:
        print("[topup] no new rows produced")
        return 1

    # Judge new rows
    with topup_metrics.stage("topup_judge", model=judge_llm.model) as m:
        for row in new_rows:
            j = judge_row(row, judge_llm, clause_by_id)
            row["judge_report"] = {"scores": j.all_scores(), "failure_flags": j.failure_flags(), "composite": j.composite()}
            for res in j.per_judge:
                m.input_tokens += res.input_tokens
                m.output_tokens += res.output_tokens
            m.count += len(j.per_judge)
        m.cost_usd = cost_usd(judge_llm.model, m.input_tokens, m.output_tokens)

    # Schema-validate and append
    kept_final: list[dict] = []
    for row in new_rows:
        errs = validate_row(row)
        if errs:
            print(f"[topup] WARN: {row['id']} failed schema: {errs[:2]}")
            continue
        kept_final.append(row)

    all_rows = rows + kept_final
    with dataset_path.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Re-render failure catalogue and report (simple rewrite)
    # Build RowJudgement lookup for catalogue — reuse existing judge_report composite via a lightweight shim
    from pipeline.judge import RowJudgement, JudgeResult
    judgements = {}
    for r in all_rows:
        jr = r.get("judge_report") or {}
        scores = jr.get("scores", {})
        # synthesize per_judge from flat scores by splitting on the dot prefix
        per = {}
        for k, v in scores.items():
            j_name, _, sub = k.partition(".")
            per.setdefault(j_name, {})[sub or j_name] = v
        per_judge = [JudgeResult(judge=name, scores=sub) for name, sub in per.items()]
        judgements[r["id"]] = RowJudgement(row_id=r["id"], category=r["category"], per_judge=per_judge)
    failure_catalogue.build(all_rows, judgements, run_dir / "failure_catalogue.md")

    # Update report.md totals
    totals = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))["totals"]
    topup_totals = json.loads((run_dir / "topup_metrics.json").read_text(encoding="utf-8"))["totals"]
    combined = {
        "dataset_rows": len(all_rows),
        "total_cost_usd": totals["total_cost_usd"] + topup_totals["total_cost_usd"],
        "wall_s_initial": totals["total_wall_seconds"],
        "wall_s_topup": topup_totals["total_wall_seconds"],
        "llm_calls": totals["llm_calls"] + topup_totals["llm_calls"],
    }
    by_cat = {"A": [], "B": [], "C": []}
    for r in all_rows:
        by_cat[r["category"]].append(r["judge_report"]["composite"])
    mean = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0.0
    report_lines = [
        "# Run report (post-topup)",
        "",
        f"- Dataset rows: {combined['dataset_rows']} (A={len(by_cat['A'])}, B={len(by_cat['B'])}, C={len(by_cat['C'])})",
        f"- Total cost (USD): {combined['total_cost_usd']:.4f} (initial {totals['total_cost_usd']:.4f} + topup {topup_totals['total_cost_usd']:.4f})",
        f"- Wall seconds: initial {combined['wall_s_initial']:.0f}s + topup {combined['wall_s_topup']:.0f}s",
        f"- LLM calls: {combined['llm_calls']}",
        "",
        "## Composite score by category",
        "",
        f"- A: mean {mean(by_cat['A'])} over {len(by_cat['A'])} rows",
        f"- B: mean {mean(by_cat['B'])} over {len(by_cat['B'])} rows",
        f"- C: mean {mean(by_cat['C'])} over {len(by_cat['C'])} rows",
        "",
        "## Note",
        "",
        "Category C initial run produced 9 rows (below 15-target) due to JSON-parse failures on long-form ambiguity responses. Topup stage ran generator C a second time with higher over-generation (2×) and seed offset; see `topup_metrics.json` for cost breakdown. Failure patterns are documented in `failure_catalogue.md`.",
        "",
        "See `judge_validation.md` and `failure_catalogue.md` for detail.",
    ]
    (run_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[topup] done. dataset now has {combined['dataset_rows']} rows; total cost ${combined['total_cost_usd']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
