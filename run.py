"""End-to-end pipeline runner. See README for usage."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pipeline.generators import a as gen_a, b as gen_b, c as gen_c
from pipeline.judge import judge_row
from pipeline.judge_validation import run_hand_label_agreement, run_cross_model_kappa
from pipeline.llm import make_client, LLMClient, StubClient
from pipeline.metrics import MetricsCollector, cost_usd
from pipeline.regen import regen_if_needed
from pipeline.retrieval import Retriever
from pipeline.schema import validate_row
from pipeline.validator import Validator
from pipeline import failure_catalogue

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def _load_clause_by_id() -> dict[str, dict[str, Any]]:
    cm = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    return {c["clause_id"]: c for c in cm["clauses"]}


def _run_generator(
    mod,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    validator: Validator,
    seed: int,
    metrics: MetricsCollector,
    stage_prefix: str,
    dropped_path: Path,
):
    out: list[dict[str, Any]] = []
    with metrics.stage(f"{stage_prefix}.generate", model=llm.model) as m:
        cands = mod.generate(n=n, retriever=retriever, llm=llm, seed=seed)
        for cand in cands:
            gm = cand.row.get("generation_meta", {})
            m.input_tokens += gm.get("tokens", {}).get("input", 0)
            m.output_tokens += gm.get("tokens", {}).get("output", 0)
        m.count = len(cands)
        m.cost_usd = cost_usd(llm.model, m.input_tokens, m.output_tokens)
    with metrics.stage(f"{stage_prefix}.validate_regen", model=llm.model) as m:
        for cand in cands:
            def regen_one(feedback: str, c=cand):
                results = mod.generate(
                    n=1, retriever=retriever, llm=llm, seed=seed + 999, regen_feedback=feedback
                )
                return results[0] if results else None
            try:
                final, result, retries = regen_if_needed(cand, validator, regen_one)
            except Exception as e:
                print(f"[{stage_prefix}] regen crashed for candidate {cand.row.get('id','?')}: {e}")
                dropped_path.parent.mkdir(parents=True, exist_ok=True)
                with dropped_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"row": cand.row, "reasons": [f"regen_crash: {e}"]}) + "\n")
                continue
            final.row["validator_report"] = result.to_dict()
            if result.passed:
                out.append(final.row)
            else:
                dropped_path.parent.mkdir(parents=True, exist_ok=True)
                with dropped_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"row": final.row, "reasons": result.reasons}) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-per-category", type=int, default=15)
    ap.add_argument("--over-generate", type=float, default=1.5)
    ap.add_argument("--model-gen", default="claude-sonnet-4-6")
    ap.add_argument("--model-judge", default="claude-opus-4-7")
    ap.add_argument("--cross-model-judge", default=None, help="optional OpenAI model for cross-model κ")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true", help="use StubClient (no API calls)")
    ap.add_argument("--yes", action="store_true", help="skip cost estimate prompt")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = MetricsCollector(out_dir / "metrics.json")

    if args.dry_run:
        gen_llm: LLMClient = StubClient()
        judge_llm: LLMClient = StubClient()
    else:
        gen_llm = make_client(args.model_gen)
        judge_llm = make_client(args.model_judge)

    retriever = Retriever()
    validator = Validator(clause_map_path=DATA / "clause_map.json", md_path=DATA / "razorpay_tos.md")

    n_over = math.ceil(args.target_per_category * args.over_generate)
    dropped_path = out_dir / "dropped.jsonl"

    print(f"[run] over-generating {n_over} per category (target {args.target_per_category})")

    rows: list[dict[str, Any]] = []
    for cat, mod in [("A", gen_a), ("B", gen_b), ("C", gen_c)]:
        validator.reset()
        produced = _run_generator(
            mod, n_over, retriever, gen_llm, validator, args.seed,
            metrics, f"gen.{cat}", dropped_path,
        )
        produced = produced[: args.target_per_category]
        rows.extend(produced)
        print(f"[run] category {cat}: kept {len(produced)} of {n_over}")

    # Judge
    clause_by_id = _load_clause_by_id()
    judgements = {}
    with metrics.stage("judge", model=judge_llm.model) as m:
        for row in rows:
            j = judge_row(row, judge_llm, clause_by_id)
            row["judge_report"] = {
                "scores": j.all_scores(),
                "failure_flags": j.failure_flags(),
                "composite": j.composite(),
            }
            judgements[row["id"]] = j
            for res in j.per_judge:
                m.input_tokens += res.input_tokens
                m.output_tokens += res.output_tokens
            m.count += len(j.per_judge)

    # Schema-validate and write dataset
    bad = []
    with (out_dir / "dataset.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            errs = validate_row(row)
            if errs:
                bad.append((row["id"], errs))
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if bad:
        print(f"[run] WARNING: {len(bad)} rows failed schema and were excluded from dataset.jsonl")
        (out_dir / "schema_failures.jsonl").write_text(
            "\n".join(json.dumps({"id": rid, "errors": errs}) for rid, errs in bad),
            encoding="utf-8",
        )

    # Judge-validation
    with metrics.stage("judge_validation", model=judge_llm.model) as m:
        report, per_row = run_hand_label_agreement(
            ROOT / "eval" / "hand_labels.jsonl", judge_llm, clause_by_id
        )
    (out_dir / "judge_validation.md").write_text(
        _format_judge_validation(report), encoding="utf-8"
    )
    (out_dir / "judge_validation.json").write_text(
        json.dumps({"report": report.to_dict(), "per_row": per_row}, indent=2),
        encoding="utf-8",
    )

    # Cross-model κ (optional)
    if args.cross_model_judge and not args.dry_run:
        with metrics.stage("cross_model_judge", model=args.cross_model_judge) as m:
            secondary = make_client(args.cross_model_judge)
            km = run_cross_model_kappa(rows, judge_llm, secondary, clause_by_id)
        (out_dir / "judge_disagreements.jsonl").write_text(
            "\n".join(json.dumps(d) for d in km["disagreements"]), encoding="utf-8"
        )
        (out_dir / "cross_model_kappa.json").write_text(json.dumps(km, indent=2), encoding="utf-8")

    # Failure catalogue
    failure_catalogue.build(rows, judgements, out_dir / "failure_catalogue.md")

    # Top-level report
    (out_dir / "report.md").write_text(
        _format_report(rows, judgements, metrics, report, out_dir),
        encoding="utf-8",
    )
    print(f"[run] done. outputs in {out_dir}")
    return 0


def _format_judge_validation(report) -> str:
    lines = [
        "# Judge validation (hand-labelled set)",
        "",
        f"- Items labelled: {report.n_items}",
        f"- Injected-failure catch rate: {report.injected_failure_catch_rate:.1%}",
        "",
        "## Per-dimension agreement",
        "",
        "| Dimension | Exact | Within-1 | κ (quadratic) | n |",
        "|---|---|---|---|---|",
    ]
    for dim, stats in sorted(report.per_dimension.items()):
        lines.append(
            f"| `{dim}` | {stats['exact_match']:.2f} | {stats['within_1']:.2f} "
            f"| {stats['quadratic_kappa']:.2f} | {stats['n']} |"
        )
    return "\n".join(lines)


def _format_report(rows, judgements, metrics, jv_report, out_dir: Path) -> str:
    totals: dict[str, Any] = {}
    if metrics.out_path.exists():
        totals = json.loads(metrics.out_path.read_text(encoding="utf-8")).get("totals", {})
    by_cat: dict[str, list[float]] = {"A": [], "B": [], "C": []}
    for row in rows:
        by_cat[row["category"]].append(judgements[row["id"]].composite())
    mean = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0.0
    lines = [
        "# Run report",
        "",
        f"- Dataset rows: {len(rows)}",
        f"- Total cost (USD): {totals.get('total_cost_usd', 0):.4f}",
        f"- Total wall seconds: {totals.get('total_wall_seconds', 0):.1f}",
        f"- LLM calls: {totals.get('llm_calls', 0)}",
        "",
        "## Composite score by category",
        "",
        f"- A: mean {mean(by_cat['A'])} over {len(by_cat['A'])} rows",
        f"- B: mean {mean(by_cat['B'])} over {len(by_cat['B'])} rows",
        f"- C: mean {mean(by_cat['C'])} over {len(by_cat['C'])} rows",
        "",
        "## Judge validation",
        "",
        f"- Injected-failure catch rate: {jv_report.injected_failure_catch_rate:.1%}",
        "",
        "See `judge_validation.md` and `failure_catalogue.md` for detail.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
