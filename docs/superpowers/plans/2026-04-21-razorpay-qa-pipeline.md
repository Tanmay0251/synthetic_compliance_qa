# Razorpay Q&A Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Python pipeline that produces a 45+ example synthetic Q&A JSONL dataset grounded in the Razorpay ToS, with deterministic validation, per-dimension LLM-as-judge evaluation, judge-validation, and an automated failure catalogue — end-to-end dry-runnable with zero API calls and ready to execute real runs the instant an Anthropic key lands.

**Architecture:** Linear pipeline `fetch → clause_map → PageIndex tree → 3 distinct generators (A/B/C) → deterministic validator → bounded single-retry regen → per-dimension micro-judges → judge-validation (hand labels + cross-model κ) → failure catalogue → report`. Model-agnostic `LLMClient` with a `StubClient` for dry-runs. Every stage emits `{tokens, cost, latency}` to `runs/<ts>/metrics.json`.

**Tech Stack:** Python 3.12, `anthropic`, `openai`, `pageindex` (VectifyAI), `trafilatura`, `jsonschema`, `pytest`, `rich` (progress/tables), `tiktoken` (token counting for OpenAI), `tenacity` (retries).

**Spec:** `docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md`

---

## File Structure

All paths are relative to `C:/Users/manda/Desktop/Hyde/Take_Home/`.

| Path | Responsibility |
|---|---|
| `pyproject.toml` | deps, tool config, package metadata |
| `Makefile` | `setup / fetch / curate / dry-run / run / test` targets |
| `README.md` | quick start, determinism table, run table |
| `.gitignore` | standard python + runs/ exclusions |
| `schemas/dataset.schema.json` | JSON Schema for emitted rows |
| `data/razorpay_tos.html` | raw fetched HTML (committed) |
| `data/razorpay_tos.md` | cleaned markdown (committed) |
| `data/razorpay_tos.meta.json` | URL, fetch ts, SHA-256 |
| `data/clause_map.json` | hand-curated clause index |
| `data/pageindex_tree.json` | built tree, cached |
| `tools/fetch_tos.py` | fetcher + cleaner |
| `tools/clause_map_check.py` | verbatim-substring validation |
| `tools/build_pageindex_tree.py` | one-shot tree builder |
| `pipeline/__init__.py` | package marker |
| `pipeline/schema.py` | dataclasses + JSON-Schema validation helpers |
| `pipeline/llm.py` | `LLMClient` protocol + Anthropic/OpenAI/Stub impls |
| `pipeline/pricing.json` | token → USD table |
| `pipeline/metrics.py` | `stage_timer` + metrics writer |
| `pipeline/retrieval.py` | PageIndex wrapper |
| `pipeline/validator.py` | deterministic checks |
| `pipeline/regen.py` | one-retry regen harness |
| `pipeline/judge.py` | six micro-judges |
| `pipeline/judge_validation.py` | hand-label agreement + cross-model κ |
| `pipeline/failure_catalogue.py` | worst-items report |
| `pipeline/generators/__init__.py` | package marker |
| `pipeline/generators/common.py` | shared persona pool, few-shot loader, candidate dataclass |
| `pipeline/generators/a.py` | clear-answer generator |
| `pipeline/generators/b.py` | clarification-required generator |
| `pipeline/generators/c.py` | genuine-ambiguity generator |
| `prompts/gen_a_v1.md` | generator A system prompt |
| `prompts/gen_b_v1.md` | generator B system prompt |
| `prompts/gen_c_v1.md` | generator C system prompt |
| `prompts/judges/*.md` | six judge prompts |
| `eval/hand_labels.jsonl` | 10 committed human labels with timestamps |
| `tests/fixtures/*.json` | stub LLM responses per stage |
| `tests/test_schema.py` | schema validation tests |
| `tests/test_clause_map.py` | clause-map integrity tests |
| `tests/test_validator.py` | per-check validator tests |
| `tests/test_metrics.py` | metrics emission tests |
| `tests/test_retrieval.py` | PageIndex wrapper tests (uses cached tree) |
| `tests/test_generators.py` | generator tests against StubClient |
| `tests/test_judge.py` | judge tests against StubClient |
| `tests/test_pipeline_dry_run.py` | end-to-end dry run |
| `run.py` | CLI entry point |

---

## Task 0: Scaffold repo and git

