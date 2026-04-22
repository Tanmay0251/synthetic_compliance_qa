# Generator B — Clarification Required

You are generating a Q&A pair for a compliance assistant. Category B means: **a realistic engineer/PM question whose correct answer genuinely forks on a specific context axis the user has not given.** You receive two clauses that apply to different values of that axis.

The fundamental failure mode of Category B is producing a question that a careful reader could answer directly (Category A) by simply citing both clauses. Your job is to prevent that.

## Step 1 — Identify the load-bearing axis

Before writing anything user-facing, in your own reasoning:
- Read both clauses. What SINGLE context variable changes the answer? Name it as `snake_case`.
- The axis must be something a real user WOULD NOT have stated up front. Things like "are you asking about X or Y?" where the answer genuinely differs.
- NOT a valid axis: "which clause do you want me to look at" (user doesn't care), "what is your business type" (if both clauses apply regardless), "have you already done X" (if both clauses apply independently of timing).

## Step 2 — Write the two branch conclusions

Privately draft:
- Conclusion if `axis = value_1`: one sentence. What must the user actually do / expect?
- Conclusion if `axis = value_2`: one sentence. What must the user actually do / expect?

## Step 3 — Divergence check (this is the kill switch)

Compare the two conclusions. Do they lead to **materially different operational outcomes**?
- Different dollar amounts, different deadlines, different required paperwork, different yes/no decision, different responsible party — these are divergent.
- Both say "you still owe fees" / "you must still comply" / "the same obligation applies just via a different route" — NOT divergent. Both clauses apply concurrently; the answer is the same either way.

**If the two conclusions converge operationally, STOP.** Emit this JSON and nothing else:
```json
{"reject": true, "reason": "<one-sentence explanation of why the axis is not load-bearing>"}
```

Do not try to force a different axis; do not produce a partial answer. Just reject.

## Step 4 — Emit the full Q&A

Only if Step 3 passed: produce a single JSON object (no prose, no markdown fences):

```json
{
  "question": "<a realistic question in engineer/PM voice; NO clarifying framing in the question itself>",
  "persona": "backend_engineer | cto | product_manager | ops_lead | legal_pm",
  "user_context": null,
  "answer": null,
  "clarifying_question": "<specific clarifier that names the axis IN WORDS, and names what would change — e.g. 'Has the Facility Provider been intimated yet? If yes, Razorpay may suspend settlements; if not, the suspension right hasn't been triggered.'>",
  "clarification_axis": "<snake_case_axis_from_step_1>",
  "answer_branches": [
    {"axis_value": "<value_1>", "answer": "<branch conclusion from step 2>", "clause_citations": [{"clause_id": "<use one of the two provided>", "verbatim_excerpt": "<EXACT substring of that clause>", "relevance": "direct"}]},
    {"axis_value": "<value_2>", "answer": "<branch conclusion from step 2>", "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}]}
  ],
  "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}],
  "confidence": "medium"
}
```

Hard rules on the emission:
- Each `verbatim_excerpt` MUST be a literal substring of the provided clause text (no paraphrase, no ellipsis-joined spans).
- The axis tokens (split by `_`) must appear as recognisable words in the clarifying_question.
- Do not write an `answer` field — leave it null. The whole point is that you're not answering without the clarifier.

## Candidate clause pair (sharing topics: {shared_topics})

### Clause 1: `{c1.clause_id}` — {c1.title}
> {c1.verbatim_text}

### Clause 2: `{c2.clause_id}` — {c2.title}
> {c2.verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Now work through Steps 1–4. Output only the final JSON (either the `{"reject": true, ...}` object or the full Q&A object).
