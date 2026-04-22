"""Generator B — clarification required."""
from __future__ import annotations
import json as _json
import random
from pathlib import Path

from pipeline.generators.common import Candidate, build_meta, dump_raw, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever

PROMPT_VERSION = "gen-b-v3"
TEMPLATE_NAME = "gen_b_v1.md"


def _select_pairs(
    retriever: Retriever,
    n: int,
    rng: random.Random,
    exclude_pair_ids: set[frozenset[str]] | None = None,
    max_single_clause_uses: int = 2,
) -> list[tuple[ClauseHit, ClauseHit, list[str]]]:
    """Pick `n` distinct clause pairs for Category B generation.

    Diversity guards:
    - skips pairs whose (frozenset of ids) is in `exclude_pair_ids`
    - limits how many times any single clause can appear across picked pairs
    """
    exclude_pair_ids = exclude_pair_ids or set()
    pairs_all = retriever.pairs_by_shared_topic(min_shared=1)
    cm = _json.loads(retriever.clause_map_path.read_text(encoding="utf-8"))
    by_id = {c["clause_id"]: c for c in cm["clauses"]}
    scored: list[tuple[int, ClauseHit, ClauseHit, list[str]]] = []
    for a, b in pairs_all:
        ta = set(by_id[a.clause_id].get("topics", []))
        tb = set(by_id[b.clause_id].get("topics", []))
        shared = sorted(ta & tb)
        if frozenset({a.clause_id, b.clause_id}) in exclude_pair_ids:
            continue
        scored.append((len(shared), a, b, shared))
    # Random order (not just shuffle of top) so diverse topics come through
    rng.shuffle(scored)
    # Light bias: prefer higher-shared-count pairs with stable sort
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[tuple[ClauseHit, ClauseHit, list[str]]] = []
    clause_uses: dict[str, int] = {}
    for _score, a, b, shared in scored:
        if clause_uses.get(a.clause_id, 0) >= max_single_clause_uses:
            continue
        if clause_uses.get(b.clause_id, 0) >= max_single_clause_uses:
            continue
        out.append((a, b, shared))
        clause_uses[a.clause_id] = clause_uses.get(a.clause_id, 0) + 1
        clause_uses[b.clause_id] = clause_uses.get(b.clause_id, 0) + 1
        if len(out) >= n:
            break
    rng.shuffle(out)
    return out[:n]


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
    exclude_pair_ids: set[frozenset[str]] | None = None,
) -> list[Candidate]:
    rng = random.Random(seed + 1)
    template = load_prompt(TEMPLATE_NAME)
    pairs = _select_pairs(retriever, n, rng, exclude_pair_ids=exclude_pair_ids)
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
            max_tokens=1800,
            seed=seed + i,
            fixture_key="gen_b_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1800,
            seed=seed + i,
        )
        try:
            data = extract_json(resp.content)
        except (ValueError, Exception) as e:
            p = dump_raw("gen_b", i, resp.content, str(e))
            print(f"[gen B] candidate {i} JSON parse failed, skipped (raw dumped to {p.name})")
            continue
        # LLM self-rejection: the load-bearing axis check failed inside the prompt.
        if data.get("reject"):
            print(f"[gen B] candidate {i} self-rejected: {data.get('reason', '(no reason)')[:120]}")
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
