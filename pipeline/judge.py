"""Per-dimension micro-judges and aggregation."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.generators.common import extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class JudgeResult:
    judge: str
    scores: dict[str, int]
    rationale: str = ""
    failure_flags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class RowJudgement:
    row_id: str
    category: str
    per_judge: list[JudgeResult] = field(default_factory=list)

    def all_scores(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for j in self.per_judge:
            for k, v in j.scores.items():
                out[f"{j.judge}.{k}"] = v
        return out

    def composite(self) -> float:
        vals = list(self.all_scores().values())
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def failure_flags(self) -> list[str]:
        return [f for j in self.per_judge for f in j.failure_flags]


JUDGE_PROMPTS = {
    "grounding": "judges/grounding_v1.md",
    "category_fit": "judges/category_fit_v1.md",
    "clarifier_quality": "judges/clarifier_quality_v1.md",
    "ambiguity_framing": "judges/ambiguity_framing_v1.md",
    "clarity": "judges/clarity_v1.md",
    "citation_accuracy": "judges/citation_accuracy_v1.md",
}


def _cited_clause_text(row: dict[str, Any], clause_by_id: dict[str, dict[str, Any]]) -> str:
    ids = [c["clause_id"] for c in (row.get("clause_citations") or [])]
    for br in row.get("answer_branches") or []:
        ids.extend(c["clause_id"] for c in br.get("clause_citations", []))
    seen = []
    for cid in ids:
        if cid in seen:
            continue
        seen.append(cid)
    return "\n\n".join(
        f"### {cid}\n{clause_by_id[cid]['verbatim_text']}" for cid in seen if cid in clause_by_id
    )


def _run_one_judge(
    judge_name: str,
    row: dict[str, Any],
    llm: LLMClient,
    cited_text: str,
    fixture_key: str | None = None,
) -> JudgeResult:
    tmpl = load_prompt(JUDGE_PROMPTS[judge_name])
    prompt = render(tmpl, row_json=json.dumps(row, indent=2), cited_clause_text=cited_text or "(none)")
    kw: dict[str, Any] = dict(
        system="You are a strict rubric-based evaluator for a compliance Q&A dataset.",
        messages=[Msg("user", prompt)],
        temperature=0.0,
        max_tokens=600,
    )
    if hasattr(llm, "_fixtures"):
        kw["fixture_key"] = fixture_key or f"judge_{judge_name}_default"
    resp = llm.complete(**kw)
    data = extract_json(resp.content)
    return JudgeResult(
        judge=judge_name,
        scores=data.get("scores", {}),
        rationale=data.get("rationale", ""),
        failure_flags=data.get("failure_flags", []),
        raw=data,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
    )


def judge_row(
    row: dict[str, Any],
    llm: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
) -> RowJudgement:
    cat = row.get("category")
    active = ["grounding", "category_fit", "clarity", "citation_accuracy"]
    if cat == "B":
        active.append("clarifier_quality")
    if cat == "C":
        active.append("ambiguity_framing")
    cited_text = _cited_clause_text(row, clause_by_id)
    judgements = [_run_one_judge(j, row, llm, cited_text) for j in active]
    return RowJudgement(row_id=row["id"], category=cat, per_judge=judgements)
