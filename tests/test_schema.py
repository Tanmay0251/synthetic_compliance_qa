import pytest
from pipeline.schema import validate_row, is_valid

def _meta() -> dict:
    return {
        "prompt_version": "gen-a-v1",
        "model": "stub",
        "seed_clause_ids": ["Part A §3.4"],
        "retrieval_trace": [],
        "timestamp": "2026-04-21T09:00:00Z",
        "cost_usd": 0.0,
        "tokens": {"input": 10, "output": 5},
        "latency_ms": 100,
        "regen_count": 0,
    }

def _cite() -> dict:
    return {
        "clause_id": "Part A §3.4",
        "verbatim_excerpt": "fees are payable on every transaction",
        "relevance": "direct",
    }

def test_valid_category_a():
    row = {
        "id": "A-001",
        "category": "A",
        "question": "We refunded a customer. Do we still owe fees?",
        "persona": "backend_engineer",
        "user_context": None,
        "answer": "Yes, fees are payable on every transaction irrespective of refund.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_valid_category_b():
    row = {
        "id": "B-001",
        "category": "B",
        "question": "Can Razorpay hold our settlement?",
        "persona": "cto",
        "user_context": None,
        "answer": None,
        "clarifying_question": "Has the Facility Provider been intimated of the unauthorised debit yet?",
        "clarification_axis": "intimation_status",
        "answer_branches": [
            {"axis_value": "intimated", "answer": "Yes, Razorpay may suspend settlements during investigation.", "clause_citations": [_cite()]},
            {"axis_value": "not_intimated", "answer": "No basis to suspend under Clause 4.1 until intimation.", "clause_citations": [_cite()]},
        ],
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_valid_category_c():
    row = {
        "id": "C-001",
        "category": "C",
        "question": "How long can Razorpay hold funds after Clause 16 suspension?",
        "persona": "cto",
        "user_context": None,
        "answer": "The ToS does not specify a maximum duration. Escalate to Razorpay.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": {
            "type": "silent",
            "what_is_known": "Clause 16.1 grants immediate suspension rights.",
            "what_is_missing": "Maximum fund-hold duration is not defined.",
        },
        "confidence": "low",
        "should_escalate": True,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_category_a_rejects_clarifying_question():
    row = {
        "id": "A-002",
        "category": "A",
        "question": "ok?",
        "persona": "x",
        "answer": "yes",
        "clarifying_question": "but what about?",
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("clarifying_question" in e for e in errs)

def test_category_c_requires_should_escalate_true():
    row = {
        "id": "C-002",
        "category": "C",
        "question": "ambiguous?",
        "persona": "x",
        "answer": "unclear",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": {"type": "silent", "what_is_known": "x", "what_is_missing": "y"},
        "confidence": "low",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("should_escalate" in e for e in errs)

def test_bad_id_format_rejected():
    row = {
        "id": "X-1",
        "category": "A",
        "question": "ok?",
        "persona": "x",
        "answer": "y",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("id" in e for e in errs)
