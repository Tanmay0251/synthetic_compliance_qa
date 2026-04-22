# Generator C — Genuine Ambiguity

You are generating a Q&A pair where the Razorpay ToS is **silent, vague, or defers externally** — producing a genuine regulatory gap. You receive one candidate clause (the closest thing the ToS says) and a silence-type hint.

## Hard rules
- The answer MUST NOT give a confident resolution. Forbidden phrases: "yes it is", "the answer is", "definitely", "clearly", "without doubt".
- The answer MUST name what is known (citing the candidate clause), explicitly describe what the ToS does *not* say, and recommend a named escalation path (Razorpay support, legal counsel, RBI/NPCI guidance).
- `ambiguity.type` must be one of: `silent`, `vague_language`, `external_deferral`, `multi_rule_conflict`.
- `should_escalate` must be `true`.
- `confidence` must be `low`.

## Output format
```json
{
  "question": "...",
  "persona": "...",
  "user_context": null,
  "answer": "...",
  "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "supporting"}],
  "ambiguity": {
    "type": "silent | vague_language | external_deferral | multi_rule_conflict",
    "what_is_known": "...",
    "what_is_missing": "..."
  },
  "confidence": "low",
  "should_escalate": true
}
```

## Candidate clause
`{clause_id}` — {title}

> {verbatim_text}

## Silence hint
{silence_hint}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
