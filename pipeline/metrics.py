"""Per-stage timing + token + cost metrics."""
from __future__ import annotations
import json
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
PRICING_PATH = ROOT / "pipeline" / "pricing.json"

with PRICING_PATH.open(encoding="utf-8") as f:
    PRICING: dict[str, dict[str, float]] = json.load(f)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    return (input_tokens / 1_000_000) * p["input_per_mtok"] + (output_tokens / 1_000_000) * p["output_per_mtok"]


@dataclass
class StageRecord:
    stage: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, out_path: Path) -> None:
        self.out_path = out_path
        self.records: list[StageRecord] = []
        self._lock = threading.Lock()
        self.started_at = time.time()

    def record(self, rec: StageRecord) -> None:
        with self._lock:
            self.records.append(rec)
            self._flush()

    def _flush(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        totals = {
            "total_cost_usd": sum(r.cost_usd for r in self.records),
            "total_input_tokens": sum(r.input_tokens for r in self.records),
            "total_output_tokens": sum(r.output_tokens for r in self.records),
            "total_wall_seconds": round(time.time() - self.started_at, 3),
            "llm_calls": sum(r.count for r in self.records),
        }
        payload = {"totals": totals, "stages": [asdict(r) for r in self.records]}
        self.out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @contextmanager
    def stage(self, name: str, model: str = "stub") -> Iterator[StageRecord]:
        rec = StageRecord(stage=name, model=model)
        t0 = time.time()
        try:
            yield rec
        finally:
            rec.latency_ms = int((time.time() - t0) * 1000)
            rec.cost_usd = cost_usd(rec.model, rec.input_tokens, rec.output_tokens)
            rec.count = max(rec.count, 1)
            self.record(rec)
