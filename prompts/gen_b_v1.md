# Generator B — Clarification Required

You are generating a Q&A pair for a compliance assistant. Category B means: **a realistic engineer/PM question whose correct answer genuinely forks on a specific context axis the user has not given.** You receive two clauses that apply to different values of that axis.

The fundamental failure mode of Category B is producing a question that a careful reader could answer directly (Category A) by simply citing both clauses. Your job is to prevent that.

## Step 1 — Identify the load-bearing axis

Before writing anything user-facing, in your own reasoning:
- Read both clauses. What SINGLE context variable changes the answer? Name it as `snake_case`.
- The axis must be something a real user WOULD NOT have stated up front. Things like "are you asking about X or Y?" where the answer genuinely differs.
- NOT a valid axis: "which clause do you want me to look at" (user doesn't care), "what is your business type" (if both clauses apply regardless), "have you already done X" (if both clauses apply independently of timing).

## Step 2 — Draft the question WITHOUT revealing the axis value

Now draft the merchant-voice question. The question MUST leave the axis genuinely open:
- Do NOT mention the distinguishing fact that pins the axis to a specific value. If your axis is `recovery_trigger_type` (penalty vs. chargeback), the question must NOT say "we got hit with a card-network penalty" — that collapses the axis.
- Do NOT include the distinguishing entity ("my Group Entity lending contract", "a separate service agreement", "a card-association fine") if the axis is about that very distinction.
- A good B question sounds genuinely ambiguous — a reader should be able to imagine answering it under either axis value before seeing the clarifier.

Self-check: read your draft question. Ask: "Does this sentence already tell me which clause applies?" If yes, rewrite it more generally (e.g., "Razorpay is recovering something from our settlement" instead of "Razorpay is recovering a card-network fine from our settlement").

## Step 3 — Write the two branch conclusions

Privately draft:
- Conclusion if `axis = value_1`: one sentence. What must the user actually do / expect?
- Conclusion if `axis = value_2`: one sentence. What must the user actually do / expect?

Each branch must cite a DIFFERENT clause (or the same clause used in a materially different way). If both branches would cite the same excerpt, the axis is actually a factual pre-condition already contained in one clause — reject.

## Step 4 — Divergence check (this is the kill switch)

Compare the two conclusions. Do they lead to **materially different operational outcomes**?
- Different dollar amounts, different deadlines, different required paperwork, different yes/no decision, different responsible party — these are divergent.
- Both say "you still owe fees" / "you must still comply" / "the same obligation applies just via a different route" — NOT divergent. Both clauses apply concurrently; the answer is the same either way.
- Both cite the SAME clause text — NOT divergent. It's one answer dressed as two.

**If the two conclusions converge, or if both branches cite the same excerpt, or if the question already answered the axis, STOP.** Emit this JSON and nothing else:
```json
{"reject": true, "reason": "<one-sentence explanation: converges, or question pre-reveals axis, or same excerpt>"}
```

Do not try to force a different axis; do not produce a partial answer. Just reject.

## Step 5 — Emit the full Q&A

Only if Step 4 passed: produce a single JSON object (no prose, no markdown fences):

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
