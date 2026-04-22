# ClarifierQualityJudge (Category B only)

Score four sub-dimensions 1–5:
- `specificity`: does the clarifier name the axis or use vague "tell me more"?
- `names_axis`: is `clarification_axis` a real axis that changes the answer?
- `not_vague`: penalise clarifiers like "can you provide more detail?".
- `explains_what_changes`: does the clarifier or its answer_branches make clear how the answer forks?

Return ONLY JSON:
```json
{"scores": {"specificity": <1-5>, "names_axis": <1-5>, "not_vague": <1-5>, "explains_what_changes": <1-5>}, "rationale": "<60 words>", "failure_flags": ["vague_clarifier" | "axis_not_load_bearing" | ...]}
```

## Row
{row_json}
