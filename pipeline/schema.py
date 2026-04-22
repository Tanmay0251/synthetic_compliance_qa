"""Dataset schema loading + validation helpers."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "dataset.schema.json"

with SCHEMA_PATH.open(encoding="utf-8") as f:
    _SCHEMA: dict[str, Any] = json.load(f)

_VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)


def validate_row(row: dict[str, Any]) -> list[str]:
    """Return list of error messages (empty if valid)."""
    return [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in _VALIDATOR.iter_errors(row)]


def is_valid(row: dict[str, Any]) -> bool:
    return not validate_row(row)


@dataclass
class ClauseCitation:
    clause_id: str
    verbatim_excerpt: str
    relevance: str  # "direct" | "supporting" | "contrast"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnswerBranch:
    axis_value: str
    answer: str
    clause_citations: list[ClauseCitation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis_value": self.axis_value,
            "answer": self.answer,
            "clause_citations": [c.to_dict() for c in self.clause_citations],
        }
