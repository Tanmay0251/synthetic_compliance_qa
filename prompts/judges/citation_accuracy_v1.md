# CitationAccuracyJudge

Score two sub-dimensions 1–5:
- `excerpt_is_verbatim`: is each citation's `verbatim_excerpt` actually verbatim from the clause?
- `clause_id_correct_scope`: does the cited clause_id scope match the claim (e.g., don't cite Part A §3.5 for a Clause 4 question)?

Return ONLY JSON:
```json
{"scores": {"excerpt_is_verbatim": <1-5>, "clause_id_correct_scope": <1-5>}, "rationale": "<40 words>", "failure_flags": ["wrong_scope" | "paraphrase_not_verbatim" | ...]}
```

## Row
{row_json}

## Cited clause text (verbatim)
{cited_clause_text}
