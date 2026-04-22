"""Judge-validation: hand-label agreement + cross-model Cohen's κ."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.judge import RowJudgement, judge_row
from pipeline.llm import LLMClient

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class AgreementReport:
    per_dimension: dict[str, dict[str, float]]
    injected_failure_catch_rate: float
    n_items: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "per_dimension": self.per_dimension,
            "injected_failure_catch_rate": self.injected_failure_catch_rate,
            "n_items": self.n_items,
        }


def _quadratic_kappa(a: list[int], b: list[int], k: int = 5) -> float:
    if not a or len(a) != len(b):
        return 0.0
    # Counts
    ca = Counter(a)
    cb = Counter(b)
    n = len(a)
    obs = defaultdict(int)
    for x, y in zip(a, b):
        obs[(x, y)] += 1
    num = 0.0
    den = 0.0
    for i in range(1, k + 1):
        for j in range(1, k + 1):
            w = ((i - j) ** 2) / ((k - 1) ** 2)
            e = (ca[i] * cb[j]) / n if n else 0
            o = obs[(i, j)]
            num += w * o
            den += w * e
    return 1.0 - (num / den) if den else 0.0


def run_hand_label_agreement(
    labels_path: Path,
    llm: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
) -> tuple[AgreementReport, list[dict[str, Any]]]:
    items = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    per_dim_deltas: dict[str, list[tuple[int, int]]] = defaultdict(list)
    per_row: list[dict[str, Any]] = []
    injected_caught = 0
    injected_total = 0
    for item in items:
        j: RowJudgement = judge_row(item["row"], llm, clause_by_id)
        judge_scores = j.all_scores()
        human_scores: dict[str, int] = item["human_scores"]
        for dim, hs in human_scores.items():
            js = judge_scores.get(dim)
            if js is None:
                continue
            per_dim_deltas[dim].append((hs, int(js)))
        if item.get("injected_failure"):
            injected_total += 1
            # A judge that caught the failure scores the affected dim <= 2.
            target_dims = _failure_target_dims(item["injected_failure"])
            caught = any(judge_scores.get(d, 5) <= 2 for d in target_dims)
            if caught:
                injected_caught += 1
        per_row.append({
            "row_id": item["row"]["id"],
            "injected_failure": item.get("injected_failure"),
            "judge": judge_scores,
            "human": human_scores,
        })
    per_dimension: dict[str, dict[str, float]] = {}
    for dim, pairs in per_dim_deltas.items():
        h, g = zip(*pairs)
        exact = sum(1 for x, y in pairs if x == y) / len(pairs)
        within_1 = sum(1 for x, y in pairs if abs(x - y) <= 1) / len(pairs)
        kappa = _quadratic_kappa(list(h), list(g))
        per_dimension[dim] = {
            "exact_match": round(exact, 3),
            "within_1": round(within_1, 3),
            "quadratic_kappa": round(kappa, 3),
            "n": len(pairs),
        }
    report = AgreementReport(
        per_dimension=per_dimension,
        injected_failure_catch_rate=round(injected_caught / injected_total, 3) if injected_total else 0.0,
        n_items=len(items),
    )
    return report, per_row


def _failure_target_dims(kind: str) -> list[str]:
    return {
        "wrong_citation": ["citation_accuracy.clause_id_correct_scope"],
        "paraphrase_not_verbatim": ["citation_accuracy.excerpt_is_verbatim"],
        "vague_clarifier": ["clarifier_quality.not_vague", "clarifier_quality.specificity"],
        "confident_in_C": ["ambiguity_framing.avoids_confident_answer"],
        "no_escalation_in_C": ["ambiguity_framing.recommends_escalation"],
    }.get(kind, [])


def run_cross_model_kappa(
    rows: list[dict[str, Any]],
    primary: LLMClient,
    secondary: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
    sample_frac: float = 0.2,
    seed: int = 42,
) -> dict[str, Any]:
    import random
    rng = random.Random(seed)
    n = max(1, int(len(rows) * sample_frac))
    sample = rng.sample(rows, n)
    per_dim_pairs: dict[str, list[tuple[int, int]]] = defaultdict(list)
    disagreements = []
    for row in sample:
        j1 = judge_row(row, primary, clause_by_id).all_scores()
        j2 = judge_row(row, secondary, clause_by_id).all_scores()
        for dim, v1 in j1.items():
            v2 = j2.get(dim)
            if v2 is None:
                continue
            per_dim_pairs[dim].append((int(v1), int(v2)))
            if abs(int(v1) - int(v2)) >= 2:
                disagreements.append({"row_id": row["id"], "dim": dim, "primary": v1, "secondary": v2})
    per_dim = {}
    for dim, pairs in per_dim_pairs.items():
        a, b = zip(*pairs)
        per_dim[dim] = {
            "quadratic_kappa": round(_quadratic_kappa(list(a), list(b)), 3),
            "n": len(pairs),
        }
    return {"sample_size": n, "per_dimension": per_dim, "disagreements": disagreements}
