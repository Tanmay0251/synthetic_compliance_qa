"""Top-up an existing run so every category meets its target.

Can also drop specified row IDs first (e.g. after an independent audit flagged
some rows as failing the PS category criteria), then regenerate to restore
target count. Pass:
    --drop-ids A-007,B-001,B-002,...

The generators are invoked with the clause / pair IDs of already-kept rows
excluded, so regenerated rows don't recycle the same seed clauses.
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


def _compute_exclusions(kept_rows: list[dict]) -> dict:
    """From already-kept rows, derive the exclusion sets the generators should honour."""
    a_clauses: set[str] = set()
    b_pairs: set[frozenset[str]] = set()
    c_clauses: set[str] = set()
    for r in kept_rows:
        ids = r["generation_meta"].get("seed_clause_ids", [])
        cat = r["category"]
        if cat == "A" and len(ids) >= 1:
            a_clauses.add(ids[0])
        elif cat == "B" and len(ids) >= 2:
            b_pairs.add(frozenset({ids[0], ids[1]}))
        elif cat == "C" and len(ids) >= 1:
            c_clauses.add(ids[0])
    return {"A": a_clauses, "B": b_pairs, "C": c_clauses}


def _call_generator(
    cat: str, *, n: int, retriever, llm, seed: int, regen_feedback: str, exclusions: dict
):
    """Unified call site that passes the right exclude_* arg per generator."""
    mod = GEN_MODULES[cat]
    if cat == "A":
        return mod.generate(
            n=n, retriever=retriever, llm=llm, seed=seed,
            regen_feedback=regen_feedback, exclude_clause_ids=exclusions["A"],
        )
    if cat == "B":
        return mod.generate(
            n=n, retriever=retriever, llm=llm, seed=seed,
            regen_feedback=regen_feedback, exclude_pair_ids=exclusions["B"],
        )
    return mod.generate(
        n=n, retriever=retriever, llm=llm, seed=seed,
        regen_feedback=regen_feedback, exclude_clause_ids=exclusions["C"],
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="existing runs/<ts>/ to top up in-place")
    ap.add_argument("--target-per-category", type=int, default=15)
    ap.add_argument("--over-generate", type=float, default=2.5)
    ap.add_argument("--model-gen", default="claude-sonnet-4-6")
    ap.add_argument("--model-judge", default="claude-opus-4-7")
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--drop-ids", default="", help="comma-separated row IDs to remove before topup")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    data_dir = ROOT / "data"
    dataset_path = run_dir / "dataset.jsonl"
    if not dataset_path.exists():
        print(f"ERROR: {dataset_path} not found", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    drop_ids = {x.strip() for x in args.drop_ids.split(",") if x.strip()}
    if drop_ids:
        before = len(rows)
        dropped_for_log = [r for r in rows if r["id"] in drop_ids]
        rows = [r for r in rows if r["id"] not in drop_ids]
        print(f"[topup] dropped {before - len(rows)} rows per --drop-ids (requested {len(drop_ids)})")
        # Keep dropped rows in dropped.jsonl with reason
        dp = run_dir / "dropped.jsonl"
        with dp.open("a", encoding="utf-8") as f:
            for dr in dropped_for_log:
                f.write(json.dumps({"row": dr, "reasons": [f"dropped_via_topup: post-audit"]}) + "\n")

    counts = Counter(r["category"] for r in rows)
    print(f"[topup] starting counts after drop: {dict(counts)}")

    deficits = {cat: max(0, args.target_per_category - counts.get(cat, 0)) for cat in "ABC"}
    if all(v == 0 for v in deficits.values()):
        print("[topup] all categories at or above target — nothing to do")
        return 0
    print(f"[topup] deficits: {deficits}")

    topup_metrics = MetricsCollector(run_dir / "topup_metrics.json")
    gen_llm = make_client(args.model_gen)
    judge_llm = make_client(args.model_judge)
    retriever = Retriever()
    validator = Validator(clause_map_path=data_dir / "clause_map.json", md_path=data_dir / "razorpay_tos.md")
    validator.reset()
    for r in rows:
        validator.check(r)
    clause_by_id = _load_clause_by_id(data_dir)

    next_idx = {cat: counts.get(cat, 0) + 1 for cat in "ABC"}
    dropped_path = run_dir / "dropped.jsonl"
    new_rows: list[dict] = []

    for cat, needed in deficits.items():
        if needed <= 0:
            continue
        # Recompute exclusions including any new rows already kept this run
        exclusions = _compute_exclusions(rows + new_rows)
        n_try = max(needed * 2, int(needed * args.over_generate))
        print(f"[topup] category {cat}: attempting {n_try} to get {needed} "
              f"(excl: A={len(exclusions['A'])} B={len(exclusions['B'])} C={len(exclusions['C'])})")
        with topup_metrics.stage(f"topup_gen.{cat}", model=gen_llm.model) as m:
            cands = _call_generator(cat, n=n_try, retriever=retriever, llm=gen_llm,
                                    seed=args.seed + ord(cat), regen_feedback="", exclusions=exclusions)
            for cand in cands:
                gm = cand.row.get("generation_meta", {})
                m.input_tokens += gm.get("tokens", {}).get("input", 0)
                m.output_tokens += gm.get("tokens", {}).get("output", 0)
            m.count = len(cands)
            m.cost_usd = cost_usd(gen_llm.model, m.input_tokens, m.output_tokens)

        kept_for_cat = 0
        with topup_metrics.stage(f"topup_validate.{cat}", model=gen_llm.model) as m:
            for idx, cand in enumerate(cands):
                if kept_for_cat >= needed:
                    break
                def regen_one(feedback: str, c=cand, cat=cat, idx=idx):
                    # UNIQUE seed per candidate so regens don't all collapse to the same pair
                    excl = _compute_exclusions(rows + new_rows)
                    results = _call_generator(
                        cat, n=1, retriever=retriever, llm=gen_llm,
                        seed=args.seed + 4242 + idx * 37, regen_feedback=feedback,
                        exclusions=excl,
                    )
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

    # Schema-validate, renumber sequentially per category, write back
    kept_final: list[dict] = []
    for row in new_rows:
        errs = validate_row(row)
        if errs:
            print(f"[topup] WARN: {row['id']} failed schema: {errs[:2]}")
            continue
        kept_final.append(row)

    all_rows = rows + kept_final
    # Renumber per-category so IDs are contiguous
    counters = {"A": 0, "B": 0, "C": 0}
    # Sort so existing rows keep their relative order; new rows get appended in generation order
    stable_order = sorted(all_rows, key=lambda r: (r["category"], r["id"]))
    for r in stable_order:
        counters[r["category"]] += 1
        r["id"] = f"{r['category']}-{counters[r['category']]:03d}"
    all_rows = stable_order

    with dataset_path.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from pipeline.judge import RowJudgement, JudgeResult
    judgements = {}
    for r in all_rows:
        jr = r.get("judge_report") or {}
        scores = jr.get("scores", {})
        per = {}
        for k, v in scores.items():
            j_name, _, sub = k.partition(".")
            per.setdefault(j_name, {})[sub or j_name] = v
        flags = jr.get("failure_flags", [])
        per_judge = []
        for name, sub in per.items():
            per_judge.append(JudgeResult(judge=name, scores=sub, failure_flags=flags if not per_judge else []))
        judgements[r["id"]] = RowJudgement(row_id=r["id"], category=r["category"], per_judge=per_judge)
    failure_catalogue.build(all_rows, judgements, run_dir / "failure_catalogue.md")

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
        f"- Total cost (USD): {combined['total_cost_usd']:.4f} "
        f"(initial {totals['total_cost_usd']:.4f} + topup {topup_totals['total_cost_usd']:.4f})",
        f"- Wall seconds: initial {combined['wall_s_initial']:.0f}s + topup {combined['wall_s_topup']:.0f}s",
        f"- LLM calls: {combined['llm_calls']}",
        "",
        "## Composite score by category",
        "",
        f"- A: mean {mean(by_cat['A'])} over {len(by_cat['A'])} rows",
        f"- B: mean {mean(by_cat['B'])} over {len(by_cat['B'])} rows",
        f"- C: mean {mean(by_cat['C'])} over {len(by_cat['C'])} rows",
        "",
        "See `judge_validation.md` and `failure_catalogue.md` for detail.",
    ]
    (run_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[topup] done. dataset now has {combined['dataset_rows']} rows; total cost ${combined['total_cost_usd']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
