import json
from pathlib import Path
import pytest
from pipeline.retrieval import Retriever

DATA = Path(__file__).resolve().parent.parent / "data"

@pytest.fixture(scope="module")
def retriever():
    if not (DATA / "pageindex_tree.json").exists():
        pytest.skip("run `make tree` first")
    return Retriever()

def test_all_clauses(retriever):
    hits = retriever.all_clauses()
    assert len(hits) >= 20

def test_get_specific_clause(retriever):
    h = retriever.get("Part A §3.4")
    assert h.clause_id == "Part A §3.4"
    assert len(h.text) > 20

def test_silence_candidates_nonempty(retriever):
    cands = retriever.silence_candidates()
    assert len(cands) > 0

def test_pairs_by_shared_topic(retriever):
    pairs = retriever.pairs_by_shared_topic()
    assert len(pairs) > 0
    a, b = pairs[0]
    assert a.clause_id != b.clause_id