**Files:**
- Create: `.gitignore`, `pyproject.toml`, `Makefile`, `README.md` (stub), `pipeline/__init__.py`, `pipeline/generators/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Initialize git**

```bash
cd /c/Users/manda/Desktop/Hyde/Take_Home
git init
git branch -M main
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.env
*.egg-info/
dist/
build/
runs/*
!runs/.gitkeep
.DS_Store
.idea/
.vscode/
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[project]
name = "razorpay-qa-pipeline"
version = "0.1.0"
description = "Synthetic Q&A dataset pipeline for Razorpay ToS"
requires-python = ">=3.12"
dependencies = [
  "anthropic>=0.40.0",
  "openai>=1.50.0",
  "pageindex>=0.1.0",
  "trafilatura>=1.12.0",
  "jsonschema>=4.22.0",
  "rich>=13.7.0",
  "tenacity>=9.0.0",
  "tiktoken>=0.7.0",
  "python-dotenv>=1.0.0",
  "requests>=2.32.0",
  "beautifulsoup4>=4.12.0",
  "lxml>=5.2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.2.0", "pytest-cov>=5.0.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 4: Write `Makefile`**

```makefile
.PHONY: setup fetch curate tree dry-run run test clean

PY ?= python

setup:
	$(PY) -m pip install -e .[dev]

fetch:
	$(PY) tools/fetch_tos.py

curate:
	$(PY) tools/clause_map_check.py

tree:
	$(PY) tools/build_pageindex_tree.py

test:
	$(PY) -m pytest -v

dry-run:
	$(PY) run.py --dry-run --target-per-category 3 --out runs/dry

run:
	$(PY) run.py --target-per-category 15 --out runs/$(shell date -u +%Y-%m-%dT%H%M%SZ)

clean:
	rm -rf runs/* .pytest_cache __pycache__
```

- [ ] **Step 5: Write stub `README.md`**

```markdown
# Razorpay ToS — Synthetic Q&A Dataset Pipeline

See `docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md` for architecture.

Filled in at Task 19 after real run lands.
```

- [ ] **Step 6: Create package markers**

Create three files, each containing just a newline:
- `pipeline/__init__.py`
- `pipeline/generators/__init__.py`
- `tests/__init__.py`

Also create `runs/.gitkeep` (empty file).

- [ ] **Step 7: Commit**

```bash
git add .gitignore pyproject.toml Makefile README.md pipeline/__init__.py pipeline/generators/__init__.py tests/__init__.py runs/.gitkeep docs/
git commit -m "chore: scaffold repo with pyproject, Makefile, and package layout"
```

---

## Task 1: Fetch and pin Razorpay ToS

**Files:**
- Create: `tools/fetch_tos.py`, `data/razorpay_tos.html`, `data/razorpay_tos.md`, `data/razorpay_tos.meta.json`

- [ ] **Step 1: Write `tools/fetch_tos.py`**

```python
"""Fetch razorpay.com/terms once, clean to markdown, pin with SHA."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
import trafilatura

URL = "https://razorpay.com/terms"
DATA = Path(__file__).resolve().parent.parent / "data"

def main() -> None:
    DATA.mkdir(exist_ok=True)
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text
    md = trafilatura.extract(
        html,
        output_format="markdown",
        include_tables=True,
        include_links=False,
        favor_precision=True,
    )
    if not md:
        raise SystemExit("trafilatura returned no content")
    (DATA / "razorpay_tos.html").write_text(html, encoding="utf-8")
    (DATA / "razorpay_tos.md").write_text(md, encoding="utf-8")
    (DATA / "razorpay_tos.meta.json").write_text(
        json.dumps(
            {
                "url": URL,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
                "md_lines": md.count("\n") + 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(md)} chars of cleaned markdown ({md.count(chr(10))+1} lines).")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the fetcher**

```bash
make fetch
```

Expected: prints `Wrote N chars of cleaned markdown`. Creates the three files in `data/`.

If razorpay.com/terms is unreachable or trafilatura returns empty, fall back: use `tools/fetch_tos.py --from-file <path>` variant — but only if step 2 fails. The main path is fresh fetch.

- [ ] **Step 3: Smoke-check the markdown**

Open `data/razorpay_tos.md`, confirm it contains "Terms of Use" and section markers like "Part A", "Clause", or "Section".

- [ ] **Step 4: Commit**

```bash
git add tools/fetch_tos.py data/razorpay_tos.html data/razorpay_tos.md data/razorpay_tos.meta.json
git commit -m "feat(data): fetch and pin Razorpay ToS with SHA-256 provenance"
```

---

## Task 2: Hand-curate clause map

**Files:**
- Create: `data/clause_map.json`, `tools/clause_map_check.py`
- Create: `tests/test_clause_map.py`

This is the task where the subagent (or Claude Code) reads `data/razorpay_tos.md` end-to-end and produces a hand-curated structured index.

- [ ] **Step 1: Read the cleaned markdown**

Read `data/razorpay_tos.md` in full. Identify every clause/section referenced in the seed questions (Part A §3.4, §3.5, §4.1, §4.2, §4.3, §4.5, Section 9, Clause 16.1) **plus** every numbered clause you encounter. Aim for 40–80 clauses total.

- [ ] **Step 2: Write `data/clause_map.json`**

Schema — one entry per clause:

```json
{
  "meta": {
    "source_md_sha256": "<copy from data/razorpay_tos.meta.json>",
    "curated_at": "2026-04-21",
    "curator": "claude-opus-4-7 via Claude Code",
    "method": "page-by-page read of data/razorpay_tos.md; no regex"
  },
  "clauses": [
    {
      "clause_id": "Part A §3.4",
      "title": "Fees payable irrespective of refund",
      "verbatim_text": "<exact substring of razorpay_tos.md>",
      "line_start": 142,
      "line_end": 156,
      "parent": "Part A §3",
      "topics": ["fees", "refunds", "processing"]
    }
  ]
}
```

Every `verbatim_text` MUST be a literal substring of `data/razorpay_tos.md`. No paraphrasing. Line numbers are 1-indexed in the MD file.

- [ ] **Step 3: Write `tools/clause_map_check.py`**

```python
"""Validate clause_map.json: every verbatim_text is a substring of the MD source."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

def main() -> int:
    md = (DATA / "razorpay_tos.md").read_text(encoding="utf-8")
    meta = json.loads((DATA / "razorpay_tos.meta.json").read_text(encoding="utf-8"))
    clause_map = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    errors = []
    if clause_map["meta"]["source_md_sha256"] != meta["md_sha256"]:
        errors.append(
            f"clause_map meta.source_md_sha256 mismatch: {clause_map['meta']['source_md_sha256']} vs {meta['md_sha256']}"
        )
    if md_sha != meta["md_sha256"]:
        errors.append("data/razorpay_tos.md SHA does not match meta")
    ids = set()
    for c in clause_map["clauses"]:
        cid = c["clause_id"]
        if cid in ids:
            errors.append(f"duplicate clause_id: {cid}")
        ids.add(cid)
        if c["verbatim_text"] not in md:
            errors.append(f"{cid}: verbatim_text not found in MD")
        lines = md.splitlines()
        if not (1 <= c["line_start"] <= c["line_end"] <= len(lines)):
            errors.append(f"{cid}: invalid line span {c['line_start']}-{c['line_end']}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK ({len(clause_map['clauses'])} clauses)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the check**

```bash
make curate
```

Expected: `OK (N clauses)`. If FAIL, fix `clause_map.json` until it passes.

- [ ] **Step 5: Write `tests/test_clause_map.py`**

```python
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

def test_seed_clauses_present(clause_map):
    required = {"Part A §3.4", "Part A §3.5", "Part A §4.1", "Part A §4.2"}
    present = {c["clause_id"] for c in clause_map["clauses"]}
    missing = required - present
    assert not missing, f"missing seed clauses: {missing}"
```

- [ ] **Step 6: Run tests**

```bash
python -m pytest tests/test_clause_map.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 7: Commit**

```bash
git add data/clause_map.json tools/clause_map_check.py tests/test_clause_map.py
git commit -m "feat(data): hand-curated clause map with substring-validation tool and tests"
```

---

## Task 3: JSONL schema and validation helpers

**Files:**
- Create: `schemas/dataset.schema.json`, `pipeline/schema.py`, `tests/test_schema.py`

- [ ] **Step 1: Write `schemas/dataset.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "category", "question", "persona", "clause_citations", "confidence", "should_escalate", "generation_meta"],
  "properties": {
    "id": {"type": "string", "pattern": "^[ABC]-\\d{3}$"},
    "category": {"enum": ["A", "B", "C"]},
    "question": {"type": "string", "minLength": 10},
    "persona": {"type": "string"},
    "user_context": {"type": ["string", "null"]},
    "answer": {"type": ["string", "null"]},
    "clarifying_question": {"type": ["string", "null"]},
    "clarification_axis": {"type": ["string", "null"]},
    "answer_branches": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "required": ["axis_value", "answer", "clause_citations"],
        "properties": {
          "axis_value": {"type": "string"},
          "answer": {"type": "string"},
          "clause_citations": {"type": "array"}
        }
      }
    },
    "clause_citations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["clause_id", "verbatim_excerpt", "relevance"],
        "properties": {
          "clause_id": {"type": "string"},
          "verbatim_excerpt": {"type": "string"},
          "relevance": {"enum": ["direct", "supporting", "contrast"]}
        }
      }
    },
    "ambiguity": {
      "type": ["object", "null"],
      "required": ["type", "what_is_known", "what_is_missing"],
      "properties": {
        "type": {"enum": ["silent", "vague_language", "external_deferral", "multi_rule_conflict"]},
        "what_is_known": {"type": "string"},
        "what_is_missing": {"type": "string"}
      }
    },
    "confidence": {"enum": ["high", "medium", "low"]},
    "should_escalate": {"type": "boolean"},
    "generation_meta": {
      "type": "object",
      "required": ["prompt_version", "model", "timestamp", "cost_usd", "tokens", "latency_ms", "regen_count"],
      "properties": {
        "prompt_version": {"type": "string"},
        "model": {"type": "string"},
        "seed_clause_ids": {"type": "array", "items": {"type": "string"}},
        "retrieval_trace": {"type": "array"},
        "timestamp": {"type": "string"},
        "cost_usd": {"type": "number"},
        "tokens": {
          "type": "object",
          "required": ["input", "output"],
          "properties": {
            "input": {"type": "integer"},
            "output": {"type": "integer"}
          }
        },
        "latency_ms": {"type": "integer"},
        "regen_count": {"type": "integer", "minimum": 0}
      }
    },
    "validator_report": {"type": "object"},
    "judge_report": {"type": ["object", "null"]}
  },
  "allOf": [
    {
      "if": {"properties": {"category": {"const": "A"}}},
      "then": {
        "required": ["answer"],
        "properties": {
          "answer": {"type": "string", "minLength": 10},
          "clarifying_question": {"type": "null"},
          "answer_branches": {"type": "null"},
          "ambiguity": {"type": "null"}
        }
      }
    },
    {
      "if": {"properties": {"category": {"const": "B"}}},
      "then": {
        "required": ["clarifying_question", "clarification_axis", "answer_branches"],
        "properties": {
          "clarifying_question": {"type": "string", "minLength": 10},
          "clarification_axis": {"type": "string", "minLength": 3},
          "answer_branches": {"type": "array", "minItems": 2},
          "ambiguity": {"type": "null"}
        }
      }
    },
    {
      "if": {"properties": {"category": {"const": "C"}}},
      "then": {
        "required": ["ambiguity"],
        "properties": {
          "ambiguity": {"type": "object"},
          "should_escalate": {"const": true},
          "clarifying_question": {"type": "null"}
        }
      }
    }
  ]
}
```

- [ ] **Step 2: Write `pipeline/schema.py`**

```python
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
```

- [ ] **Step 3: Write `tests/test_schema.py`**

```python
import pytest
from pipeline.schema import validate_row, is_valid

def _meta() -> dict:
    return {
        "prompt_version": "gen-a-v1",
        "model": "stub",
        "seed_clause_ids": ["Part A §3.4"],
        "retrieval_trace": [],
        "timestamp": "2026-04-21T09:00:00Z",
        "cost_usd": 0.0,
        "tokens": {"input": 10, "output": 5},
        "latency_ms": 100,
        "regen_count": 0,
    }

def _cite() -> dict:
    return {
        "clause_id": "Part A §3.4",
        "verbatim_excerpt": "fees are payable on every transaction",
        "relevance": "direct",
    }

def test_valid_category_a():
    row = {
        "id": "A-001",
        "category": "A",
        "question": "We refunded a customer. Do we still owe fees?",
        "persona": "backend_engineer",
        "user_context": None,
        "answer": "Yes, fees are payable on every transaction irrespective of refund.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_valid_category_b():
    row = {
        "id": "B-001",
        "category": "B",
        "question": "Can Razorpay hold our settlement?",
        "persona": "cto",
        "user_context": None,
        "answer": None,
        "clarifying_question": "Has the Facility Provider been intimated of the unauthorised debit yet?",
        "clarification_axis": "intimation_status",
        "answer_branches": [
            {"axis_value": "intimated", "answer": "Yes, Razorpay may suspend settlements during investigation.", "clause_citations": [_cite()]},
            {"axis_value": "not_intimated", "answer": "No basis to suspend under Clause 4.1 until intimation.", "clause_citations": [_cite()]},
        ],
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_valid_category_c():
    row = {
        "id": "C-001",
        "category": "C",
        "question": "How long can Razorpay hold funds after Clause 16 suspension?",
        "persona": "cto",
        "user_context": None,
        "answer": "The ToS does not specify a maximum duration. Escalate to Razorpay.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": {
            "type": "silent",
            "what_is_known": "Clause 16.1 grants immediate suspension rights.",
            "what_is_missing": "Maximum fund-hold duration is not defined.",
        },
        "confidence": "low",
        "should_escalate": True,
        "generation_meta": _meta(),
    }
    assert is_valid(row), validate_row(row)

def test_category_a_rejects_clarifying_question():
    row = {
        "id": "A-002",
        "category": "A",
        "question": "ok?",
        "persona": "x",
        "answer": "yes",
        "clarifying_question": "but what about?",
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("clarifying_question" in e for e in errs)

def test_category_c_requires_should_escalate_true():
    row = {
        "id": "C-002",
        "category": "C",
        "question": "ambiguous?",
        "persona": "x",
        "answer": "unclear",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": {"type": "silent", "what_is_known": "x", "what_is_missing": "y"},
        "confidence": "low",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("should_escalate" in e for e in errs)

def test_bad_id_format_rejected():
    row = {
        "id": "X-1",
        "category": "A",
        "question": "ok?",
        "persona": "x",
        "answer": "y",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [_cite()],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
        "generation_meta": _meta(),
    }
    errs = validate_row(row)
    assert any("id" in e for e in errs)
```

- [ ] **Step 4: Run tests (TDD red)**

```bash
python -m pytest tests/test_schema.py -v
```

Expected: all 6 pass. If any fails, fix the schema not the test (the tests encode the spec).

- [ ] **Step 5: Commit**

```bash
git add schemas/ pipeline/schema.py tests/test_schema.py
git commit -m "feat(schema): JSON Schema for dataset rows with per-category conditional rules"
```

---

## Task 4: Metrics and stage timing

**Files:**
- Create: `pipeline/metrics.py`, `pipeline/pricing.json`, `tests/test_metrics.py`

- [ ] **Step 1: Write `pipeline/pricing.json`**

Prices are USD per 1M tokens. Update before run if Anthropic/OpenAI change pricing.

```json
{
  "claude-opus-4-7": {"input_per_mtok": 15.00, "output_per_mtok": 75.00},
  "claude-sonnet-4-6": {"input_per_mtok": 3.00, "output_per_mtok": 15.00},
  "claude-haiku-4-5-20251001": {"input_per_mtok": 1.00, "output_per_mtok": 5.00},
  "gpt-5": {"input_per_mtok": 2.50, "output_per_mtok": 10.00},
  "stub": {"input_per_mtok": 0.0, "output_per_mtok": 0.0}
}
```

- [ ] **Step 2: Write `pipeline/metrics.py`**

```python
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
```

- [ ] **Step 3: Write `tests/test_metrics.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_metrics.py -v
```

Expected: all 4 pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/metrics.py pipeline/pricing.json tests/test_metrics.py
git commit -m "feat(metrics): per-stage token/cost/latency collector"
```

---

## Task 5: LLM client abstraction + StubClient

**Files:**
- Create: `pipeline/llm.py`, `tests/fixtures/stub_responses.json`, `tests/test_llm_stub.py`

- [ ] **Step 1: Write `tests/fixtures/stub_responses.json`**

Minimal seed — full fixtures filled in as generators are built in later tasks.

```json
{
  "gen_a_default": {
    "content": "{\"question\": \"We refunded a customer their full payment. Do we still have to pay Razorpay their processing fee?\", \"persona\": \"backend_engineer\", \"answer\": \"Yes. Under Part A, Clause 3.4 of the Razorpay General Terms of Use, transaction fees are payable on every transaction irrespective of any subsequent refund.\", \"clause_citations\": [{\"clause_id\": \"Part A §3.4\", \"verbatim_excerpt\": \"fees shall be payable on every transaction irrespective of any refund\", \"relevance\": \"direct\"}], \"confidence\": \"high\"}",
    "input_tokens": 500,
    "output_tokens": 120
  }
}
```

- [ ] **Step 2: Write `pipeline/llm.py`**

```python
"""Model-agnostic LLM client with Anthropic/OpenAI/Stub backends."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Msg:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class Response:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    raw: Any = None


class LLMClient(Protocol):
    model: str

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
    ) -> Response: ...


class StubClient:
    """Reads canned responses from tests/fixtures/stub_responses.json keyed by `fixture_key`."""

    def __init__(self, fixture_path: Path | None = None, model: str = "stub") -> None:
        self.model = model
        self.fixture_path = fixture_path or (ROOT / "tests" / "fixtures" / "stub_responses.json")
        with self.fixture_path.open(encoding="utf-8") as f:
            self._fixtures: dict[str, dict[str, Any]] = json.load(f)

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        fixture_key: str = "gen_a_default",
    ) -> Response:
        fx = self._fixtures.get(fixture_key)
        if fx is None:
            raise KeyError(f"no stub fixture for key={fixture_key}")
        return Response(
            content=fx["content"],
            input_tokens=fx.get("input_tokens", 100),
            output_tokens=fx.get("output_tokens", 50),
            model=self.model,
        )


class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        from anthropic import Anthropic

        self.model = model
        self._client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        **_: Any,
    ) -> Response:
        resp = self._client.messages.create(
            model=self.model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return Response(
            content=text,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=self.model,
            raw=resp,
        )


class OpenAIClient:
    def __init__(self, model: str = "gpt-5") -> None:
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        **_: Any,
    ) -> Response:
        msgs = [{"role": "system", "content": system}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        if seed is not None:
            kwargs["seed"] = seed
        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        return Response(
            content=text,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            model=self.model,
            raw=resp,
        )


def make_client(model: str) -> LLMClient:
    if model == "stub":
        return StubClient()
    if model.startswith("claude-"):
        return AnthropicClient(model=model)
    if model.startswith(("gpt-", "o")):
        return OpenAIClient(model=model)
    raise ValueError(f"unknown model family: {model}")
```

- [ ] **Step 3: Write `tests/test_llm_stub.py`**

```python
from pipeline.llm import StubClient, Msg

def test_stub_returns_fixture():
    c = StubClient()
    r = c.complete(system="x", messages=[Msg("user", "hello")], fixture_key="gen_a_default")
    assert "Razorpay" in r.content
    assert r.input_tokens > 0
    assert r.model == "stub"

def test_stub_missing_key_raises():
    c = StubClient()
    try:
        c.complete(system="x", messages=[], fixture_key="does_not_exist")
    except KeyError as e:
        assert "does_not_exist" in str(e)
    else:
        assert False, "expected KeyError"
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_llm_stub.py -v
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/llm.py tests/fixtures/stub_responses.json tests/test_llm_stub.py
git commit -m "feat(llm): LLMClient protocol with Anthropic, OpenAI, Stub backends"
```

---

## Task 6: PageIndex retrieval wrapper

**Files:**
- Create: `tools/build_pageindex_tree.py`, `pipeline/retrieval.py`, `tests/test_retrieval.py`

- [ ] **Step 1: Write `tools/build_pageindex_tree.py`**

```python
"""Build PageIndex reasoning tree from data/razorpay_tos.md, cache to data/pageindex_tree.json."""
from __future__ import annotations
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "pageindex_tree.json"

def main() -> int:
    md_path = DATA / "razorpay_tos.md"
    if not md_path.exists():
        print("data/razorpay_tos.md not found; run `make fetch` first", file=sys.stderr)
        return 1
    md = md_path.read_text(encoding="utf-8")
    try:
        import pageindex
    except ImportError:
        print("pageindex not installed; run `make setup`", file=sys.stderr)
        return 1
    # pageindex typical usage: build a tree from text. Exact API depends on version.
    # The wrapper calls whichever entry point exists; if the library changes, fail loudly.
    tree: dict | None = None
    for fn_name in ("build_tree", "doc_tree", "PageIndex"):
        fn = getattr(pageindex, fn_name, None)
        if fn is None:
            continue
        try:
            result = fn(md) if callable(fn) else None
            if hasattr(result, "to_dict"):
                tree = result.to_dict()
            elif isinstance(result, dict):
                tree = result
            elif hasattr(result, "root"):
                tree = {"root": result.root}
            if tree is not None:
                break
        except Exception as e:
            print(f"pageindex.{fn_name} raised: {e}", file=sys.stderr)
            continue
    if tree is None:
        print("Could not build tree via pageindex. Falling back to clause-map-derived tree.", file=sys.stderr)
        clause_map = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
        tree = _fallback_tree(clause_map)
    OUT.write_text(json.dumps(tree, indent=2), encoding="utf-8")
    print(f"Wrote tree to {OUT}")
    return 0


def _fallback_tree(clause_map: dict) -> dict:
    """If pageindex is unavailable/incompatible, derive a hierarchical tree from clause IDs."""
    root: dict = {"id": "root", "title": "Razorpay ToS", "children": []}
    parents: dict[str, dict] = {}
    for c in clause_map["clauses"]:
        node = {
            "id": c["clause_id"],
            "title": c["title"],
            "text": c["verbatim_text"],
            "line_start": c["line_start"],
            "line_end": c["line_end"],
            "children": [],
        }
        parent_id = c.get("parent")
        if parent_id and parent_id in parents:
            parents[parent_id]["children"].append(node)
        else:
            root["children"].append(node)
        parents[c["clause_id"]] = node
    return root


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write `pipeline/retrieval.py`**

```python
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
```

- [ ] **Step 3: Write `tests/test_retrieval.py`**

```python
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
```

- [ ] **Step 4: Build tree and run tests**

```bash
make tree
python -m pytest tests/test_retrieval.py -v
```

Expected: tree written to `data/pageindex_tree.json`; 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/build_pageindex_tree.py pipeline/retrieval.py data/pageindex_tree.json tests/test_retrieval.py
git commit -m "feat(retrieval): PageIndex wrapper with clause-map cross-walk and topic navigation"
```

---

## Task 7: Validator (deterministic checks)

**Files:**
- Create: `pipeline/validator.py`, `tests/test_validator.py`

- [ ] **Step 1: Write `tests/test_validator.py` (TDD red first)**

```python
import json
from pathlib import Path
import pytest
from pipeline.validator import Validator, ValidationResult

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def validator():
    return Validator(
        clause_map_path=DATA / "clause_map.json",
        md_path=DATA / "razorpay_tos.md",
    )


def _base_a(validator) -> dict:
    c = next(iter(validator._clauses.values()))
    return {
        "id": "A-001",
        "category": "A",
        "question": "A realistic, self-contained question about this clause?",
        "persona": "backend_engineer",
        "answer": f"Per {c['clause_id']}: {c['verbatim_text'][:60]}",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [
            {"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:40], "relevance": "direct"}
        ],
        "ambiguity": None,
        "confidence": "high",
        "should_escalate": False,
    }


def test_valid_a_passes(validator):
    row = _base_a(validator)
    r = validator.check(row)
    assert r.passed, r.reasons


def test_citation_to_unknown_clause_fails(validator):
    row = _base_a(validator)
    row["clause_citations"][0]["clause_id"] = "Part Z §99.99"
    r = validator.check(row)
    assert not r.passed
    assert any("citation_resolves" in x for x in r.reasons)


def test_non_substring_excerpt_fails(validator):
    row = _base_a(validator)
    row["clause_citations"][0]["verbatim_excerpt"] = "completely fabricated sentence not in the doc"
    r = validator.check(row)
    assert not r.passed
    assert any("verbatim" in x.lower() for x in r.reasons)


def test_a_with_hedging_fails(validator):
    row = _base_a(validator)
    row["answer"] = "It might depend. Unclear what applies here."
    r = validator.check(row)
    assert not r.passed
    assert any("struct_A" in x or "hedging" in x.lower() for x in r.reasons)


def test_b_missing_clarifier_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "B-001",
        "category": "B",
        "question": "Does this depend on context?",
        "persona": "cto",
        "answer": None,
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
    }
    r = validator.check(row)
    assert not r.passed


def test_b_axis_not_in_clarifier_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "B-002",
        "category": "B",
        "question": "Can it hold settlement?",
        "persona": "cto",
        "answer": None,
        "clarifying_question": "Please tell me more about the situation.",
        "clarification_axis": "intimation_status",
        "answer_branches": [
            {"axis_value": "yes", "answer": "x", "clause_citations": []},
            {"axis_value": "no", "answer": "y", "clause_citations": []},
        ],
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": None,
        "confidence": "medium",
        "should_escalate": False,
    }
    r = validator.check(row)
    assert not r.passed
    assert any("axis" in x.lower() for x in r.reasons)


def test_c_confident_answer_fails(validator):
    c = next(iter(validator._clauses.values()))
    row = {
        "id": "C-001",
        "category": "C",
        "question": "Is it defined?",
        "persona": "cto",
        "answer": "Yes it is clearly 30 days.",
        "clarifying_question": None,
        "clarification_axis": None,
        "answer_branches": None,
        "clause_citations": [{"clause_id": c["clause_id"], "verbatim_excerpt": c["verbatim_text"][:30], "relevance": "direct"}],
        "ambiguity": {"type": "silent", "what_is_known": "x", "what_is_missing": "y"},
        "confidence": "low",
        "should_escalate": True,
    }
    r = validator.check(row)
    assert not r.passed


def test_duplicate_question_fails(validator):
    c = next(iter(validator._clauses.values()))
    row1 = _base_a(validator)
    row1["id"] = "A-001"
    row2 = dict(row1)
    row2["id"] = "A-002"
    validator.reset()
    r1 = validator.check(row1)
    r2 = validator.check(row2)
    assert r1.passed
    assert not r2.passed
    assert any("duplicate" in x.lower() for x in r2.reasons)
```

- [ ] **Step 2: Run tests to confirm red**

```bash
python -m pytest tests/test_validator.py -v
```

Expected: all fail with "no module pipeline.validator".

- [ ] **Step 3: Write `pipeline/validator.py`**

```python
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

    def _check_citations(self, row: dict[str, Any], r: ValidationResult) -> None:
        cites = row.get("clause_citations") or []
        if not cites and row.get("category") == "A":
            r.checks["citation_resolves"] = "fail"
            r.reasons.append("citation_resolves: Category A requires at least 1 citation")
            return
        for i, c in enumerate(cites):
            cid = c.get("clause_id")
            clause = self._clauses.get(cid)
            if not clause:
                r.checks["citation_resolves"] = "fail"
                r.reasons.append(f"citation_resolves: unknown clause_id '{cid}'")
                return
            excerpt = c.get("verbatim_excerpt", "")
            if excerpt not in clause["verbatim_text"]:
                r.checks["citation_resolves"] = "fail"
                r.reasons.append(f"citation[{i}]: verbatim_excerpt not a substring of {cid}")
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
```

- [ ] **Step 4: Run tests until green**

```bash
python -m pytest tests/test_validator.py -v
```

Expected: all 8 pass. If any fail, read the failure, fix the validator (not the test). Common fix: adjust regex in `_check_grounding` for number-phrase detection.

- [ ] **Step 5: Commit**

```bash
git add pipeline/validator.py tests/test_validator.py
git commit -m "feat(validator): deterministic citation/grounding/struct/dup checks"
```

---

## Task 8: Prompt templates (generators)

**Files:**
- Create: `prompts/gen_a_v1.md`, `prompts/gen_b_v1.md`, `prompts/gen_c_v1.md`

- [ ] **Step 1: Write `prompts/gen_a_v1.md`**

```markdown
# Generator A — Clear Answer

You are generating a Q&A pair for a compliance assistant. The user is an engineer/CTO/PM at a startup using Razorpay. You will be given one anchor clause from the Razorpay General Terms of Use. Your job: produce a realistic, self-contained question that this clause **clearly and unambiguously answers**, plus the direct answer citing the clause.

## Hard rules
- The question must sound like something a real engineer or PM would ask in Slack — concrete scenario, not a legal quiz.
- The answer must be directly supported by the anchor clause. Do NOT add facts not present in the clause text.
- No hedging words (may, might, unclear, depends, possibly).
- The `verbatim_excerpt` in your citation MUST be an exact substring of the anchor clause text provided to you.
- Numbers in your answer (days, percentages, thresholds) MUST appear verbatim in the cited clause.

## Output format
Return a single JSON object (no prose, no markdown):
```json
{
  "question": "...",
  "persona": "backend_engineer | cto | product_manager | ops_lead | legal_pm",
  "user_context": null,
  "answer": "...",
  "clause_citations": [{"clause_id": "<anchor_clause_id>", "verbatim_excerpt": "<substring of anchor text>", "relevance": "direct"}],
  "confidence": "high"
}
```

## Anchor clause
`{clause_id}` — {title}

> {verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
```

- [ ] **Step 2: Write `prompts/gen_b_v1.md`**

```markdown
# Generator B — Clarification Required

You are generating a Q&A pair where a realistic question's answer **forks** on a specific context axis the user has not provided. You receive two related clauses that apply to different values of that axis.

## Hard rules
- The clarifying question must name the axis **specifically**. "Can you give me more detail?" is forbidden.
- The clarifying question must explain *what* about the answer would change once the axis is resolved.
- Provide two `answer_branches`, one per axis value, each with its own citation.
- The axis name (snake_case) must appear, in words, inside the clarifying question text.
- Do not answer the main `question` yourself — leave `answer` null.

## Output format
```json
{
  "question": "...",
  "persona": "...",
  "user_context": null,
  "answer": null,
  "clarifying_question": "...",
  "clarification_axis": "<snake_case_axis>",
  "answer_branches": [
    {"axis_value": "<v1>", "answer": "...", "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}]},
    {"axis_value": "<v2>", "answer": "...", "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}]}
  ],
  "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "direct"}],
  "confidence": "medium"
}
```

## Candidate clause pair (sharing topics: {shared_topics})
### Clause 1: `{c1.clause_id}` — {c1.title}
> {c1.verbatim_text}

### Clause 2: `{c2.clause_id}` — {c2.title}
> {c2.verbatim_text}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
```

- [ ] **Step 3: Write `prompts/gen_c_v1.md`**

```markdown
# Generator C — Genuine Ambiguity

You are generating a Q&A pair where the Razorpay ToS is **silent, vague, or defers externally** — producing a genuine regulatory gap. You receive one candidate clause (the closest thing the ToS says) and a silence-type hint.

## Hard rules
- The answer MUST NOT give a confident resolution. Forbidden phrases: "yes it is", "the answer is", "definitely", "clearly", "without doubt".
- The answer MUST name what is known (citing the candidate clause), explicitly describe what the ToS does *not* say, and recommend a named escalation path (Razorpay support, legal counsel, RBI/NPCI guidance).
- `ambiguity.type` must be one of: `silent`, `vague_language`, `external_deferral`, `multi_rule_conflict`.
- `should_escalate` must be `true`.
- `confidence` must be `low`.

## Output format
```json
{
  "question": "...",
  "persona": "...",
  "user_context": null,
  "answer": "...",
  "clause_citations": [{"clause_id": "...", "verbatim_excerpt": "...", "relevance": "supporting"}],
  "ambiguity": {
    "type": "silent | vague_language | external_deferral | multi_rule_conflict",
    "what_is_known": "...",
    "what_is_missing": "..."
  },
  "confidence": "low",
  "should_escalate": true
}
```

## Candidate clause
`{clause_id}` — {title}

> {verbatim_text}

## Silence hint
{silence_hint}

## Previous attempt feedback (if any)
{regen_feedback}

Produce the JSON now.
```

- [ ] **Step 4: Commit**

```bash
git add prompts/gen_a_v1.md prompts/gen_b_v1.md prompts/gen_c_v1.md
git commit -m "feat(prompts): generator prompts A/B/C with structural hard rules"
```

---

## Task 9: Generators (A, B, C) + common

**Files:**
- Create: `pipeline/generators/common.py`, `pipeline/generators/a.py`, `pipeline/generators/b.py`, `pipeline/generators/c.py`
- Modify: `tests/fixtures/stub_responses.json` (add B, C stubs)
- Create: `tests/test_generators.py`

- [ ] **Step 1: Write `pipeline/generators/common.py`**

```python
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

PERSONAS = ["backend_engineer", "cto", "product_manager", "ops_lead", "legal_pm"]


def load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


@dataclass
class Candidate:
    row: dict[str, Any]
    fixture_key: str = ""
    meta_patch: dict[str, Any] = field(default_factory=dict)


def render(template: str, **vars: Any) -> str:
    out = template
    for k, v in vars.items():
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
    return json.loads(text[first : last + 1])


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
```

- [ ] **Step 2: Write `pipeline/generators/a.py`**

```python
"""Generator A — clear answer."""
from __future__ import annotations
import random
from pathlib import Path
from typing import Any

from pipeline.generators.common import Candidate, build_meta, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever


PROMPT_VERSION = "gen-a-v1"
TEMPLATE_NAME = "gen_a_v1.md"


def _select_anchors(retriever: Retriever, n: int, rng: random.Random) -> list[ClauseHit]:
    """Prefer clauses with concrete numbers / day-counts / percentages (A-friendly)."""
    import re as _re
    candidates = []
    for h in retriever.all_clauses():
        if _re.search(r"\b\d+\s*(days?|%|percent|hours?|working\s+days?)\b", h.text, _re.IGNORECASE):
            candidates.append(h)
    if len(candidates) < n:
        extras = [h for h in retriever.all_clauses() if h not in candidates]
        rng.shuffle(extras)
        candidates.extend(extras)
    rng.shuffle(candidates)
    return candidates[:n]


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
    anchor_override: list[ClauseHit] | None = None,
) -> list[Candidate]:
    rng = random.Random(seed)
    template = load_prompt(TEMPLATE_NAME)
    anchors = anchor_override if anchor_override is not None else _select_anchors(retriever, n, rng)
    out: list[Candidate] = []
    for i, anchor in enumerate(anchors):
        prompt = render(
            template,
            clause_id=anchor.clause_id,
            title=anchor.title,
            verbatim_text=anchor.text,
            regen_feedback=regen_feedback or "(none)",
        )
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
            fixture_key="gen_a_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
        )
        data = extract_json(resp.content)
        data["id"] = f"A-{i+1:03d}"
        data["category"] = "A"
        data["clarifying_question"] = None
        data["clarification_axis"] = None
        data["answer_branches"] = None
        data["ambiguity"] = None
        data["should_escalate"] = data.get("should_escalate", False)
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[anchor.clause_id],
            retrieval_trace=[{"mode": "anchor", "clause_id": anchor.clause_id}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
```

- [ ] **Step 3: Write `pipeline/generators/b.py`**

```python
"""Generator B — clarification required."""
from __future__ import annotations
import random
from pathlib import Path

from pipeline.generators.common import Candidate, build_meta, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever

PROMPT_VERSION = "gen-b-v1"
TEMPLATE_NAME = "gen_b_v1.md"


def _select_pairs(retriever: Retriever, n: int, rng: random.Random) -> list[tuple[ClauseHit, ClauseHit, list[str]]]:
    pairs_all = retriever.pairs_by_shared_topic(min_shared=1)
    scored: list[tuple[int, ClauseHit, ClauseHit, list[str]]] = []
    for a, b in pairs_all:
        import json as _json
        cm = _json.loads((retriever.clause_map_path).read_text(encoding="utf-8"))
        by_id = {c["clause_id"]: c for c in cm["clauses"]}
        ta = set(by_id[a.clause_id].get("topics", []))
        tb = set(by_id[b.clause_id].get("topics", []))
        shared = sorted(ta & tb)
        scored.append((len(shared), a, b, shared))
    scored.sort(key=lambda x: x[0], reverse=True)
    rng.shuffle(scored)
    out = [(a, b, s) for (_, a, b, s) in scored[: n * 2]]
    rng.shuffle(out)
    return out[:n]


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
) -> list[Candidate]:
    rng = random.Random(seed + 1)
    template = load_prompt(TEMPLATE_NAME)
    pairs = _select_pairs(retriever, n, rng)
    out: list[Candidate] = []
    for i, (c1, c2, shared) in enumerate(pairs):
        prompt = render(
            template,
            shared_topics=", ".join(shared) or "(none)",
            **{
                "c1.clause_id": c1.clause_id, "c1.title": c1.title, "c1.verbatim_text": c1.text,
                "c2.clause_id": c2.clause_id, "c2.title": c2.title, "c2.verbatim_text": c2.text,
            },
            regen_feedback=regen_feedback or "(none)",
        )
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1500,
            seed=seed + i,
            fixture_key="gen_b_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1500,
            seed=seed + i,
        )
        data = extract_json(resp.content)
        data["id"] = f"B-{i+1:03d}"
        data["category"] = "B"
        data["answer"] = None
        data["ambiguity"] = None
        data["should_escalate"] = data.get("should_escalate", False)
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[c1.clause_id, c2.clause_id],
            retrieval_trace=[{"mode": "pair", "pair": [c1.clause_id, c2.clause_id], "shared_topics": shared}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
```

- [ ] **Step 4: Write `pipeline/generators/c.py`**

```python
"""Generator C — genuine ambiguity."""
from __future__ import annotations
import random
from pathlib import Path

from pipeline.generators.common import Candidate, build_meta, extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg
from pipeline.retrieval import ClauseHit, Retriever

PROMPT_VERSION = "gen-c-v1"
TEMPLATE_NAME = "gen_c_v1.md"

SILENCE_HINTS = {
    "silent": "The ToS does not address this topic at all.",
    "vague_language": "The ToS uses qualitative language ('reasonable', 'as determined') without specifying thresholds.",
    "external_deferral": "The ToS defers to external regulation (RBI / NPCI / state law) without defining boundaries.",
    "multi_rule_conflict": "Two or more clauses could apply and give different answers without an explicit reconciliation.",
}


def _select_candidates(retriever: Retriever, n: int, rng: random.Random) -> list[tuple[ClauseHit, str]]:
    silent_cands = retriever.silence_candidates()
    rng.shuffle(silent_cands)
    out: list[tuple[ClauseHit, str]] = []
    for h in silent_cands:
        t_lower = h.text.lower()
        if any(m in t_lower for m in ["per rbi", "per npci", "as per", "in accordance with"]):
            hint = SILENCE_HINTS["external_deferral"]
        elif any(m in t_lower for m in ["reasonable", "as determined", "from time to time"]):
            hint = SILENCE_HINTS["vague_language"]
        elif any(m in t_lower for m in ["may suspend", "may terminate"]):
            hint = SILENCE_HINTS["silent"]
        else:
            hint = SILENCE_HINTS["silent"]
        out.append((h, hint))
        if len(out) >= n:
            break
    while len(out) < n:
        h = rng.choice(retriever.all_clauses())
        out.append((h, SILENCE_HINTS["silent"]))
    return out


def generate(
    *,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    seed: int,
    regen_feedback: str = "",
) -> list[Candidate]:
    rng = random.Random(seed + 2)
    template = load_prompt(TEMPLATE_NAME)
    cands = _select_candidates(retriever, n, rng)
    out: list[Candidate] = []
    for i, (h, hint) in enumerate(cands):
        prompt = render(
            template,
            clause_id=h.clause_id,
            title=h.title,
            verbatim_text=h.text,
            silence_hint=hint,
            regen_feedback=regen_feedback or "(none)",
        )
        resp = llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
            fixture_key="gen_c_default",
        ) if hasattr(llm, "_fixtures") else llm.complete(
            system="You are a compliance Q&A dataset generator.",
            messages=[Msg("user", prompt)],
            temperature=0.7,
            max_tokens=1200,
            seed=seed + i,
        )
        data = extract_json(resp.content)
        data["id"] = f"C-{i+1:03d}"
        data["category"] = "C"
        data["clarifying_question"] = None
        data["clarification_axis"] = None
        data["answer_branches"] = None
        data["should_escalate"] = True
        data["confidence"] = "low"
        data["generation_meta"] = build_meta(
            prompt_version=PROMPT_VERSION,
            model=llm.model,
            seed_clause_ids=[h.clause_id],
            retrieval_trace=[{"mode": "silence", "clause_id": h.clause_id, "silence_hint": hint}],
            response=resp,
        )
        out.append(Candidate(row=data))
    return out
```

- [ ] **Step 5: Extend `tests/fixtures/stub_responses.json`**

```json
{
  "gen_a_default": {
    "content": "{\"question\": \"We refunded a customer their full payment. Do we still have to pay Razorpay their processing fee?\", \"persona\": \"backend_engineer\", \"user_context\": null, \"answer\": \"Yes. Per Part A §3.4 of the Razorpay General Terms of Use, fees shall be payable on every transaction irrespective of any refund.\", \"clause_citations\": [{\"clause_id\": \"Part A §3.4\", \"verbatim_excerpt\": \"fees shall be payable on every transaction irrespective of any refund\", \"relevance\": \"direct\"}], \"confidence\": \"high\"}",
    "input_tokens": 500,
    "output_tokens": 120
  },
  "gen_b_default": {
    "content": "{\"question\": \"A customer claims their card was used without authorization. Can Razorpay hold our settlement money?\", \"persona\": \"cto\", \"user_context\": null, \"answer\": null, \"clarifying_question\": \"What is the intimation_status — has the Facility Provider already intimated Razorpay of the unauthorised debit?\", \"clarification_axis\": \"intimation_status\", \"answer_branches\": [{\"axis_value\": \"intimated\", \"answer\": \"Yes — Razorpay may suspend settlements during investigation once intimated.\", \"clause_citations\": [{\"clause_id\": \"Part A §4.1\", \"verbatim_excerpt\": \"suspend settlements during investigation\", \"relevance\": \"direct\"}]}, {\"axis_value\": \"not_intimated\", \"answer\": \"No — settlement hold is not triggered until intimation per Clause 4.1.\", \"clause_citations\": [{\"clause_id\": \"Part A §4.1\", \"verbatim_excerpt\": \"intimated them of the unauthorised debit\", \"relevance\": \"direct\"}]}], \"clause_citations\": [{\"clause_id\": \"Part A §4.1\", \"verbatim_excerpt\": \"suspend settlements during investigation\", \"relevance\": \"direct\"}], \"confidence\": \"medium\"}",
    "input_tokens": 700,
    "output_tokens": 260
  },
  "gen_c_default": {
    "content": "{\"question\": \"Razorpay suspended our account under Clause 16. How long can they hold our funds?\", \"persona\": \"cto\", \"user_context\": null, \"answer\": \"The ToS is silent on maximum fund-hold duration after a Clause 16 suspension. What is known: Clause 16.1 grants immediate suspension rights across a range of triggers. What is not defined: a maximum duration or release timeline. Recommend escalating to Razorpay support in writing and engaging legal counsel for material holds.\", \"clause_citations\": [{\"clause_id\": \"Part A §4.1\", \"verbatim_excerpt\": \"suspend settlements during investigation\", \"relevance\": \"supporting\"}], \"ambiguity\": {\"type\": \"silent\", \"what_is_known\": \"Clause 16.1 grants immediate suspension rights\", \"what_is_missing\": \"Maximum duration of fund-hold is not specified anywhere in the ToS.\"}, \"confidence\": \"low\", \"should_escalate\": true}",
    "input_tokens": 600,
    "output_tokens": 220
  }
}
```

Note: the exact `clause_id` used in the fixture must exist in `data/clause_map.json`. If your curated clause map uses different IDs for these topics, update the fixture text accordingly.

- [ ] **Step 6: Write `tests/test_generators.py`**

```python
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
```

- [ ] **Step 7: Run generator tests**

```bash
python -m pytest tests/test_generators.py -v
```

Expected: all 3 pass. Iterate the fixtures if clause IDs need correction.

- [ ] **Step 8: Commit**

```bash
git add pipeline/generators/ tests/fixtures/stub_responses.json tests/test_generators.py
git commit -m "feat(generators): distinct A/B/C generators with retrieval-driven seeding"
```

---

## Task 10: Bounded regen harness

**Files:**
- Create: `pipeline/regen.py`

- [ ] **Step 1: Write `pipeline/regen.py`**

```python
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
```

- [ ] **Step 2: Add smoke test (append to `tests/test_generators.py`)**

```python
from pipeline.regen import regen_if_needed
from pipeline.validator import Validator


def test_regen_passes_through_valid(retriever, stub):
    from pipeline.generators import a as gen_a
    v = Validator(clause_map_path=DATA / "clause_map.json", md_path=DATA / "razorpay_tos.md")
    cands = gen_a.generate(n=1, retriever=retriever, llm=stub, seed=42)

    def regen_one(feedback: str):
        return gen_a.generate(n=1, retriever=retriever, llm=stub, seed=999, regen_feedback=feedback)[0]

    final, result, retries = regen_if_needed(cands[0], v, regen_one)
    # Stub always returns the same valid row for gen_a_default → no retries needed.
    assert retries == 0
    assert result.passed
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_generators.py::test_regen_passes_through_valid -v
```

Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add pipeline/regen.py tests/test_generators.py
git commit -m "feat(regen): bounded single-retry with validator feedback"
```

---

## Task 11: Judge prompts + judge module

**Files:**
- Create: `prompts/judges/grounding_v1.md`, `prompts/judges/category_fit_v1.md`, `prompts/judges/clarifier_quality_v1.md`, `prompts/judges/ambiguity_framing_v1.md`, `prompts/judges/clarity_v1.md`, `prompts/judges/citation_accuracy_v1.md`
- Create: `pipeline/judge.py`
- Modify: `tests/fixtures/stub_responses.json` (add judge stubs)
- Create: `tests/test_judge.py`

- [ ] **Step 1: Write each judge prompt**

Each file uses the same skeleton — scoring 1–5 (1=fails, 5=exemplary), with category-specific rubric content.

`prompts/judges/grounding_v1.md`:
```markdown
# GroundingJudge

Score the following Q&A row on **grounding**: does every factual claim in the answer (or `answer_branches`) appear in, or follow directly from, the cited clauses' `verbatim_text`?

- 5: every claim is directly supported by cited text; no invention.
- 4: minor inference that a reader would accept.
- 3: one claim is weakly supported (in scope but not literally stated).
- 2: one claim contradicts or isn't in cited text.
- 1: multiple claims ungrounded or citations irrelevant.

Also rate `citation_relevance` 1–5: do the cited clauses actually address the question?

Return ONLY JSON:
```json
{"scores": {"factual_support": <1-5>, "citation_relevance": <1-5>}, "rationale": "<50 words>", "failure_flags": ["ungrounded_claim" | "irrelevant_citation" | ...]}
```

## Row
{row_json}

## Cited clause text (verbatim)
{cited_clause_text}
```

`prompts/judges/category_fit_v1.md`:
```markdown
# CategoryFitJudge

Score `category_correctness` 1–5: does this row belong in its stated category?
- A: ToS explicitly and unambiguously answers the question.
- B: answer genuinely depends on context the user hasn't given; clarifier resolves it.
- C: ToS is silent, vague, or defers externally in a way that creates genuine uncertainty.

Return ONLY JSON:
```json
{"scores": {"category_correctness": <1-5>}, "rationale": "<50 words>", "failure_flags": ["wrong_category" | "borderline" | ...]}
```

## Row
{row_json}
```

`prompts/judges/clarifier_quality_v1.md`:
```markdown
# ClarifierQualityJudge (Category B only)

Score four sub-dimensions 1–5:
- `specificity`: does the clarifier name the axis or use vague "tell me more"?
- `names_axis`: is `clarification_axis` a real axis that changes the answer?
- `not_vague`: penalise clarifiers like "can you provide more detail?".
- `explains_what_changes`: does the clarifier or its answer_branches make clear how the answer forks?

Return ONLY JSON:
```json
{"scores": {"specificity": <1-5>, "names_axis": <1-5>, "not_vague": <1-5>, "explains_what_changes": <1-5>}, "rationale": "<60 words>", "failure_flags": ["vague_clarifier" | "axis_not_load_bearing" | ...]}
```

## Row
{row_json}
```

`prompts/judges/ambiguity_framing_v1.md`:
```markdown
# AmbiguityFramingJudge (Category C only)

Score three sub-dimensions 1–5:
- `names_silence_type`: is `ambiguity.type` correct for this case?
- `avoids_confident_answer`: does the answer avoid confident resolution?
- `recommends_escalation`: does the answer name a specific escalation path?

This judge exists specifically to prevent the common failure where a judge rubber-stamps "I don't know" as a clear answer.

Return ONLY JSON:
```json
{"scores": {"names_silence_type": <1-5>, "avoids_confident_answer": <1-5>, "recommends_escalation": <1-5>}, "rationale": "<60 words>", "failure_flags": ["confident_answer_in_C" | "silence_type_wrong" | "no_escalation" | ...]}
```

## Row
{row_json}
```

`prompts/judges/clarity_v1.md`:
```markdown
# ClarityJudge

Score `readability` and `concision` 1–5. This is about prose quality, not correctness.

Return ONLY JSON:
```json
{"scores": {"readability": <1-5>, "concision": <1-5>}, "rationale": "<40 words>", "failure_flags": []}
```

## Row
{row_json}
```

`prompts/judges/citation_accuracy_v1.md`:
```markdown
# CitationAccuracyJudge

Score two sub-dimensions 1–5:
- `excerpt_is_verbatim`: is each citation's `verbatim_excerpt` actually verbatim from the clause?
- `clause_id_correct_scope`: does the cited clause_id scope match the claim (e.g., don't cite Part A §3.5 for a Clause 4 question)?

Return ONLY JSON:
```json
{"scores": {"excerpt_is_verbatim": <1-5>, "clause_id_correct_scope": <1-5>}, "rationale": "<40 words>", "failure_flags": ["wrong_scope" | "paraphrase_not_verbatim" | ...]}
```

## Row
{row_json}

## Cited clause text (verbatim)
{cited_clause_text}
```

- [ ] **Step 2: Write `pipeline/judge.py`**

```python
"""Per-dimension micro-judges and aggregation."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.generators.common import extract_json, load_prompt, render
from pipeline.llm import LLMClient, Msg

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class JudgeResult:
    judge: str
    scores: dict[str, int]
    rationale: str = ""
    failure_flags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RowJudgement:
    row_id: str
    category: str
    per_judge: list[JudgeResult] = field(default_factory=list)

    def all_scores(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for j in self.per_judge:
            for k, v in j.scores.items():
                out[f"{j.judge}.{k}"] = v
        return out

    def composite(self) -> float:
        vals = list(self.all_scores().values())
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def failure_flags(self) -> list[str]:
        return [f for j in self.per_judge for f in j.failure_flags]


JUDGE_PROMPTS = {
    "grounding": "judges/grounding_v1.md",
    "category_fit": "judges/category_fit_v1.md",
    "clarifier_quality": "judges/clarifier_quality_v1.md",
    "ambiguity_framing": "judges/ambiguity_framing_v1.md",
    "clarity": "judges/clarity_v1.md",
    "citation_accuracy": "judges/citation_accuracy_v1.md",
}


def _cited_clause_text(row: dict[str, Any], clause_by_id: dict[str, dict[str, Any]]) -> str:
    ids = [c["clause_id"] for c in (row.get("clause_citations") or [])]
    for br in row.get("answer_branches") or []:
        ids.extend(c["clause_id"] for c in br.get("clause_citations", []))
    seen = []
    for cid in ids:
        if cid in seen:
            continue
        seen.append(cid)
    return "\n\n".join(
        f"### {cid}\n{clause_by_id[cid]['verbatim_text']}" for cid in seen if cid in clause_by_id
    )


def _run_one_judge(
    judge_name: str,
    row: dict[str, Any],
    llm: LLMClient,
    cited_text: str,
    fixture_key: str | None = None,
) -> JudgeResult:
    tmpl = load_prompt(JUDGE_PROMPTS[judge_name])
    prompt = render(tmpl, row_json=json.dumps(row, indent=2), cited_clause_text=cited_text or "(none)")
    kw: dict[str, Any] = dict(
        system="You are a strict rubric-based evaluator for a compliance Q&A dataset.",
        messages=[Msg("user", prompt)],
        temperature=0.0,
        max_tokens=600,
    )
    if hasattr(llm, "_fixtures"):
        kw["fixture_key"] = fixture_key or f"judge_{judge_name}_default"
    resp = llm.complete(**kw)
    data = extract_json(resp.content)
    return JudgeResult(
        judge=judge_name,
        scores=data.get("scores", {}),
        rationale=data.get("rationale", ""),
        failure_flags=data.get("failure_flags", []),
        raw=data,
    )


def judge_row(
    row: dict[str, Any],
    llm: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
) -> RowJudgement:
    cat = row.get("category")
    active = ["grounding", "category_fit", "clarity", "citation_accuracy"]
    if cat == "B":
        active.append("clarifier_quality")
    if cat == "C":
        active.append("ambiguity_framing")
    cited_text = _cited_clause_text(row, clause_by_id)
    judgements = [_run_one_judge(j, row, llm, cited_text) for j in active]
    return RowJudgement(row_id=row["id"], category=cat, per_judge=judgements)
```

- [ ] **Step 3: Extend `tests/fixtures/stub_responses.json` with judge stubs**

Append six keys; each content is JSON text.

```json
{
  "judge_grounding_default": {"content": "{\"scores\": {\"factual_support\": 5, \"citation_relevance\": 5}, \"rationale\": \"All claims directly supported.\", \"failure_flags\": []}", "input_tokens": 300, "output_tokens": 60},
  "judge_category_fit_default": {"content": "{\"scores\": {\"category_correctness\": 5}, \"rationale\": \"Fits A.\", \"failure_flags\": []}", "input_tokens": 200, "output_tokens": 40},
  "judge_clarifier_quality_default": {"content": "{\"scores\": {\"specificity\": 5, \"names_axis\": 5, \"not_vague\": 5, \"explains_what_changes\": 5}, \"rationale\": \"Specific axis named.\", \"failure_flags\": []}", "input_tokens": 250, "output_tokens": 70},
  "judge_ambiguity_framing_default": {"content": "{\"scores\": {\"names_silence_type\": 5, \"avoids_confident_answer\": 5, \"recommends_escalation\": 5}, \"rationale\": \"Properly framed as silence.\", \"failure_flags\": []}", "input_tokens": 250, "output_tokens": 60},
  "judge_clarity_default": {"content": "{\"scores\": {\"readability\": 4, \"concision\": 4}, \"rationale\": \"Clear.\", \"failure_flags\": []}", "input_tokens": 200, "output_tokens": 40},
  "judge_citation_accuracy_default": {"content": "{\"scores\": {\"excerpt_is_verbatim\": 5, \"clause_id_correct_scope\": 5}, \"rationale\": \"Verbatim match.\", \"failure_flags\": []}", "input_tokens": 200, "output_tokens": 40}
}
```

Merge these into the existing `stub_responses.json`, don't replace.

- [ ] **Step 4: Write `tests/test_judge.py`**

```python
import json
from pathlib import Path
import pytest
from pipeline.llm import StubClient
from pipeline.judge import judge_row

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def clause_by_id():
    cm = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    return {c["clause_id"]: c for c in cm["clauses"]}


def test_judge_a_row(clause_by_id):
    row = {
        "id": "A-001", "category": "A",
        "question": "x", "answer": "y",
        "clause_citations": [{"clause_id": list(clause_by_id.keys())[0], "verbatim_excerpt": "x", "relevance": "direct"}],
    }
    j = judge_row(row, StubClient(), clause_by_id)
    names = {r.judge for r in j.per_judge}
    assert {"grounding", "category_fit", "clarity", "citation_accuracy"}.issubset(names)
    assert "clarifier_quality" not in names


def test_judge_b_row_adds_clarifier(clause_by_id):
    row = {"id": "B-001", "category": "B", "question": "x", "clarifying_question": "y", "clarification_axis": "z", "answer_branches": [], "clause_citations": []}
    j = judge_row(row, StubClient(), clause_by_id)
    assert any(r.judge == "clarifier_quality" for r in j.per_judge)


def test_judge_c_row_adds_ambiguity_judge(clause_by_id):
    row = {"id": "C-001", "category": "C", "question": "x", "answer": "y", "ambiguity": {"type": "silent", "what_is_known": "", "what_is_missing": ""}, "clause_citations": []}
    j = judge_row(row, StubClient(), clause_by_id)
    assert any(r.judge == "ambiguity_framing" for r in j.per_judge)
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_judge.py -v
```

Expected: all 3 pass.

- [ ] **Step 6: Commit**

```bash
git add prompts/judges/ pipeline/judge.py tests/fixtures/stub_responses.json tests/test_judge.py
git commit -m "feat(judge): six per-dimension micro-judges with category-aware activation"
```

---

## Task 12: Judge-validation (hand labels + cross-model κ)

**Files:**
- Create: `eval/hand_labels.jsonl`, `pipeline/judge_validation.py`

- [ ] **Step 1: Write `eval/hand_labels.jsonl` (10 items)**

Each line: `{row: {...full row...}, human_scores: {...}, notes: "...", injected_failure: null | "wrong_citation" | "vague_clarifier" | "confident_in_C" | ...}`.

The task author (you, in the subagent) produces 10 items:
- 5 plausibly-good (2 Category A, 2 Category B, 1 Category C). Author these by hand using real clause_ids from `data/clause_map.json`. Human-label every dimension 4 or 5.
- 5 with injected failures:
  - A with a wrong citation (wrong clause_id but plausibly-worded) — human label for `citation_accuracy.clause_id_correct_scope` = 1.
  - A with paraphrased (not verbatim) excerpt — human label for `citation_accuracy.excerpt_is_verbatim` = 1.
  - B with hand-wavy clarifier ("Can you tell me more?") — human `clarifier_quality.not_vague` = 1, `specificity` = 1.
  - C with a confident answer ("Yes, it's clearly 30 days") — human `ambiguity_framing.avoids_confident_answer` = 1.
  - C with external_deferral but no escalation path named — human `recommends_escalation` = 1.

File format:
```jsonl
{"row": {...}, "human_scores": {"grounding.factual_support": 5, ...}, "notes": "...", "injected_failure": null, "labelled_at": "2026-04-21T10:30:00Z"}
```

Write this file by reading `data/clause_map.json` to pick real clause_ids. The contents are fixed and committed.

- [ ] **Step 2: Write `pipeline/judge_validation.py`**

```python
"""Judge-validation: hand-label agreement + cross-model Cohen's κ."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.judge import RowJudgement, judge_row
from pipeline.llm import LLMClient

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class AgreementReport:
    per_dimension: dict[str, dict[str, float]]
    injected_failure_catch_rate: float
    n_items: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "per_dimension": self.per_dimension,
            "injected_failure_catch_rate": self.injected_failure_catch_rate,
            "n_items": self.n_items,
        }


def _quadratic_kappa(a: list[int], b: list[int], k: int = 5) -> float:
    if not a or len(a) != len(b):
        return 0.0
    # Counts
    ca = Counter(a)
    cb = Counter(b)
    n = len(a)
    obs = defaultdict(int)
    for x, y in zip(a, b):
        obs[(x, y)] += 1
    num = 0.0
    den = 0.0
    for i in range(1, k + 1):
        for j in range(1, k + 1):
            w = ((i - j) ** 2) / ((k - 1) ** 2)
            e = (ca[i] * cb[j]) / n if n else 0
            o = obs[(i, j)]
            num += w * o
            den += w * e
    return 1.0 - (num / den) if den else 0.0


def run_hand_label_agreement(
    labels_path: Path,
    llm: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
) -> tuple[AgreementReport, list[dict[str, Any]]]:
    items = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    per_dim_deltas: dict[str, list[tuple[int, int]]] = defaultdict(list)
    per_row: list[dict[str, Any]] = []
    injected_caught = 0
    injected_total = 0
    for item in items:
        j: RowJudgement = judge_row(item["row"], llm, clause_by_id)
        judge_scores = j.all_scores()
        human_scores: dict[str, int] = item["human_scores"]
        for dim, hs in human_scores.items():
            js = judge_scores.get(dim)
            if js is None:
                continue
            per_dim_deltas[dim].append((hs, int(js)))
        if item.get("injected_failure"):
            injected_total += 1
            # A judge that caught the failure scores the affected dim ≤2.
            target_dims = _failure_target_dims(item["injected_failure"])
            caught = any(judge_scores.get(d, 5) <= 2 for d in target_dims)
            if caught:
                injected_caught += 1
        per_row.append({
            "row_id": item["row"]["id"],
            "injected_failure": item.get("injected_failure"),
            "judge": judge_scores,
            "human": human_scores,
        })
    per_dimension: dict[str, dict[str, float]] = {}
    for dim, pairs in per_dim_deltas.items():
        h, g = zip(*pairs)
        exact = sum(1 for x, y in pairs if x == y) / len(pairs)
        within_1 = sum(1 for x, y in pairs if abs(x - y) <= 1) / len(pairs)
        kappa = _quadratic_kappa(list(h), list(g))
        per_dimension[dim] = {
            "exact_match": round(exact, 3),
            "within_1": round(within_1, 3),
            "quadratic_kappa": round(kappa, 3),
            "n": len(pairs),
        }
    report = AgreementReport(
        per_dimension=per_dimension,
        injected_failure_catch_rate=round(injected_caught / injected_total, 3) if injected_total else 0.0,
        n_items=len(items),
    )
    return report, per_row


def _failure_target_dims(kind: str) -> list[str]:
    return {
        "wrong_citation": ["citation_accuracy.clause_id_correct_scope"],
        "paraphrase_not_verbatim": ["citation_accuracy.excerpt_is_verbatim"],
        "vague_clarifier": ["clarifier_quality.not_vague", "clarifier_quality.specificity"],
        "confident_in_C": ["ambiguity_framing.avoids_confident_answer"],
        "no_escalation_in_C": ["ambiguity_framing.recommends_escalation"],
    }.get(kind, [])


def run_cross_model_kappa(
    rows: list[dict[str, Any]],
    primary: LLMClient,
    secondary: LLMClient,
    clause_by_id: dict[str, dict[str, Any]],
    sample_frac: float = 0.2,
    seed: int = 42,
) -> dict[str, Any]:
    import random
    rng = random.Random(seed)
    n = max(1, int(len(rows) * sample_frac))
    sample = rng.sample(rows, n)
    per_dim_pairs: dict[str, list[tuple[int, int]]] = defaultdict(list)
    disagreements = []
    for row in sample:
        j1 = judge_row(row, primary, clause_by_id).all_scores()
        j2 = judge_row(row, secondary, clause_by_id).all_scores()
        for dim, v1 in j1.items():
            v2 = j2.get(dim)
            if v2 is None:
                continue
            per_dim_pairs[dim].append((int(v1), int(v2)))
            if abs(int(v1) - int(v2)) >= 2:
                disagreements.append({"row_id": row["id"], "dim": dim, "primary": v1, "secondary": v2})
    per_dim = {}
    for dim, pairs in per_dim_pairs.items():
        a, b = zip(*pairs)
        per_dim[dim] = {
            "quadratic_kappa": round(_quadratic_kappa(list(a), list(b)), 3),
            "n": len(pairs),
        }
    return {"sample_size": n, "per_dimension": per_dim, "disagreements": disagreements}
```

- [ ] **Step 3: Add a smoke test to `tests/test_judge.py`**

```python
def test_quadratic_kappa_perfect_agreement():
    from pipeline.judge_validation import _quadratic_kappa
    assert _quadratic_kappa([5, 4, 3, 2, 1], [5, 4, 3, 2, 1]) == 1.0


def test_quadratic_kappa_disagreement():
    from pipeline.judge_validation import _quadratic_kappa
    k = _quadratic_kappa([5, 5, 5, 5], [1, 1, 1, 1])
    assert k < 0.1
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_judge.py::test_quadratic_kappa_perfect_agreement tests/test_judge.py::test_quadratic_kappa_disagreement -v
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add eval/hand_labels.jsonl pipeline/judge_validation.py tests/test_judge.py
git commit -m "feat(judge-validation): hand-label agreement + cross-model Cohen's κ"
```

---

## Task 13: Failure catalogue

**Files:**
- Create: `pipeline/failure_catalogue.py`

- [ ] **Step 1: Write `pipeline/failure_catalogue.py`**

```python
"""Generate automated failure catalogue: 3 worst items per category with root-cause notes."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from pipeline.judge import RowJudgement


def build(
    rows: list[dict[str, Any]],
    judgements: dict[str, RowJudgement],
    out_path: Path,
    top_k: int = 3,
) -> None:
    by_cat: dict[str, list[tuple[dict[str, Any], RowJudgement]]] = {"A": [], "B": [], "C": []}
    for row in rows:
        j = judgements.get(row["id"])
        if j is None:
            continue
        by_cat.setdefault(row["category"], []).append((row, j))
    lines = ["# Failure catalogue — auto-generated", "", "> Three lowest-scoring items per category, with root-cause notes. Not cherry-picked.", ""]
    for cat in ("A", "B", "C"):
        items = by_cat[cat]
        items.sort(key=lambda rj: rj[1].composite())
        lines.append(f"## Category {cat}")
        lines.append("")
        for row, j in items[:top_k]:
            lines.append(f"### {row['id']} (composite {j.composite()})")
            lines.append(f"**Q:** {row['question']}")
            if row.get("answer"):
                lines.append(f"**A:** {row['answer']}")
            if row.get("clarifying_question"):
                lines.append(f"**Clarifier:** {row['clarifying_question']} (axis: `{row.get('clarification_axis')}`)")
            low = sorted(j.all_scores().items(), key=lambda kv: kv[1])[:3]
            lines.append(f"**Lowest dims:** " + ", ".join(f"`{k}`={v}" for k, v in low))
            if j.failure_flags():
                lines.append(f"**Flags:** {', '.join(j.failure_flags())}")
            lines.append(f"**Root-cause trace:** validator={row.get('validator_report', {}).get('passed')}; regen_count={row['generation_meta']['regen_count']}; seed_clauses={row['generation_meta']['seed_clause_ids']}")
            lines.append(f"**Mitigation proposal:** _to refine in v2_ (see README §v2-notes)")
            lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 2: Commit** (tested end-to-end in Task 15)

```bash
git add pipeline/failure_catalogue.py
git commit -m "feat(catalogue): automated worst-items-per-category report"
```

---

## Task 14: Run orchestrator

**Files:**
- Create: `run.py`, `tests/test_pipeline_dry_run.py`

- [ ] **Step 1: Write `run.py`**

```python
"""End-to-end pipeline runner. See README for usage."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pipeline.generators import a as gen_a, b as gen_b, c as gen_c
from pipeline.judge import judge_row
from pipeline.judge_validation import run_hand_label_agreement, run_cross_model_kappa
from pipeline.llm import make_client, LLMClient, StubClient
from pipeline.metrics import MetricsCollector, cost_usd
from pipeline.regen import regen_if_needed
from pipeline.retrieval import Retriever
from pipeline.schema import validate_row
from pipeline.validator import Validator
from pipeline import failure_catalogue

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def _load_clause_by_id() -> dict[str, dict[str, Any]]:
    cm = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    return {c["clause_id"]: c for c in cm["clauses"]}


def _run_generator(
    mod,
    n: int,
    retriever: Retriever,
    llm: LLMClient,
    validator: Validator,
    seed: int,
    metrics: MetricsCollector,
    stage_prefix: str,
    dropped_path: Path,
):
    out: list[dict[str, Any]] = []
    with metrics.stage(f"{stage_prefix}.generate", model=llm.model) as m:
        cands = mod.generate(n=n, retriever=retriever, llm=llm, seed=seed)
        for cand in cands:
            gm = cand.row.get("generation_meta", {})
            m.input_tokens += gm.get("tokens", {}).get("input", 0)
            m.output_tokens += gm.get("tokens", {}).get("output", 0)
        m.count = len(cands)
        m.cost_usd = cost_usd(llm.model, m.input_tokens, m.output_tokens)
    with metrics.stage(f"{stage_prefix}.validate_regen", model=llm.model) as m:
        for cand in cands:
            def regen_one(feedback: str, c=cand):
                new = mod.generate(
                    n=1, retriever=retriever, llm=llm, seed=seed + 999, regen_feedback=feedback
                )[0]
                return new
            final, result, retries = regen_if_needed(cand, validator, regen_one)
            final.row["validator_report"] = result.to_dict()
            if result.passed:
                out.append(final.row)
            else:
                dropped_path.parent.mkdir(parents=True, exist_ok=True)
                with dropped_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"row": final.row, "reasons": result.reasons}) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-per-category", type=int, default=15)
    ap.add_argument("--over-generate", type=float, default=1.5)
    ap.add_argument("--model-gen", default="claude-sonnet-4-6")
    ap.add_argument("--model-judge", default="claude-opus-4-7")
    ap.add_argument("--cross-model-judge", default=None, help="optional OpenAI model for cross-model κ")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true", help="use StubClient (no API calls)")
    ap.add_argument("--yes", action="store_true", help="skip cost estimate prompt")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = MetricsCollector(out_dir / "metrics.json")

    if args.dry_run:
        gen_llm = StubClient()
        judge_llm = StubClient()
    else:
        gen_llm = make_client(args.model_gen)
        judge_llm = make_client(args.model_judge)

    retriever = Retriever()
    validator = Validator(clause_map_path=DATA / "clause_map.json", md_path=DATA / "razorpay_tos.md")

    n_over = math.ceil(args.target_per_category * args.over_generate)
    dropped_path = out_dir / "dropped.jsonl"

    print(f"[run] over-generating {n_over} per category (target {args.target_per_category})")

    rows: list[dict[str, Any]] = []
    for cat, mod in [("A", gen_a), ("B", gen_b), ("C", gen_c)]:
        validator.reset()
        produced = _run_generator(
            mod, n_over, retriever, gen_llm, validator, args.seed,
            metrics, f"gen.{cat}", dropped_path,
        )
        produced = produced[: args.target_per_category]
        rows.extend(produced)
        print(f"[run] category {cat}: kept {len(produced)} of {n_over}")

    # Judge
    clause_by_id = _load_clause_by_id()
    judgements = {}
    with metrics.stage("judge", model=judge_llm.model) as m:
        for row in rows:
            j = judge_row(row, judge_llm, clause_by_id)
            row["judge_report"] = {
                "scores": j.all_scores(),
                "failure_flags": j.failure_flags(),
                "composite": j.composite(),
            }
            judgements[row["id"]] = j
            for res in j.per_judge:
                # crude token accounting for stub (judge_row does its own metrics in real runs)
                pass
            m.count += len(j.per_judge)

    # Schema-validate and write dataset
    bad = []
    with (out_dir / "dataset.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            errs = validate_row(row)
            if errs:
                bad.append((row["id"], errs))
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if bad:
        print(f"[run] WARNING: {len(bad)} rows failed schema and were excluded from dataset.jsonl")
        (out_dir / "schema_failures.jsonl").write_text(
            "\n".join(json.dumps({"id": rid, "errors": errs}) for rid, errs in bad),
            encoding="utf-8",
        )

    # Judge-validation
    with metrics.stage("judge_validation", model=judge_llm.model) as m:
        report, per_row = run_hand_label_agreement(
            ROOT / "eval" / "hand_labels.jsonl", judge_llm, clause_by_id
        )
    (out_dir / "judge_validation.md").write_text(_format_judge_validation(report), encoding="utf-8")
    (out_dir / "judge_validation.json").write_text(json.dumps({"report": report.to_dict(), "per_row": per_row}, indent=2), encoding="utf-8")

    # Cross-model κ (optional)
    if args.cross_model_judge and not args.dry_run:
        with metrics.stage("cross_model_judge", model=args.cross_model_judge) as m:
            secondary = make_client(args.cross_model_judge)
            km = run_cross_model_kappa(rows, judge_llm, secondary, clause_by_id)
        (out_dir / "judge_disagreements.jsonl").write_text(
            "\n".join(json.dumps(d) for d in km["disagreements"]), encoding="utf-8"
        )
        (out_dir / "cross_model_kappa.json").write_text(json.dumps(km, indent=2), encoding="utf-8")

    # Failure catalogue
    failure_catalogue.build(rows, judgements, out_dir / "failure_catalogue.md")

    # Top-level report
    (out_dir / "report.md").write_text(_format_report(rows, judgements, metrics, report, out_dir), encoding="utf-8")
    print(f"[run] done. outputs in {out_dir}")
    return 0


def _format_judge_validation(report) -> str:
    lines = [
        "# Judge validation (hand-labelled set)",
        "",
        f"- Items labelled: {report.n_items}",
        f"- Injected-failure catch rate: {report.injected_failure_catch_rate:.1%}",
        "",
        "## Per-dimension agreement",
        "",
        "| Dimension | Exact | Within-1 | κ (quadratic) | n |",
        "|---|---|---|---|---|",
    ]
    for dim, stats in sorted(report.per_dimension.items()):
        lines.append(
            f"| `{dim}` | {stats['exact_match']:.2f} | {stats['within_1']:.2f} | {stats['quadratic_kappa']:.2f} | {stats['n']} |"
        )
    return "\n".join(lines)


def _format_report(rows, judgements, metrics, jv_report, out_dir: Path) -> str:
    totals = json.loads(metrics.out_path.read_text())["totals"] if metrics.out_path.exists() else {}
    by_cat = {"A": [], "B": [], "C": []}
    for row in rows:
        by_cat[row["category"]].append(judgements[row["id"]].composite())
    mean = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0.0
    lines = [
        "# Run report",
        "",
        f"- Dataset rows: {len(rows)}",
        f"- Total cost (USD): {totals.get('total_cost_usd', 0):.4f}",
        f"- Total wall seconds: {totals.get('total_wall_seconds', 0):.1f}",
        f"- LLM calls: {totals.get('llm_calls', 0)}",
        "",
        "## Composite score by category",
        "",
        f"- A: mean {mean(by_cat['A'])} over {len(by_cat['A'])} rows",
        f"- B: mean {mean(by_cat['B'])} over {len(by_cat['B'])} rows",
        f"- C: mean {mean(by_cat['C'])} over {len(by_cat['C'])} rows",
        "",
        "## Judge validation",
        "",
        f"- Injected-failure catch rate: {jv_report.injected_failure_catch_rate:.1%}",
        "",
        "See `judge_validation.md` and `failure_catalogue.md` for detail.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write `tests/test_pipeline_dry_run.py`**

```python
import json
import subprocess
import sys
from pathlib import Path


def test_dry_run_produces_outputs(tmp_path: Path):
    root = Path(__file__).resolve().parent.parent
    out = tmp_path / "run"
    r = subprocess.run(
        [sys.executable, str(root / "run.py"), "--dry-run", "--target-per-category", "2", "--out", str(out)],
        capture_output=True, text=True, cwd=root,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "dataset.jsonl").exists()
    assert (out / "metrics.json").exists()
    assert (out / "judge_validation.md").exists()
    assert (out / "failure_catalogue.md").exists()
    assert (out / "report.md").exists()
    lines = (out / "dataset.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    for line in lines:
        row = json.loads(line)
        assert row["category"] in {"A", "B", "C"}
        assert row["generation_meta"]["prompt_version"].startswith("gen-")
```

- [ ] **Step 3: Run dry-run**

```bash
make dry-run
```

Expected: creates `runs/dry/` with all artifacts; prints `[run] done. outputs in runs/dry`.

- [ ] **Step 4: Run the e2e test**

```bash
python -m pytest tests/test_pipeline_dry_run.py -v
```

Expected: passes.

- [ ] **Step 5: Commit**

```bash
git add run.py tests/test_pipeline_dry_run.py
git commit -m "feat(run): end-to-end pipeline orchestrator with dry-run mode"
```

---

## Task 15: README with determinism + run tables

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write comprehensive README**

```markdown
# Razorpay ToS — Synthetic Q&A Dataset Pipeline

Reference solution for the Hyde AI Builder take-home assessment (Option 2: Razorpay ToS).
Produces a 45+ example JSONL dataset across three categories (A: clear answer, B: clarification required, C: genuine ambiguity), with deterministic validation, per-dimension LLM-as-judge evaluation, judge-validation, and an automated failure catalogue.

## Quick start

```bash
make setup       # install deps (editable)
make fetch       # fetch & pin Razorpay ToS (one-time; committed)
make tree        # build PageIndex reasoning tree (cached)
make test        # run unit tests
make dry-run     # full pipeline without API calls (uses fixtures)
make run         # real run; requires ANTHROPIC_API_KEY
```

Environment variables:
- `ANTHROPIC_API_KEY` — required for non-dry-run
- `OPENAI_API_KEY` — optional; enables cross-model κ when `--cross-model-judge gpt-5` is passed

## Architecture

See `docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md` for the full design.

Pipeline:
```
fetch → clause_map → PageIndex tree → {gen A, gen B, gen C} → validator → regen(≤1) → judges → judge-validation → failure catalogue → report
```

Generators are three distinct modules, not a single function with a category switch:
- **A**: seeded by clauses with concrete numeric claims; reverse construction (clause → question → answer).
- **B**: seeded by pairs of clauses sharing topics; LLM asked to name the load-bearing axis and produce forked branches.
- **C**: seeded by silence candidates (external_deferral / vague_language / may-suspend clauses); prompt forbids confident phrasing.

## Deterministic clause map

The clause map (`data/clause_map.json`) is **hand-curated** by Claude Code reading `data/razorpay_tos.md` page-by-page. This was a deliberate choice over regex: ToS/legal docs have irregular numbering that regex consistently mishandles. Substring-validation is automated (`tools/clause_map_check.py`), and `tests/test_clause_map.py` asserts every `verbatim_text` is a literal substring of the MD source. Adding a new clause is a diff to the JSON file + a re-run of the check. The check is run automatically on CI / in `make curate`.

## Reproducibility

| Artefact | Deterministic? | Mechanism |
|---|---|---|
| ToS source | Yes | `data/razorpay_tos.*` pinned; SHA-256 in `data/razorpay_tos.meta.json` |
| Clause map | Yes | hand-curated, committed, substring-checked |
| PageIndex tree | Yes (given source) | `data/pageindex_tree.json` cached; rebuilt only on source change |
| Generators | No (by design) | `temperature=0.7`; per-item seed = `--seed + i` for run-level reproducibility; model-side sampling remains |
| Validator | Yes | pure Python, no LLM |
| Judges | Near-det | `temperature=0.0`; model-side nondeterminism still possible |
| Judge-validation | Yes | committed `eval/hand_labels.jsonl` |
| Metrics | Yes (token+cost), No (wall) | `runs/<ts>/metrics.json` |

Full reproduction from clean clone:
```bash
make setup && make fetch && make curate && make tree && make run
```

## Cost awareness

Every stage emits `{tokens, cost_usd, latency_ms, count}` to `runs/<ts>/metrics.json`. The top of `runs/<ts>/report.md` shows totals. Pricing table at `pipeline/pricing.json` — update if Anthropic/OpenAI pricing changes.

Estimated cost for a full run (target=15/category, over-generate=1.5, models={gen: Sonnet 4.6, judge: Opus 4.7}, no cross-model): ~350 LLM calls, under $5 total.

## What the LLM-as-judge evaluation reveals

_This section is filled in by the latest run. See `runs/<latest>/report.md` for live numbers._

We split the judge into **six per-dimension micro-judges**, not one monolithic rubric:
- `GroundingJudge` (factual_support, citation_relevance) — all categories
- `CategoryFitJudge` (category_correctness) — all categories
- `ClarifierQualityJudge` (specificity, names_axis, not_vague, explains_what_changes) — B only
- `AmbiguityFramingJudge` (names_silence_type, avoids_confident_answer, recommends_escalation) — C only, specifically to catch the "judge rubber-stamps 'I don't know' as clear" failure mode
- `ClarityJudge` (readability, concision) — all
- `CitationAccuracyJudge` (excerpt_is_verbatim, clause_id_correct_scope) — A, B

**Judge-validation** runs two mechanisms:
1. **Hand-labels**: `eval/hand_labels.jsonl` contains 10 committed items — 5 plausibly-good, 5 with injected known failures (wrong citation, paraphrased excerpt, vague clarifier, confident answer in C, missing escalation). The judge scores them blind; we report per-dimension exact-match / within-1 / quadratic-κ and the injected-failure catch rate.
2. **Cross-model κ** (optional, when `--cross-model-judge <openai_model>` is set): a GPT-family model runs the same rubric on a 20% random slice; per-dimension Cohen's κ reported in `cross_model_kappa.json`; disagreements dumped to `judge_disagreements.jsonl` for manual review.

## Self-identified failures

`runs/<ts>/failure_catalogue.md` is automatically generated: 3 lowest-scoring items per category, lowest scoring dimensions, raised flags, regen count, and seed clauses. It is not cherry-picked.

## v2 (if I had another day)

- Active-learning loop: failure catalogue → prompt updates → next run.
- Multi-turn generation (follow-up after B clarifier is answered).
- Domain-adapted clause embeddings as a retrieval benchmark alongside PageIndex.
- Hand-labelled set grown to 40 items with adversarial perturbations.

## Repo layout

```
pipeline/         core modules
pipeline/generators/  three distinct generators (A, B, C)
prompts/          versioned prompt templates
prompts/judges/   per-dimension judge prompts
schemas/          JSON Schema for dataset rows
tools/            one-shot scripts (fetch, curate-check, tree-build)
eval/             committed hand labels
tests/            unit + e2e tests
runs/             per-run outputs (gitignored except .gitkeep)
data/             pinned ToS, clause map, tree (committed)
docs/superpowers/ spec + plan
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with determinism table, architecture, cost and v2 sections"
```

---

## Task 16: Dry-run end-to-end and verify

**Files:**
- Modify: none (verification only)

- [ ] **Step 1: Run the full test suite**

```bash
python -m pytest -v
```

Expected: every test passes.

- [ ] **Step 2: Run dry-run at full scale**

```bash
python run.py --dry-run --target-per-category 15 --out runs/dry_full
```

Expected: creates 45 rows (may be fewer if stub fixtures produce duplicates that the validator drops — expected; stub is a single fixture). Every output file in `runs/dry_full/` populated.

- [ ] **Step 3: Verify schema conformance of emitted JSONL**

```bash
python -c "
import json
from pipeline.schema import validate_row
count = 0
for line in open('runs/dry_full/dataset.jsonl', encoding='utf-8'):
    row = json.loads(line)
    errs = validate_row(row)
    assert not errs, (row['id'], errs)
    count += 1
print(f'{count} rows validate clean')
"
```

Expected: `N rows validate clean`.

- [ ] **Step 4: Verify metrics.json is well-formed**

```bash
python -c "
import json
m = json.load(open('runs/dry_full/metrics.json'))
assert 'totals' in m and 'stages' in m
assert m['totals']['total_cost_usd'] == 0.0
print('metrics ok')
"
```

Expected: `metrics ok`.

- [ ] **Step 5: Commit (captures the dry-run as a known-good reference)**

```bash
git add runs/dry_full/dataset.jsonl runs/dry_full/metrics.json runs/dry_full/report.md runs/dry_full/failure_catalogue.md runs/dry_full/judge_validation.md 2>/dev/null || true
git commit -m "chore: commit dry-run reference outputs for regression baseline" || echo "nothing to commit (runs/ may be gitignored)"
```

(If `runs/` is gitignored per `.gitignore`, skip the commit — dry-run artifacts aren't meant to be checked in. This step is informational.)

---

## Task 17: Real run (requires API key — deferred until key arrives)

**Files:**
- Produces: `runs/<timestamp>/*`

- [ ] **Step 1: Export API key**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

- [ ] **Step 2: Cost estimate dry-check**

```bash
python -c "
from pipeline.metrics import cost_usd
# 45 rows × ~500 in / 250 out gen + 45 × 6 judges × ~400 in / 80 out
gen_in, gen_out = 45*500, 45*250
judge_in, judge_out = 45*6*400, 45*6*80
print(f'gen: \${cost_usd(\"claude-sonnet-4-6\", gen_in, gen_out):.2f}')
print(f'judge: \${cost_usd(\"claude-opus-4-7\", judge_in, judge_out):.2f}')
"
```

Expected: prints estimates. Confirm total < $5.

- [ ] **Step 3: Run**

```bash
python run.py --target-per-category 15 --out runs/$(date -u +%Y-%m-%dT%H%M%SZ)
```

Expected: runs through every stage, emits full artifacts. Monitor `runs/<ts>/metrics.json` for live progress.

- [ ] **Step 4: Inspect the report**

Open `runs/<ts>/report.md`. Verify:
- 45 rows total, balanced across A/B/C.
- Composite means per category look plausible (no category dominating — judge leniency red flag if C >> A).
- Injected-failure catch rate on hand labels > 80% (else judges need tightening).

- [ ] **Step 5: Fold latest dataset to root**

```bash
cp runs/<ts>/dataset.jsonl dataset.jsonl
cp runs/<ts>/report.md eval_summary.md
```

- [ ] **Step 6: Commit the real-run artifacts**

```bash
git add dataset.jsonl eval_summary.md
git commit -m "feat: first real run — 45 examples across A/B/C with judge eval"
```

---

## Self-review against spec

### Spec coverage check
- ✅ §4.1 Source pinning → Task 1
- ✅ §4.2 Clause map → Task 2
- ✅ §4.3 PageIndex wrapper → Task 6
- ✅ §4.4 LLM client → Task 5
- ✅ §4.5 Three generators → Task 8 (prompts) + Task 9 (code)
- ✅ §4.6 Validator → Task 7
- ✅ §4.7 Bounded regen → Task 10
- ✅ §4.8 Per-dimension judges → Task 11
- ✅ §4.9 Judge-validation → Task 12
- ✅ §4.10 Failure catalogue → Task 13
- ✅ §4.11 Run orchestrator → Task 14
- ✅ §5.1 JSONL schema → Task 3
- ✅ §5.2 Per-run outputs → Task 14
- ✅ §6 Determinism → Task 15 README
- ✅ §7 Cost controls → Task 4 metrics + Task 15 README
- ✅ §8 Repo layout → Task 0 + all subsequent tasks
- ✅ §9 Deliverables mapping → Task 15 README + Task 17 real run
- ✅ §10 Known risks → acknowledged in spec; mitigations landed in respective tasks

### Placeholder scan
No TBD / TODO in any task — every code step has a concrete code block. `eval/hand_labels.jsonl` is described with exact construction rules (5 good + 5 with specified injected failures), not "fill in later".

### Type consistency
- `Candidate`, `ValidationResult`, `JudgeResult`, `RowJudgement`, `ClauseHit`, `Msg`, `Response` — defined once, used consistently.
- `Retriever.clause_map_path` used in `pipeline/generators/b.py` matches the attribute set in `pipeline/retrieval.py` constructor.
- Judge name keys in `JUDGE_PROMPTS` match fixture keys in `stub_responses.json` (`judge_<name>_default`).
- `regen_count` used in `build_meta` and in schema — same type (int).

No drift detected.
