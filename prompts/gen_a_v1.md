# Generator A — Clear Answer

You are generating a Q&A pair for a compliance assistant. The user is an engineer/CTO/PM at a startup using Razorpay. You will be given one anchor clause from the Razorpay General Terms of Use. Your job: produce a realistic, self-contained question that this clause **clearly and unambiguously answers**, plus the direct answer citing the clause.

## Hard rules
- The question must sound like something a real engineer or PM would ask in Slack — concrete scenario, not a legal quiz.
- The answer must be directly supported by the anchor clause. Do NOT add facts not present in the clause text.
- No hedging words (may, might, unclear, depends, possibly).
- The `verbatim_excerpt` in your citation MUST be an exact substring of the anchor clause text provided to you.
- Numbers in your answer (days, percentages, thresholds) MUST appear verbatim in the cited clause.

## Output format
Return a single JSON object (no prose, no markdown):
```json
{
  "question": "...",
  "persona": "backend_engineer | cto | product_manager | ops_lead | legal_pm",
  "user_context": null,
  "answer": "...",
  "clause_citations": [{"clause_id": "<anchor_clause_id>", "verbatim_excerpt": "<substring of anchor text>", "relevance": "direct"}],
  "confidence": "high"
}
```

## Anchor clause
`{clause_id}` — {title}

> {verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
