import json
from pathlib import Path
import pytest
from pipeline.llm import StubClient
from pipeline.judge import judge_row
from pipeline.schema import validate_row

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EVAL = ROOT / "eval"


@pytest.fixture(scope="module")
def clause_by_id():
    cm = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    return {c["clause_id"]: c for c in cm["clauses"]}


def test_judge_a_row(clause_by_id):
    row = {
        "id": "A-001", "category": "A",
        "question": "x", "answer": "y",
        "clause_citations": [{"clause_id": list(clause_by_id.keys())[0], "verbatim_excerpt": "x", "relevance": "direct"}],
    }
    j = judge_row(row, StubClient(), clause_by_id)
    names = {r.judge for r in j.per_judge}
    assert {"grounding", "category_fit", "clarity", "citation_accuracy"}.issubset(names)
    assert "clarifier_quality" not in names


def test_judge_b_row_adds_clarifier(clause_by_id):
    row = {"id": "B-001", "category": "B", "question": "x", "clarifying_question": "y", "clarification_axis": "z", "answer_branches": [], "clause_citations": []}
    j = judge_row(row, StubClient(), clause_by_id)
    assert any(r.judge == "clarifier_quality" for r in j.per_judge)


def test_judge_c_row_adds_ambiguity_judge(clause_by_id):
    row = {"id": "C-001", "category": "C", "question": "x", "answer": "y", "ambiguity": {"type": "silent", "what_is_known": "", "what_is_missing": ""}, "clause_citations": []}
    j = judge_row(row, StubClient(), clause_by_id)
    assert any(r.judge == "ambiguity_framing" for r in j.per_judge)


def test_quadratic_kappa_perfect_agreement():
    from pipeline.judge_validation import _quadratic_kappa
    assert _quadratic_kappa([5, 4, 3, 2, 1], [5, 4, 3, 2, 1]) == 1.0


def test_quadratic_kappa_disagreement():
    from pipeline.judge_validation import _quadratic_kappa
    k = _quadratic_kappa([5, 5, 5, 5], [1, 1, 1, 1])
    assert k < 0.1


def test_hand_labels_schema_valid():
    items = [
        json.loads(line)
        for line in (EVAL / "hand_labels.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(items) == 10, f"expected 10 items, got {len(items)}"
    for item in items:
        errs = validate_row(item["row"])
        assert not errs, f"row {item['row']['id']} failed schema: {errs}"
