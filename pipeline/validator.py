"""Deterministic validator for generated Q&A candidates."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HEDGE_WORDS = {"might", "unclear", "depends", "possibly", "may be", "not sure", "ambiguous"}
PRONOUN_NO_ANTECEDENT = re.compile(r"^\s*(it|this|that|they)\b", re.IGNORECASE)


@dataclass
class ValidationResult:
    passed: bool
    checks: dict[str, str] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": self.checks, "reasons": self.reasons}


class Validator:
    def __init__(self, clause_map_path: Path, md_path: Path) -> None:
        cm = json.loads(Path(clause_map_path).read_text(encoding="utf-8"))
        self._clauses: dict[str, dict[str, Any]] = {c["clause_id"]: c for c in cm["clauses"]}
        self._md: str = Path(md_path).read_text(encoding="utf-8")
        self._seen_hashes: set[str] = set()
        self._seen_clause_sets: list[tuple[str, frozenset[str]]] = []

    def reset(self) -> None:
        self._seen_hashes.clear()
        self._seen_clause_sets.clear()

    def check(self, row: dict[str, Any]) -> ValidationResult:
        r = ValidationResult(passed=True)
        self._check_citations(row, r)
        self._check_grounding(row, r)
        self._check_self_containment(row, r)
        self._check_duplicate(row, r)
        cat = row.get("category")
        if cat == "A":
            self._check_struct_a(row, r)
        elif cat == "B":
            self._check_struct_b(row, r)
        elif cat == "C":
            self._check_struct_c(row, r)
        r.passed = all(v == "ok" for v in r.checks.values())
        return r

    # Unicode quote variants that LLMs commonly normalise — treat them as equivalent when
    # checking that an excerpt is a substring of the clause text.
    _QUOTE_NORMALISE = str.maketrans({
        "“": '"', "”": '"', "‘": "'", "’": "'",
    })

    @classmethod
    def _excerpt_in_clause(cls, excerpt: str, clause_text: str) -> bool:
        if excerpt in clause_text:
            return True
        return excerpt.translate(cls._QUOTE_NORMALISE) in clause_text.translate(cls._QUOTE_NORMALISE)

    def _check_citations(self, row: dict[str, Any], r: ValidationResult) -> None:
        cites = row.get("clause_citations") or []
        if not cites and row.get("category") == "A":
            r.checks["citation_resolves"] = "fail"
            r.reasons.append("citation_resolves: Category A requires at least 1 citation")
            return

        def _check_one(label: str, c: dict[str, Any]) -> bool:
            cid = c.get("clause_id")
            clause = self._clauses.get(cid)
            if not clause:
                r.checks["citation_resolves"] = "fail"
                r.reasons.append(f"citation_resolves: unknown clause_id '{cid}' ({label})")
                return False
            excerpt = c.get("verbatim_excerpt", "")
            if not self._excerpt_in_clause(excerpt, clause["verbatim_text"]):
                r.checks["citation_resolves"] = "fail"
                r.reasons.append(f"{label}: verbatim_excerpt not a substring of {cid}")
                return False
            return True

        for i, c in enumerate(cites):
            if not _check_one(f"citation[{i}]", c):
                return
        # Also check per-branch citations — gap in v1 validator.
        for bi, br in enumerate(row.get("answer_branches") or []):
            for ci, c in enumerate(br.get("clause_citations", [])):
                if not _check_one(f"branches[{bi}].clause_citations[{ci}]", c):
                    return
        r.checks["citation_resolves"] = "ok"

    def _check_grounding(self, row: dict[str, Any], r: ValidationResult) -> None:
        answer_text = row.get("answer") or ""
        for br in row.get("answer_branches") or []:
            answer_text += " " + br.get("answer", "")
        # Extract day-count / percentage / numeric claims
        nums = re.findall(r"\b\d+\s*(?:days?|working days?|%|percent|hours?)\b", answer_text, re.IGNORECASE)
        cited_text = " ".join(
            self._clauses[c["clause_id"]]["verbatim_text"]
            for c in (row.get("clause_citations") or [])
            if c.get("clause_id") in self._clauses
        )
        ungrounded = [n for n in nums if n.lower() not in cited_text.lower()]
        if ungrounded:
            r.checks["grounding"] = "fail"
            r.reasons.append(f"grounding: numeric claims not found in any cited clause: {ungrounded}")
        else:
            r.checks["grounding"] = "ok"

    def _check_self_containment(self, row: dict[str, Any], r: ValidationResult) -> None:
        q = row.get("question", "")
        if PRONOUN_NO_ANTECEDENT.match(q):
            r.checks["self_containment"] = "fail"
            r.reasons.append(f"self_containment: question starts with pronoun without antecedent: '{q[:40]}'")
            return
        if any(p in q.lower() for p in ["previous question", "earlier you said", "as you mentioned"]):
            r.checks["self_containment"] = "fail"
            r.reasons.append("self_containment: question references prior turn")
            return
        r.checks["self_containment"] = "ok"

    def _check_duplicate(self, row: dict[str, Any], r: ValidationResult) -> None:
        q = row.get("question", "").lower().strip()
        q_hash = re.sub(r"\W+", " ", q).strip()
        cite_set = frozenset(c["clause_id"] for c in row.get("clause_citations") or [])
        if q_hash in self._seen_hashes:
            r.checks["duplicate"] = "fail"
            r.reasons.append("duplicate: identical normalised question already seen")
            return
        for seen_q, seen_cs in self._seen_clause_sets:
            if seen_cs == cite_set and self._jaccard(q_hash, seen_q) >= 0.8:
                r.checks["duplicate"] = "fail"
                r.reasons.append(f"duplicate: near-duplicate of {seen_q[:30]} with same cite set")
                return
        self._seen_hashes.add(q_hash)
        self._seen_clause_sets.append((q_hash, cite_set))
        r.checks["duplicate"] = "ok"

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa, sb = set(a.split()), set(b.split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    def _check_struct_a(self, row: dict[str, Any], r: ValidationResult) -> None:
        if not row.get("clause_citations"):
            r.checks["struct_A"] = "fail"
            r.reasons.append("struct_A: category A requires citation")
            return
        answer = (row.get("answer") or "").lower()
        hedges_found = [h for h in HEDGE_WORDS if re.search(rf"\b{re.escape(h)}\b", answer)]
        if hedges_found:
            r.checks["struct_A"] = "fail"
            r.reasons.append(f"struct_A: hedging words in clear-answer response: {hedges_found}")
            return
        r.checks["struct_A"] = "ok"

    def _check_struct_b(self, row: dict[str, Any], r: ValidationResult) -> None:
        cq = row.get("clarifying_question") or ""
        axis = row.get("clarification_axis") or ""
        branches = row.get("answer_branches") or []
        if not cq.strip():
            r.checks["struct_B"] = "fail"
            r.reasons.append("struct_B: missing clarifying_question")
            return
        if not axis.strip():
            r.checks["struct_B"] = "fail"
            r.reasons.append("struct_B: missing clarification_axis")
            return
        if axis.replace("_", " ").lower() not in cq.lower() and not any(
            tok in cq.lower() for tok in axis.lower().split("_")
        ):
            r.checks["struct_B"] = "fail"
            r.reasons.append(f"struct_B: axis '{axis}' not referenced in clarifying_question")
            return
        if len(branches) < 2:
            r.checks["struct_B"] = "fail"
            r.reasons.append("struct_B: need >=2 answer_branches")
            return
        r.checks["struct_B"] = "ok"

    def _check_struct_c(self, row: dict[str, Any], r: ValidationResult) -> None:
        amb = row.get("ambiguity")
        if not amb:
            r.checks["struct_C"] = "fail"
            r.reasons.append("struct_C: missing ambiguity block")
            return
        if amb.get("type") not in {"silent", "vague_language", "external_deferral", "multi_rule_conflict"}:
            r.checks["struct_C"] = "fail"
            r.reasons.append(f"struct_C: invalid ambiguity.type '{amb.get('type')}'")
            return
        answer = (row.get("answer") or "").lower()
        confident_markers = ["yes it is", "clearly", "definitely", "the answer is", "without doubt"]
        if any(m in answer for m in confident_markers):
            r.checks["struct_C"] = "fail"
            r.reasons.append("struct_C: confident phrasing in a genuine-ambiguity answer")
            return
        if not row.get("should_escalate"):
            r.checks["struct_C"] = "fail"
            r.reasons.append("struct_C: should_escalate must be true")
            return
        if not any(w in answer for w in ["escalate", "seek", "inform", "confirm with", "contact razorpay", "legal"]):
            r.checks["struct_C"] = "fail"
            r.reasons.append("struct_C: missing escalation recommendation in answer")
            return
        r.checks["struct_C"] = "ok"
