# Generator C — Genuine Ambiguity

You are generating a Q&A pair for a compliance assistant. Category C means: **the Razorpay ToS is genuinely silent, uses vague language, defers externally, or has conflicting rules** — creating real uncertainty that a careful reader cannot resolve from the document alone.

The fundamental failure mode of Category C is inventing silence where the ToS actually does answer the question if you look elsewhere. Your job is to prevent that.

## Step 1 — Frame the question within the silence

Look at the candidate clause and the silence hint. Draft a question that:
- A real engineer / CTO / PM would ask in Slack.
- Sits at the **boundary** of what the clause says — asks about a detail the clause does not specify.
- Does not have a clean answer elsewhere in the ToS.

## Step 2 — Silence verification (kill switch)

Before emitting, check honestly: could the Razorpay ToS answer this question if the user just read the right section? Signs it could:
- The candidate clause actually defines the thing (you're inventing silence).
- A standard clause (fees, settlement timing, chargeback flow) plainly answers it.
- You're asking about a generic commercial concept the ToS does cover.

If the ToS can answer this directly, **STOP**. Emit only:
```json
{"reject": true, "reason": "<one sentence — which clause does answer this>"}
```

## Step 3 — Emit the full Q&A

Only if Step 2 passed: single JSON object, no prose:

```json
{
  "question": "<realistic engineer/PM question that probes the silence>",
  "persona": "backend_engineer | cto | product_manager | ops_lead | legal_pm",
  "user_context": null,
  "answer": "<4-6 sentences: name what IS known from the cited clause, state specifically what the ToS does NOT define, recommend a NAMED escalation path (Razorpay dashboard ticket / written notice under §18 / RBI circular review / external legal counsel — not generic 'contact someone')>",
  "clause_citations": [
    {"clause_id": "<provided candidate clause>", "verbatim_excerpt": "<EXACT substring of its verbatim_text>", "relevance": "supporting"}
  ],
  "ambiguity": {
    "type": "silent | vague_language | external_deferral | multi_rule_conflict",
    "what_is_known": "<one sentence — the provable fact from the clause>",
    "what_is_missing": "<one sentence — the specific gap that forces escalation>"
  },
  "confidence": "low",
  "should_escalate": true
}
```

Hard rules on the emission:
- Forbidden phrasings in `answer`: "yes it is", "the answer is", "definitely", "clearly", "without doubt". These mean you've given a confident resolution, which is not Category C.
- `verbatim_excerpt` is a literal substring of the candidate clause (no paraphrase).
- `ambiguity.type` must match the flavor of silence you found.

## Candidate clause

`{clause_id}` — {title}

> {verbatim_text}

## Silence hint
{silence_hint}

## Previous attempt feedback (if any)
{regen_feedback}

Work through Steps 1–3. Output only the final JSON (either `{"reject": true, ...}` or the full Q&A object).
