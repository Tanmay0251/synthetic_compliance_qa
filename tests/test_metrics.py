import json
from pathlib import Path
from pipeline.metrics import MetricsCollector, cost_usd

def test_cost_sonnet():
    c = cost_usd("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert c == 18.0

def test_stub_is_free():
    assert cost_usd("stub", 999999, 999999) == 0.0

def test_collector_writes_json(tmp_path: Path):
    m = MetricsCollector(tmp_path / "m.json")
    with m.stage("gen.A", model="stub") as r:
        r.input_tokens = 10
        r.output_tokens = 5
    data = json.loads((tmp_path / "m.json").read_text())
    assert data["stages"][0]["stage"] == "gen.A"
    assert data["stages"][0]["input_tokens"] == 10
    assert data["totals"]["llm_calls"] == 1
    assert data["totals"]["total_cost_usd"] == 0.0

def test_collector_accumulates(tmp_path: Path):
    m = MetricsCollector(tmp_path / "m.json")
    with m.stage("a", model="stub"): pass
    with m.stage("b", model="stub"): pass
    data = json.loads((tmp_path / "m.json").read_text())
    assert len(data["stages"]) == 2
