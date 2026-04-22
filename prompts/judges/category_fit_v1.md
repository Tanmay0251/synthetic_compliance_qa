# CategoryFitJudge

Score `category_correctness` 1–5: does this row belong in its stated category?
- A: ToS explicitly and unambiguously answers the question.
- B: answer genuinely depends on context the user hasn't given; clarifier resolves it.
- C: ToS is silent, vague, or defers externally in a way that creates genuine uncertainty.

Return ONLY JSON:
```json
{"scores": {"category_correctness": <1-5>}, "rationale": "<50 words>", "failure_flags": ["wrong_category" | "borderline" | ...]}
```

## Row
{row_json}
