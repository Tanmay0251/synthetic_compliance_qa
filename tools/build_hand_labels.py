"""One-off script to build eval/hand_labels.jsonl from real clause_map entries.

Each row is schema-validated. The script prints the id + injected_failure of each
item it writes, and exits nonzero if any row fails schema validation.
"""
from __future__ import annotations
import json
from pathlib import Path

from pipeline.schema import validate_row

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval" / "hand_labels.jsonl"
LABELLED_AT = "2026-04-21T11:00:00Z"


def _meta() -> dict:
    return {
        "prompt_version": "hand-label-v1",
        "model": "human-curated",
        "seed_clause_ids": [],
        "retrieval_trace": [],
        "timestamp": LABELLED_AT,
        "cost_usd": 0.0,
        "tokens": {"input": 0, "output": 0},
        "latency_ms": 0,
        "regen_count": 0,
    }


def _a_row(id_: str, q: str, a: str, citations: list[dict], confidence: str = "high") -> dict:
    return {
        "id": id_,
        "category": "A",
        "question": q,
        "persona": "backend_engineer",
        "user_context": None,
        "answer": a,
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": citations,
        "ambiguity": None,
        "confidence": confidence,
        "should_escalate": False,
        "generation_meta": _meta(),
    }


def _b_row(id_: str, q: str, clarifier: str, axis: str, branches: list[dict], citations: list[dict]) -> dict:
    return {
        "id": id_,
        "category": "B",
        "question": q,
        "persona": "cto",
        "user_context": None,
        "answer": None,
        "clarifying_question": clarifier,
        "clarification_axis": axis,
        "answer_branches": branches,
        "clause_citations": citations,
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
        "generation_meta": _meta(),
    }


def _c_row(id_: str, q: str, a: str, amb: dict, citations: list[dict]) -> dict:
    return {
        "id": id_,
        "category": "C",
        "question": q,
        "persona": "cto",
        "user_context": None,
        "answer": a,
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": citations,
        "ambiguity": amb,
        "confidence": "low",
        "should_escalate": True,
        "generation_meta": _meta(),
    }


