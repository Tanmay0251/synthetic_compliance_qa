# AmbiguityFramingJudge (Category C only)

Score three sub-dimensions 1–5:
- `names_silence_type`: is `ambiguity.type` correct for this case?
- `avoids_confident_answer`: does the answer avoid confident resolution?
- `recommends_escalation`: does the answer name a specific escalation path?

This judge exists specifically to prevent the common failure where a judge rubber-stamps "I don't know" as a clear answer.

Return ONLY JSON:
```json
{"scores": {"names_silence_type": <1-5>, "avoids_confident_answer": <1-5>, "recommends_escalation": <1-5>}, "rationale": "<60 words>", "failure_flags": ["confident_answer_in_C" | "silence_type_wrong" | "no_escalation" | ...]}
```

## Row
{row_json}
