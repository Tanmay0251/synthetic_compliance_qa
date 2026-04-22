"""Generator A — clear answer."""
from __future__ import annotations
import random
from pathlib import Path
from typing import Any

from pipeline.generators.common import Candidate, build_meta, dump_raw, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever


PROMPT_VERSION = "gen-a-v2"
TEMPLATE_NAME = "gen_a_v1.md"


def _select_anchors(
    retriever: Retriever,
    n: int,
    rng: random.Random,
    exclude_clause_ids: set[str] | None = None,
) -> list[ClauseHit]:
    """Prefer clauses with concrete numbers / day-counts / percentages (A-friendly)."""
    import re as _re
    exclude = set(exclude_clause_ids or [])
    candidates = []
    for h in retriever.all_clauses():
        if h.clause_id in exclude:
            continue
        if _re.search(r"\b\d+\s*(days?|%|percent|hours?|working\s+days?)\b", h.text, _re.IGNORECASE):
            candidates.append(h)
    if len(candidates) < n:
        extras = [h for h in retriever.all_clauses() if h.clause_id not in exclude and h not in candidates]
        rng.shuffle(extras)
        candidates.extend(extras)
    rng.shuffle(candidates)
    return candidates[:n]


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
    anchor_override: list[ClauseHit] | None = None,
    exclude_clause_ids: set[str] | None = None,
) -> list[Candidate]:
    rng = random.Random(seed)
    template = load_prompt(TEMPLATE_NAME)
    anchors = anchor_override if anchor_override is not None else _select_anchors(
        retriever, n, rng, exclude_clause_ids=exclude_clause_ids
    )
    out: list[Candidate] = []
    for i, anchor in enumerate(anchors):
        prompt = render(
            template,
            clause_id=anchor.clause_id,
            title=anchor.title,
            verbatim_text=anchor.text,
            regen_feedback=regen_feedback or "(none)",
        )
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
            fixture_key="gen_a_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
        )
        try:
            data = extract_json(resp.content)
        except (ValueError, Exception) as e:
            p = dump_raw("gen_a", i, resp.content, str(e))
            print(f"[gen A] candidate {i} JSON parse failed, skipped (raw dumped to {p.name})")
            continue
        if data.get("reject"):
            print(f"[gen A] candidate {i} self-rejected: {data.get('reason', '')[:120]}")
            continue
        data["id"] = f"A-{len(out)+1:03d}"
        data["category"] = "A"
        data["clarifying_question"] = None
        data["clarification_axis"] = None
        data["answer_branches"] = None
        data["ambiguity"] = None
        data["should_escalate"] = data.get("should_escalate", False)
        data.setdefault("confidence", "high")
        data.setdefault("user_context", None)
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[anchor.clause_id],
            retrieval_trace=[{"mode": "anchor", "clause_id": anchor.clause_id}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
