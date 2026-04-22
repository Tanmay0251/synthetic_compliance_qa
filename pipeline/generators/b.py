"""Generator B — clarification required."""
from __future__ import annotations
import json as _json
import random
from pathlib import Path

from pipeline.generators.common import Candidate, build_meta, dump_raw, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever

PROMPT_VERSION = "gen-b-v1"
TEMPLATE_NAME = "gen_b_v1.md"


def _select_pairs(retriever: Retriever, n: int, rng: random.Random) -> list[tuple[ClauseHit, ClauseHit, list[str]]]:
    pairs_all = retriever.pairs_by_shared_topic(min_shared=1)
    cm = _json.loads(retriever.clause_map_path.read_text(encoding="utf-8"))
    by_id = {c["clause_id"]: c for c in cm["clauses"]}
    scored: list[tuple[int, ClauseHit, ClauseHit, list[str]]] = []
    for a, b in pairs_all:
        ta = set(by_id[a.clause_id].get("topics", []))
        tb = set(by_id[b.clause_id].get("topics", []))
        shared = sorted(ta & tb)
        scored.append((len(shared), a, b, shared))
    scored.sort(key=lambda x: x[0], reverse=True)
    rng.shuffle(scored)
    out = [(a, b, s) for (_, a, b, s) in scored[: n * 2]]
    rng.shuffle(out)
    return out[:n]


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
) -> list[Candidate]:
    rng = random.Random(seed + 1)
    template = load_prompt(TEMPLATE_NAME)
    pairs = _select_pairs(retriever, n, rng)
    out: list[Candidate] = []
    for i, (c1, c2, shared) in enumerate(pairs):
        prompt_vars = {
            "shared_topics": ", ".join(shared) or "(none)",
            "c1.clause_id": c1.clause_id,
            "c1.title": c1.title,
            "c1.verbatim_text": c1.text,
            "c2.clause_id": c2.clause_id,
            "c2.title": c2.title,
            "c2.verbatim_text": c2.text,
            "regen_feedback": regen_feedback or "(none)",
        }
        prompt = render(template, prompt_vars)
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1500,
            seed=seed + i,
            fixture_key="gen_b_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1500,
            seed=seed + i,
        )
        try:
            data = extract_json(resp.content)
        except (ValueError, Exception) as e:
            p = dump_raw("gen_b", i, resp.content, str(e))
            print(f"[gen B] candidate {i} JSON parse failed, skipped (raw dumped to {p.name})")
            continue
        data["id"] = f"B-{len(out)+1:03d}"
        data["category"] = "B"
        data["answer"] = None
        data["ambiguity"] = None
        data["should_escalate"] = data.get("should_escalate", False)
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[c1.clause_id, c2.clause_id],
            retrieval_trace=[{"mode": "pair", "pair": [c1.clause_id, c2.clause_id], "shared_topics": shared}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
