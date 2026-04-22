"""One-retry regeneration on validator failure."""
from __future__ import annotations
from typing import Callable

from pipeline.generators.common import Candidate
from pipeline.validator import ValidationResult, Validator


def regen_if_needed(
    cand: Candidate,
    validator: Validator,
    regen_one: Callable[[str], Candidate | None],
    max_retries: int = 1,
) -> tuple[Candidate, ValidationResult, int]:
    result = validator.check(cand.row)
    retries = 0
    cur = cand
    while not result.passed and retries < max_retries:
        feedback = "; ".join(result.reasons)
        new = regen_one(feedback)
        if new is None:
            break
        retries += 1
        new.row["generation_meta"]["regen_count"] = retries
        new.row["id"] = cand.row["id"]
        new.row["category"] = cand.row["category"]
        cur = new
        result = validator.check(cur.row)
    return cur, result, retries
