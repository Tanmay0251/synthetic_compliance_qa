import json
from pathlib import Path
import pytest

DATA = Path(__file__).resolve().parent.parent / "data"

@pytest.fixture(scope="module")
def clause_map():
    return json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))

@pytest.fixture(scope="module")
def md():
    return (DATA / "razorpay_tos.md").read_text(encoding="utf-8")

def test_clause_map_nonempty(clause_map):
    assert len(clause_map["clauses"]) >= 20

def test_all_verbatim_substrings(clause_map, md):
    for c in clause_map["clauses"]:
        assert c["verbatim_text"] in md, f"{c['clause_id']} not in MD"

def test_unique_ids(clause_map):
    ids = [c["clause_id"] for c in clause_map["clauses"]]
    assert len(ids) == len(set(ids))

def test_seed_topics_covered(clause_map):
    all_topics = set()
    for c in clause_map["clauses"]:
        all_topics.update(c.get("topics", []))
    required = {"fees", "refunds", "settlement", "chargeback", "suspension"}
    missing = required - all_topics
    assert not missing, f"missing topic coverage: {missing}"
