from pathlib import Path
import pytest
from pipeline.llm import StubClient
from pipeline.retrieval import Retriever
from pipeline.generators import a, b, c

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def retriever():
    if not (DATA / "pageindex_tree.json").exists():
        pytest.skip("run `make tree` first")
    return Retriever()


@pytest.fixture
def stub():
    return StubClient()


def test_gen_a_produces_candidates(retriever, stub):
    cands = a.generate(n=2, retriever=retriever, llm=stub, seed=42)
    assert len(cands) == 2
    for cand in cands:
        assert cand.row["category"] == "A"
        assert cand.row["id"].startswith("A-")
        assert cand.row["answer"]
        assert cand.row["clause_citations"]


def test_gen_b_has_branches(retriever, stub):
    cands = b.generate(n=1, retriever=retriever, llm=stub, seed=42)
    assert cands[0].row["category"] == "B"
    assert cands[0].row["clarifying_question"]
    assert len(cands[0].row["answer_branches"]) >= 2


def test_gen_c_is_escalating(retriever, stub):
    cands = c.generate(n=1, retriever=retriever, llm=stub, seed=42)
    assert cands[0].row["category"] == "C"
    assert cands[0].row["should_escalate"] is True
    assert cands[0].row["confidence"] == "low"
    assert cands[0].row["ambiguity"]["type"] in {"silent", "vague_language", "external_deferral", "multi_rule_conflict"}


from pipeline.regen import regen_if_needed
from pipeline.validator import Validator


def test_regen_passes_through_valid(retriever, stub):
    from pipeline.generators import a as gen_a
    v = Validator(clause_map_path=DATA / "clause_map.json", md_path=DATA / "razorpay_tos.md")
    cands = gen_a.generate(n=1, retriever=retriever, llm=stub, seed=42)

    def regen_one(feedback: str):
        return gen_a.generate(n=1, retriever=retriever, llm=stub, seed=999, regen_feedback=feedback)[0]

    final, result, retries = regen_if_needed(cands[0], v, regen_one)
    # Stub always returns the same valid row for gen_a_default -> no retries needed.
    assert retries == 0
    assert result.passed
