"""PageIndex-backed retrieval with clause-map cross-walk."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ClauseHit:
    clause_id: str
    title: str
    text: str
    line_start: int
    line_end: int
    score: float = 0.0
    node_path: list[str] = None  # type: ignore[assignment]


class Retriever:
    def __init__(
        self,
        tree_path: Path | None = None,
        clause_map_path: Path | None = None,
    ) -> None:
        self.tree_path = tree_path or ROOT / "data" / "pageindex_tree.json"
        self.clause_map_path = clause_map_path or ROOT / "data" / "clause_map.json"
        self._tree = json.loads(self.tree_path.read_text(encoding="utf-8"))
        cm = json.loads(self.clause_map_path.read_text(encoding="utf-8"))
        self._clause_by_id: dict[str, dict[str, Any]] = {c["clause_id"]: c for c in cm["clauses"]}
        self._all_clauses: list[dict[str, Any]] = cm["clauses"]

    def all_clauses(self) -> list[ClauseHit]:
        return [self._to_hit(c) for c in self._all_clauses]

    def get(self, clause_id: str) -> ClauseHit:
        return self._to_hit(self._clause_by_id[clause_id])

    def query(self, nl_query: str, top_k: int = 5) -> list[ClauseHit]:
        """Naive scoring: topic-keyword + title-substring overlap. PageIndex tree is used for structure;
        full reasoning-based navigation requires an LLM — the query path stays keyword-based and is
        explicitly documented as such. For generation, we prefer `navigate_by_topic` below."""
        q = nl_query.lower()
        scored: list[tuple[float, dict[str, Any]]] = []
        for c in self._all_clauses:
            s = 0.0
            for t in c.get("topics", []):
                if t.lower() in q:
                    s += 2.0
            if c["title"].lower() in q or any(w in q for w in c["title"].lower().split()):
                s += 1.0
            if s > 0:
                scored.append((s, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._to_hit(c, score=s) for s, c in scored[:top_k]]

    def navigate_by_topic(self, topic: str) -> list[ClauseHit]:
        return [self._to_hit(c) for c in self._all_clauses if topic in c.get("topics", [])]

    def pairs_by_shared_topic(self, min_shared: int = 1) -> list[tuple[ClauseHit, ClauseHit]]:
        pairs: list[tuple[ClauseHit, ClauseHit]] = []
        cs = self._all_clauses
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                shared = set(cs[i].get("topics", [])) & set(cs[j].get("topics", []))
                if len(shared) >= min_shared and cs[i].get("parent") != cs[j]["clause_id"]:
                    pairs.append((self._to_hit(cs[i]), self._to_hit(cs[j])))
        return pairs

    def silence_candidates(self) -> list[ClauseHit]:
        """Clauses that defer externally or use vague language — candidates for Category C."""
        markers = ["as per", "per rbi", "per npci", "as determined", "in accordance with",
                   "may suspend", "may terminate", "from time to time", "reasonable"]
        out = []
        for c in self._all_clauses:
            text = c["verbatim_text"].lower()
            if any(m in text for m in markers):
                out.append(self._to_hit(c))
        return out

    @staticmethod
    def _to_hit(c: dict[str, Any], score: float = 0.0) -> ClauseHit:
        return ClauseHit(
            clause_id=c["clause_id"],
            title=c["title"],
            text=c["verbatim_text"],
            line_start=c["line_start"],
            line_end=c["line_end"],
            score=score,
        )
