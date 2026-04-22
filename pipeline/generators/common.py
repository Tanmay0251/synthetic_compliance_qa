"""Shared utilities for generators A/B/C."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.llm import LLMClient, Msg, Response
from pipeline.retrieval import ClauseHit

ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS = ROOT / "prompts"
RAW_DUMP_DIR = ROOT / "runs" / "_raw_dumps"

PERSONAS = ["backend_engineer", "cto", "product_manager", "ops_lead", "legal_pm"]


def dump_raw(stage: str, idx: int, content: str, err: str) -> Path:
    """Save a failed LLM response for post-mortem. Returns the file path written."""
    RAW_DUMP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = RAW_DUMP_DIR / f"{ts}_{stage}_{idx:03d}.txt"
    path.write_text(f"=== ERROR ===\n{err}\n\n=== RAW CONTENT ===\n{content}\n", encoding="utf-8")
    return path


def load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


@dataclass
class Candidate:
    row: dict[str, Any]
    fixture_key: str = ""
    meta_patch: dict[str, Any] = field(default_factory=dict)


def render(template: str, vars: dict[str, Any] | None = None, **kwargs: Any) -> str:
    """Render a template by substituting `{key}` placeholders.

    Accepts either a dict (for keys that contain dots or other non-identifier
    characters that Python keyword arguments cannot express) or **kwargs, or
    both. The dict is applied first, then kwargs, so kwargs override.
    """
    all_vars: dict[str, Any] = dict(vars or {})
    all_vars.update(kwargs)
    out = template
    for k, v in all_vars.items():
        out = out.replace("{" + k + "}", str(v) if v is not None else "")
    return out


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1:
        raise ValueError(f"no JSON object in response: {text[:120]}")
    blob = text[first : last + 1]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass
    # Attempt 2: strip trailing commas before } or ] (a common LLM tic).
    cleaned = re.sub(r",(\s*[}\]])", r"\1", blob)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Attempt 3: some models emit unescaped control characters inside strings.
    cleaned2 = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", cleaned)
    try:
        return json.loads(cleaned2)
    except json.JSONDecodeError:
        pass
    # Attempt 4: hand off to json_repair for ambitious fixes (embedded unescaped quotes, etc.).
    try:
        import json_repair  # type: ignore
        repaired = json_repair.loads(cleaned2)
        if isinstance(repaired, dict):
            return repaired
    except Exception:
        pass
    # Give up with a diagnostic.
    try:
        json.loads(cleaned2)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"extract_json failed after 4 attempts: {e.msg} at line {e.lineno} col {e.colno}. "
            f"Snippet around error: {cleaned2[max(0, e.pos-80):e.pos+80]!r}"
        ) from e
    raise ValueError("extract_json: unreachable")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_meta(
    *,
    prompt_version: str,
    model: str,
    seed_clause_ids: list[str],
    retrieval_trace: list[dict[str, Any]],
    response: Response,
    regen_count: int = 0,
    cost_usd: float = 0.0,
    latency_ms: int = 0,
) -> dict[str, Any]:
    return {
        "prompt_version": prompt_version,
        "model": model,
        "seed_clause_ids": seed_clause_ids,
        "retrieval_trace": retrieval_trace,
        "timestamp": now_iso(),
        "cost_usd": cost_usd,
        "tokens": {"input": response.input_tokens, "output": response.output_tokens},
        "latency_ms": latency_ms,
        "regen_count": regen_count,
    }
