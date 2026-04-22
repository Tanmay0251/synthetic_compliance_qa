"""Generate automated failure catalogue: 3 worst items per category with root-cause notes."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from pipeline.judge import RowJudgement


# Maps a low-scoring judge dimension to a concrete rubric/code mitigation.
DIM_MITIGATIONS: dict[str, str] = {
    "category_fit.category_correctness": (
        "generator B over-produces borderline questions that could also be answered as Category A "
        "(the axis exists but isn't load-bearing). Code fix: tighten `pipeline/generators/b.py` "
        "`_select_pairs` to require that the two clauses in a pair disagree on a numeric/temporal "
        "dimension (not just share a topic). Rubric fix: add a `axis_is_load_bearing` gate to the "
        "validator that fails if a single clause can answer the question directly."
    ),
    "clarifier_quality.names_axis": (
        "the axis token appears in the clarifier but in a way that the judge didn't recognise as "
        "naming (e.g., embedded in a larger phrase). Rubric fix: have `ClarifierQualityJudge` "
        "require the axis to appear as a standalone noun phrase, not inside a conjunction."
    ),
    "clarifier_quality.explains_what_changes": (
        "clarifier describes the axis but not the consequence of resolving it. Prompt fix: "
        "`prompts/gen_b_v1.md` — add an explicit 'the answer would change from X to Y' requirement "
        "in the clarifier output, not just 'the answer depends on...'."
    ),
    "clarity.concision": (
        "long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a "
        "`< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: "
        "validator could add a `word_count` structural check."
    ),
    "clarity.readability": (
        "dense legal prose mirrored verbatim from the source. Prompt fix: tell the generator to "
        "paraphrase into plain English while preserving numbers/entities exactly. Judge fix: "
        "weaken `clarity.readability` — it's correlating with topic complexity, not author error."
    ),
    "citation_accuracy.excerpt_is_verbatim": (
        "the generator paraphrased a long clause into a shorter, clearer excerpt. The deterministic "
        "validator catches exact-match failures, but some excerpts are non-contiguous segments that "
        "the validator happens to pass because each sub-span is a substring. Code fix: require the "
        "excerpt to be a CONTIGUOUS substring; reject ellipsis-joined passages."
    ),
    "citation_accuracy.clause_id_correct_scope": (
        "citation points to a sibling clause one level off (e.g. §3.4 instead of §3.4.1). Code fix: "
        "extend the validator's `citation_resolves` check to verify the citation is at the deepest "
        "level that contains the cited excerpt verbatim."
    ),
    "ambiguity_framing.recommends_escalation": (
        "answer names escalation recipients ('contact Razorpay') but doesn't specify the "
        "mechanism (email vs dashboard ticket vs written notice per §18.1). Rubric fix: "
        "`AmbiguityFramingJudge` should require a named mechanism, not just a recipient."
    ),
    "ambiguity_framing.names_silence_type": (
        "the `ambiguity.type` doesn't match what the answer actually argues (e.g., tagged "
        "`silent` but the answer describes `external_deferral`). Code fix: post-generation "
        "classifier that re-derives the type from the answer text and rejects mismatches."
    ),
    "grounding.factual_support": (
        "a numeric or temporal claim in the answer isn't backed by any cited clause. The "
        "deterministic grounding check only matches literal day/percentage patterns; this is a "
        "miss where the model paraphrased the number into different units. Code fix: extend "
        "`_check_grounding` in `pipeline/validator.py` to normalise numeric units before matching."
    ),
    "grounding.citation_relevance": (
        "cited clause is topically related but doesn't actually answer the question. The generator "
        "retrieved a neighbor clause that shares topics but doesn't carry the specific obligation. "
        "Code fix: after generation, require the cited clause to overlap with an entity/number "
        "that also appears in the question, not just shared topic tags."
    ),
    "category_correctness": (
        "see `category_fit.category_correctness` notes above."
    ),
}

DEFAULT_MITIGATION = (
    "no automated mitigation heuristic matched this failure dimension — inspect manually and "
    "add a rule to `DIM_MITIGATIONS` in `pipeline/failure_catalogue.py` if this pattern recurs."
)


def _mitigation_for(low_dims: list[tuple[str, int]]) -> str:
    for dim, _score in low_dims:
        if dim in DIM_MITIGATIONS:
            return DIM_MITIGATIONS[dim]
    return DEFAULT_MITIGATION


def build(
    rows: list[dict[str, Any]],
    judgements: dict[str, RowJudgement],
    out_path: Path,
    top_k: int = 3,
) -> None:
    by_cat: dict[str, list[tuple[dict[str, Any], RowJudgement]]] = {"A": [], "B": [], "C": []}
    for row in rows:
        j = judgements.get(row["id"])
        if j is None:
            continue
        by_cat.setdefault(row["category"], []).append((row, j))
    lines = [
        "# Failure catalogue — auto-generated",
        "",
        "> Three lowest-scoring items per category, with root-cause notes. Not cherry-picked.",
        "> Each item lists the lowest-scoring dimensions and a specific rubric or code change "
        "that would catch it.",
        "",
    ]
    for cat in ("A", "B", "C"):
        items = by_cat[cat]
        items.sort(key=lambda rj: rj[1].composite())
        lines.append(f"## Category {cat}")
        lines.append("")
        for row, j in items[:top_k]:
            lines.append(f"### {row['id']} (composite {j.composite()})")
            lines.append(f"**Q:** {row['question']}")
            if row.get("answer"):
                lines.append(f"**A:** {row['answer']}")
            if row.get("clarifying_question"):
                lines.append(
                    f"**Clarifier:** {row['clarifying_question']} "
                    f"(axis: `{row.get('clarification_axis')}`)"
                )
            low = sorted(j.all_scores().items(), key=lambda kv: kv[1])[:3]
            lines.append("**Lowest dims:** " + ", ".join(f"`{k}`={v}" for k, v in low))
            # Deduplicate flags (a single flag may be repeated across per-judge entries).
            flags = sorted(set(j.failure_flags()))
            if flags:
                lines.append(f"**Flags:** {', '.join(flags)}")
            lines.append(
                f"**Root-cause trace:** validator={row.get('validator_report', {}).get('passed')}; "
                f"regen_count={row['generation_meta']['regen_count']}; "
                f"seed_clauses={row['generation_meta']['seed_clause_ids']}"
            )
            lines.append(f"**Mitigation proposal:** {_mitigation_for(low)}")
            lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
