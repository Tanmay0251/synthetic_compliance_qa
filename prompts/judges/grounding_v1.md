# GroundingJudge

Score the following Q&A row on **grounding**: does every factual claim in the answer (or `answer_branches`) appear in, or follow directly from, the cited clauses' `verbatim_text`?

- 5: every claim is directly supported by cited text; no invention.
- 4: minor inference that a reader would accept.
- 3: one claim is weakly supported (in scope but not literally stated).
- 2: one claim contradicts or isn't in cited text.
- 1: multiple claims ungrounded or citations irrelevant.

Also rate `citation_relevance` 1–5: do the cited clauses actually address the question?

Return ONLY JSON:
```json
{"scores": {"factual_support": <1-5>, "citation_relevance": <1-5>}, "rationale": "<50 words>", "failure_flags": ["ungrounded_claim" | "irrelevant_citation" | ...]}
```

## Row
{row_json}

## Cited clause text (verbatim)
{cited_clause_text}
