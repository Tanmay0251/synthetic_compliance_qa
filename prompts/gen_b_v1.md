# Generator B — Clarification Required

You are generating a Q&A pair where a realistic question's answer **forks** on a specific context axis the user has not provided. You receive two related clauses that apply to different values of that axis.

## Hard rules
- The clarifying question must name the axis **specifically**. "Can you give me more detail?" is forbidden.
- The clarifying question must explain *what* about the answer would change once the axis is resolved.
- Provide two `answer_branches`, one per axis value, each with its own citation.
- The axis name (snake_case) must appear, in words, inside the clarifying question text.
- Do not answer the main `question` yourself — leave `answer` null.

## Output format
```json
{
  "question": "...",
  "persona": "...",
  "user_context": null,
  "answer": null,
  "clarifying_question": "...",
  "clarification_axis": "<snake_case_axis>",
  "answer_branches": [
    {"axis_value": "<v1>", "answer": "...", "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}]},
    {"axis_value": "<v2>", "answer": "...", "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}]}
  ],
  "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}],
  "confidence": "medium"
}
```

## Candidate clause pair (sharing topics: {shared_topics})
### Clause 1: `{c1.clause_id}` — {c1.title}
> {c1.verbatim_text}

### Clause 2: `{c2.clause_id}` — {c2.title}
> {c2.verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
