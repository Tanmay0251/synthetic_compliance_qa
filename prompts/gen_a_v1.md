# Generator A — Clear Answer

You are generating a Q&A pair for a compliance assistant. Category A means: **the Razorpay ToS explicitly and unambiguously answers the question**, and the answer just needs to cite the clause. You receive one anchor clause. Your job: produce a realistic engineer/PM question that this clause answers without interpretation.

The fundamental failure mode of Category A is framing a question that sounds general, then citing a scoped clause that only answers a narrower version of it. Your job is to prevent that.

## Step 1 — Identify the clause's scope

Read the anchor clause carefully. Is it:
- **Fully general** (applies to any merchant, any transaction)? → question can be generic.
- **Scoped** (applies only to PA-CB outward / offline devices / gaming merchants / specific transaction types / post-demerger period)? → your question MUST stay inside that scope.

If the clause is scoped, your question must explicitly name the scope (e.g., "for cross-border outward transactions under the PA-CB framework..." or "for offline POS device merchants..."). Do not ask a generic-sounding question and then cite the scoped clause; a careful reader would flag this as a scope mismatch.

## Step 2 — Ambiguity check (kill switch)

Before emitting, check: does your anchor clause ALONE unambiguously answer the question you've drafted? Signs it doesn't:
- You'd need a second clause to fully answer.
- The clause says "subject to X" or "as determined by Y" — the user still needs to check X or Y.
- Timing, amount, or procedure depends on context you haven't asked about.

If it's not unambiguously answered by this one clause, **STOP**. Emit only:
```json
{"reject": true, "reason": "<one sentence explaining what additional clause or context is needed>"}
```

## Step 3 — Emit the full Q&A

Only if Steps 1–2 passed: single JSON object, no prose fences:

```json
{
  "question": "<realistic engineer/PM question IN SCOPE of the anchor clause>",
  "persona": "backend_engineer | cto | product_manager | ops_lead | legal_pm",
  "user_context": null,
  "answer": "<direct answer; reference the clause ID; no hedging>",
  "clause_citations": [
    {"clause_id": "<anchor_clause_id>", "verbatim_excerpt": "<EXACT substring of anchor text>", "relevance": "direct"}
  ],
  "confidence": "high"
}
```

Hard rules on the emission:
- No hedging words (may, might, unclear, depends, possibly).
- `verbatim_excerpt` is a literal substring of the anchor clause text.
- Any number in your answer (days, percentages, thresholds, money amounts) MUST appear verbatim in the cited clause.
- The question must be self-contained (no pronouns without antecedents, no references to prior turns).

## Anchor clause
`{clause_id}` — {title}

> {verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Work through Steps 1–3. Output only the final JSON (either `{"reject": true, ...}` or the full Q&A object).
