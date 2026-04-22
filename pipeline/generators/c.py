"""Generator C — genuine ambiguity."""
from __future__ import annotations
import random
from pathlib import Path

from pipeline.generators.common import Candidate, build_meta, dump_raw, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever

PROMPT_VERSION = "gen-c-v1"
TEMPLATE_NAME = "gen_c_v1.md"

SILENCE_HINTS = {
    "silent": "The ToS does not address this topic at all.",
    "vague_language": "The ToS uses qualitative language ('reasonable', 'as determined') without specifying thresholds.",
    "external_deferral": "The ToS defers to external regulation (RBI / NPCI / state law) without defining boundaries.",
    "multi_rule_conflict": "Two or more clauses could apply and give different answers without an explicit reconciliation.",
}


def _select_candidates(retriever: Retriever, n: int, rng: random.Random) -> list[tuple[ClauseHit, str]]:
    silent_cands = retriever.silence_candidates()
    rng.shuffle(silent_cands)
    out: list[tuple[ClauseHit, str]] = []
    for h in silent_cands:
        t_lower = h.text.lower()
        if any(m in t_lower for m in ["per rbi", "per npci", "as per", "in accordance with"]):
            hint = SILENCE_HINTS["external_deferral"]
        elif any(m in t_lower for m in ["reasonable", "as determined", "from time to time"]):
            hint = SILENCE_HINTS["vague_language"]
        elif any(m in t_lower for m in ["may suspend", "may terminate"]):
            hint = SILENCE_HINTS["silent"]
        else:
            hint = SILENCE_HINTS["silent"]
        out.append((h, hint))
        if len(out) >= n:
            break
    while len(out) < n:
        h = rng.choice(retriever.all_clauses())
        out.append((h, SILENCE_HINTS["silent"]))
    return out


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
) -> list[Candidate]:
    rng = random.Random(seed + 2)
    template = load_prompt(TEMPLATE_NAME)
    cands = _select_candidates(retriever, n, rng)
    out: list[Candidate] = []
    for i, (h, hint) in enumerate(cands):
        prompt = render(
            template,
            clause_id=h.clause_id,
            title=h.title,
            verbatim_text=h.text,
            silence_hint=hint,
            regen_feedback=regen_feedback or "(none)",
        )
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
            fixture_key="gen_c_default",
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
            p = dump_raw("gen_c", i, resp.content, str(e))
            print(f"[gen C] candidate {i} JSON parse failed, skipped (raw dumped to {p.name})")
            continue
        data["id"] = f"C-{len(out)+1:03d}"
        data["category"] = "C"
        data["clarifying_question"] = None
        data["clarification_axis"] = None
        data["answer_branches"] = None
        data["should_escalate"] = True
        data["confidence"] = "low"
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[h.clause_id],
            retrieval_trace=[{"mode": "silence", "clause_id": h.clause_id, "silence_hint": hint}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