def build_items() -> list[dict]:
    items: list[dict] = []

    # ---- 1. A good — fees-on-refund (Part B Part I §3.4) ----
    a1 = _a_row(
        "A-001",
        "We refunded a customer their full payment. Do we still have to pay Razorpay their processing fee?",
        "Yes. Razorpay PA fees shall always be applicable and payable by You on each Transaction irrespective of whether You have refunded the customer.",
        [{
            "clause_id": "Part B Part I \u00a73.4",
            "verbatim_excerpt": "Razorpay PA fees shall always be applicable and payable by You on each Transaction irrespective of whether You have refunded",
            "relevance": "direct",
        }],
    )
    items.append({
        "row": a1,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Category A; direct lift from Part B Part I \u00a73.4. Claim matches cited text verbatim.",
        "injected_failure": None,
        "labelled_at": LABELLED_AT,
    })

    # ---- 2. A good — late-authorised auto-refund window (Part B Part I §3.5) ----
    a2 = _a_row(
        "A-002",
        "If our integration fails to capture a late-authorised payment, what happens to the customer's money?",
        "Razorpay PA may initiate an auto-refund to the customer within five (5) days for payments that are late authorized but not captured by You.",
        [{
            "clause_id": "Part B Part I \u00a73.5",
            "verbatim_excerpt": "for payments that are late authorized but not captured by You, Razorpay PA may initiate auto-refund to the customer within five (5) days",
            "relevance": "direct",
        }],
    )
    items.append({
        "row": a2,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "clarity.readability": 4,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Category A; ToS explicitly states the five-day window. Verbatim excerpt is a substring of \u00a73.5.",
        "injected_failure": None,
        "labelled_at": LABELLED_AT,
    })

    # ---- 3. B good — unauthorised-debit settlement hold (Part B Part I §4.1), axis=intimation_status ----
    b1_cite = {
        "clause_id": "Part B Part I \u00a74.1",
        "verbatim_excerpt": "suspend settlements to You during the pendency of inquiries, investigations and resolution",
        "relevance": "direct",
    }
    b1 = _b_row(
        "B-001",
        "A customer claims their card was used without authorization. Can Razorpay hold our settlement money?",
        "Has a Facility Provider already intimated Razorpay that a customer reported an unauthorised debit? The availability of Razorpay's \u00a74.1 suspension right turns on whether that intimation has occurred.",
        "intimation_status",
        [
            {
                "axis_value": "intimated",
                "answer": "Yes. Once a Facility Provider intimates Razorpay of the unauthorised debit, Razorpay PA shall be entitled to suspend settlements to You during the pendency of inquiries, investigations and resolution.",
                "clause_citations": [b1_cite],
            },
            {
                "axis_value": "not_intimated",
                "answer": "No. The Part B Part I \u00a74.1 suspension right is conditioned on a Facility Provider intimating Razorpay that a customer has reported an unauthorised debit; absent that intimation, the settlement hold right under \u00a74.1 has not been triggered.",
                "clause_citations": [b1_cite],
            },
        ],
        [b1_cite],
    )
    items.append({
        "row": b1,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "clarifier_quality.specificity": 5,
            "clarifier_quality.names_axis": 5,
            "clarifier_quality.not_vague": 5,
            "clarifier_quality.explains_what_changes": 5,
            "clarity.readability": 4,
            "clarity.concision": 4,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Category B; clarifier names the load-bearing axis (intimation_status).",
        "injected_failure": None,
        "labelled_at": LABELLED_AT,
    })

    # ---- 4. B good — chargeback docs, axis=docs_availability (Part B Part I §2.2) ----
    b2_cite = {
        "clause_id": "Part B Part I \u00a72.2",
        "verbatim_excerpt": "if You are unable to furnish Chargeback Documents",
        "relevance": "direct",
    }
    b2 = _b_row(
        "B-002",
        "We received a chargeback. Will we be held liable for it?",
        "Do you have, and can you furnish, the Chargeback Documents that the Facility Provider needs? The outcome of the chargeback under Part B Part I \u00a72.2 depends on whether those documents are available and acceptable to the Facility Provider.",
        "chargeback_documents_availability",
        [
            {
                "axis_value": "documents_furnished_and_accepted",
                "answer": "If Chargeback Documents are furnished and the Facility Provider is satisfied with them, the reversal described in \u00a72.2 does not apply.",
                "clause_citations": [b2_cite],
            },
            {
                "axis_value": "documents_unavailable_or_unsatisfactory",
                "answer": "If You are unable to furnish Chargeback Documents, or the Facility Provider is not satisfied with them, the Facility Provider is entitled to order Razorpay PA to reverse the debit of the Chargeback Amount so that it is credited back to the customer.",
                "clause_citations": [b2_cite],
            },
        ],
        [b2_cite],
    )
    items.append({
        "row": b2,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "clarifier_quality.specificity": 5,
            "clarifier_quality.names_axis": 5,
            "clarifier_quality.not_vague": 5,
            "clarifier_quality.explains_what_changes": 4,
            "clarity.readability": 4,
            "clarity.concision": 4,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Category B; the chargeback outcome genuinely forks on documentation availability.",
        "injected_failure": None,
        "labelled_at": LABELLED_AT,
    })

    # ---- 5. C good — suspension duration is silent (Part A §16.1) ----
    c1_cite = {
        "clause_id": "Part A \u00a716.1",
        "verbatim_excerpt": "Razorpay PA shall have the right to immediately suspend Services and settlement",
        "relevance": "supporting",
    }
    c1 = _c_row(
        "C-001",
        "Razorpay suspended our account under Clause 16. How long can they hold our funds before releasing them?",
        "The Razorpay Terms of Use do not specify a maximum duration for fund holds following a Clause 16 suspension. What is known: Part A \u00a716.1 grants Razorpay PA the right to immediately suspend Services and settlement across a range of triggers. What is not said: any cap on how long settlements can remain held, or a release timeline. We recommend you escalate to Razorpay support in writing and engage legal counsel for any material hold.",
        {
            "type": "silent",
            "what_is_known": "Part A \u00a716.1 grants immediate suspension rights across many triggers.",
            "what_is_missing": "No maximum duration or release timeline for fund holds is defined anywhere in the ToS.",
        },
        [c1_cite],
    )
    items.append({
        "row": c1,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 4,
            "category_correctness": 5,
            "ambiguity_framing.names_silence_type": 5,
            "ambiguity_framing.avoids_confident_answer": 5,
            "ambiguity_framing.recommends_escalation": 5,
            "clarity.readability": 4,
            "clarity.concision": 4,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Category C; genuine silence, explicit escalation path named.",
        "injected_failure": None,
        "labelled_at": LABELLED_AT,
    })

    # ---- 6. A + wrong_citation — fees-on-refund question cites a chargeback clause (wrong scope) ----
    a3 = _a_row(
        "A-003",
        "We refunded a customer. Are we still on the hook for Razorpay's per-transaction fee?",
        "Yes. Razorpay PA fees remain applicable and payable on each Transaction even when you have refunded the customer.",
        [{
            # WRONG: cite Part B Part I \u00a72.1 (Chargeback) for a fees-on-refund claim
            "clause_id": "Part B Part I \u00a72.1",
            "verbatim_excerpt": "upon receipt of a Chargeback Request shall forthwith deduct Chargeback Amount from the Transaction Amounts",
            "relevance": "direct",
        }],
    )
    items.append({
        "row": a3,
        "human_scores": {
            "grounding.factual_support": 4,
            "grounding.citation_relevance": 2,
            "category_correctness": 4,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 1,
        },
        "notes": "Injected failure: answer is about fees-on-refund but citation points at the Chargeback clause (\u00a72.1). clause_id_correct_scope must be 1.",
        "injected_failure": "wrong_citation",
        "labelled_at": LABELLED_AT,
    })

    # ---- 7. A + paraphrase_not_verbatim — gaming restriction, paraphrased excerpt ----
    a4 = _a_row(
        "A-004",
        "Can we onboard a fantasy cricket platform that lets users deposit real money and win cash prizes?",
        "No. Part A \u00a714.10 prohibits using Razorpay's Services for any form of real money online gaming as defined under the Promotion and Regulation of Online Gaming Act, 2025.",
        [{
            "clause_id": "Part A \u00a714.10",
            # PARAPHRASE (not a substring of the verbatim text):
            "verbatim_excerpt": "merchants may not use Razorpay for real-money online gaming businesses under the 2025 Online Gaming Act",
            "relevance": "direct",
        }],
    )
    items.append({
        "row": a4,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 1,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Injected failure: verbatim_excerpt is a paraphrase of \u00a714.10, not an actual substring. Production deterministic validator would also catch this; we include it here specifically to test the judge.",
        "injected_failure": "paraphrase_not_verbatim",
        "labelled_at": LABELLED_AT,
    })

    # ---- 8. B + vague_clarifier — generic "tell me more" style clarifier ----
    b3_cite = {
        "clause_id": "Part B Part I \u00a74.1",
        "verbatim_excerpt": "suspend settlements to You during the pendency of inquiries, investigations and resolution",
        "relevance": "direct",
    }
    b3 = _b_row(
        "B-003",
        "A customer disputed a transaction. Can Razorpay hold our settlements?",
        "Can you tell me more about the situation?",
        "general_context",
        [
            {
                "axis_value": "intimated",
                "answer": "If a Facility Provider has intimated Razorpay of the unauthorised debit, Razorpay PA shall be entitled to suspend settlements to You during the pendency of inquiries, investigations and resolution.",
                "clause_citations": [b3_cite],
            },
            {
                "axis_value": "not_intimated",
                "answer": "Absent such intimation, the Part B Part I \u00a74.1 suspension right has not been triggered.",
                "clause_citations": [b3_cite],
            },
        ],
        [b3_cite],
    )
    items.append({
        "row": b3,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 5,
            "category_correctness": 4,
            "clarifier_quality.specificity": 1,
            "clarifier_quality.names_axis": 2,
            "clarifier_quality.not_vague": 1,
            "clarifier_quality.explains_what_changes": 3,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Injected failure: clarifier is a generic 'tell me more' with a throwaway axis 'general_context'. Branches are real but clarifier does not name the load-bearing axis.",
        "injected_failure": "vague_clarifier",
        "labelled_at": LABELLED_AT,
    })

    # ---- 9. C + confident_in_C — answer is confidently declarative despite ambiguity ----
    c2_cite = {
        "clause_id": "Part A \u00a716.1",
        "verbatim_excerpt": "Razorpay PA shall have the right to immediately suspend Services and settlement",
        "relevance": "supporting",
    }
    c2 = _c_row(
        "C-002",
        "If Razorpay suspends us under Clause 16, how many days before they have to release the funds?",
        "Yes, it is clearly 30 days. Part A \u00a716.1 gives Razorpay the right to suspend settlement, but funds must be released within thirty days of the suspension trigger. You should still escalate to Razorpay support in writing if the hold extends past this window.",
        {
            "type": "silent",
            "what_is_known": "Part A \u00a716.1 grants the right to immediately suspend Services and settlement.",
            "what_is_missing": "No specific release timeline is defined in the ToS for funds held under \u00a716.1.",
        },
        [c2_cite],
    )
    items.append({
        "row": c2,
        "human_scores": {
            "grounding.factual_support": 1,
            "grounding.citation_relevance": 5,
            "category_correctness": 5,
            "ambiguity_framing.names_silence_type": 5,
            "ambiguity_framing.avoids_confident_answer": 1,
            "ambiguity_framing.recommends_escalation": 5,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Injected failure: answer invents a '30 days' release window despite ambiguity.type=silent. avoids_confident_answer must be 1; factual_support is also 1 because the 30-day claim is ungrounded.",
        "injected_failure": "confident_in_C",
        "labelled_at": LABELLED_AT,
    })

    # ---- 10. C + no_escalation_in_C — acknowledges silence but omits escalation recommendation ----
    c3_cite = {
        "clause_id": "Part A \u00a716.1",
        "verbatim_excerpt": "Razorpay PA shall have the right to immediately suspend Services and settlement",
        "relevance": "supporting",
    }
    c3 = _c_row(
        "C-003",
        "Is there any documented SLA on how long Razorpay can hold our funds after a Clause 16 suspension?",
        "The Razorpay Terms of Use do not state a specific SLA or maximum duration for fund holds after a Clause 16 suspension. Part A \u00a716.1 grants Razorpay PA the right to immediately suspend Services and settlement, but the ToS are silent on how long the hold may last.",
        {
            "type": "silent",
            "what_is_known": "Part A \u00a716.1 grants immediate suspension rights.",
            "what_is_missing": "No SLA or release timeline for fund holds is documented in the ToS.",
        },
        [c3_cite],
    )
    items.append({
        "row": c3,
        "human_scores": {
            "grounding.factual_support": 5,
            "grounding.citation_relevance": 4,
            "category_correctness": 5,
            "ambiguity_framing.names_silence_type": 5,
            "ambiguity_framing.avoids_confident_answer": 5,
            "ambiguity_framing.recommends_escalation": 1,
            "clarity.readability": 5,
            "clarity.concision": 5,
            "citation_accuracy.excerpt_is_verbatim": 5,
            "citation_accuracy.clause_id_correct_scope": 5,
        },
        "notes": "Injected failure: names silence correctly and avoids confident answer, but omits any escalation recommendation. recommends_escalation must be 1.",
        "injected_failure": "no_escalation_in_C",
        "labelled_at": LABELLED_AT,
    })

    return items


def main() -> int:
    items = build_items()
    assert len(items) == 10, f"expected 10 items, got {len(items)}"
    any_err = False
    for i, item in enumerate(items):
        errs = validate_row(item["row"])
        if errs:
            any_err = True
            print(f"[FAIL] item {i} id={item['row']['id']}: {errs}")
    if any_err:
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    for item in items:
        print(f"{item['row']['id']} injected_failure={item['injected_failure']}")
    print(f"wrote {len(items)} items to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
