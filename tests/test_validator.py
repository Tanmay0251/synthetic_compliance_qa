import json
from pathlib import Path
import pytest
from pipeline.validator import Validator, ValidationResult

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def validator():
    return Validator(
        clause_map_path=DATA / "clause_map.json",
        md_path=DATA / "razorpay_tos.md",
    )


def _base_a(validator) -> dict:
    c = next(iter(validator._clauses.values()))
    return {
        "id": "A-001",
        "category": "A",
        "question": "A realistic, self-contained question about this clause?",
        "persona": "backend_engineer",
        "answer": f"Per {c['clause_id']}: {c['verbatim_text'][:60]}",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [
            {"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:40], "relevance": "direct"}
        ],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
    }


def test_valid_a_passes(validator):
    row = _base_a(validator)
    r = validator.check(row)
    assert r.passed, r.reasons


def test_citation_to_unknown_clause_fails(validator):
    row = _base_a(validator)
    row["clause_citations"][0]["clause_id"] = "Part Z §99.99"
    r = validator.check(row)
    assert not r.passed
    assert any("citation_resolves" in x for x in r.reasons)


def test_non_substring_excerpt_fails(validator):
    row = _base_a(validator)
    row["clause_citations"][0]["verbatim_excerpt"] = "completely fabricated sentence not in the doc"
    r = validator.check(row)
    assert not r.passed
    assert any("verbatim" in x.lower() for x in r.reasons)


def test_a_with_hedging_fails(validator):
    row = _base_a(validator)
    row["answer"] = "It might depend. Unclear what applies here."
    r = validator.check(row)
    assert not r.passed
    assert any("struct_A" in x or "hedging" in x.lower() for x in r.reasons)


def test_b_missing_clarifier_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "B-001",
        "category": "B",
        "question": "Does this depend on context?",
        "persona": "cto",
        "answer": None,
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
    }
    r = validator.check(row)
    assert not r.passed


def test_b_axis_not_in_clarifier_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "B-002",
        "category": "B",
        "question": "Can it hold settlement?",
        "persona": "cto",
        "answer": None,
        "clarifying_question": "Please tell me more about the situation.",
        "clarification_axis": "intimation_status",
        "answer_branches": [
            {"axis_value": "yes", "answer": "x", "clause_citations": []},
            {"axis_value": "no", "answer": "y", "clause_citations": []},
        ],
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
    }
    r = validator.check(row)
    assert not r.passed
    assert any("axis" in x.lower() for x in r.reasons)


def test_c_confident_answer_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "C-001",
        "category": "C",
        "question": "Is it defined?",
        "persona": "cto",
        "answer": "Yes it is clearly 30 days.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": {"type": "silent", "what_is_known": "x", "what_is_missing": "y"},
        "confidence": "low",
        "should_escalate": True,
    }
    r = validator.check(row)
    assert not r.passed


def test_duplicate_question_fails(validator):
    c = next(iter(validator._clauses.values()))
    row1 = _base_a(validator)
    row1["id"] = "A-001"
    row2 = dict(row1)
    row2["id"] = "A-002"
    validator.reset()
    r1 = validator.check(row1)
    r2 = validator.check(row2)
    assert r1.passed
    assert not r2.passed
    assert any("duplicate" in x.lower() for x in r2.reasons)
