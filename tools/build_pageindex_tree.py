"""Build the PageIndex reasoning tree from data/razorpay_tos.md.

Uses the open-source PageIndex library (VectifyAI/PageIndex on GitHub). The
PyPI `pageindex` package is an API-client for the hosted service; we invoke
the GitHub repo directly instead so the tree is built locally with our own
LLM key.

Requires ANTHROPIC_API_KEY (or OPENAI_API_KEY) in env. PageIndex uses LiteLLM
and we default to `anthropic/claude-sonnet-4-6`.

Falls back to a clause-map-derived tree only if PageIndex cannot be invoked.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VENDOR = ROOT / "third_party" / "PageIndex"
PAGEINDEX_REPO = "https://github.com/VectifyAI/PageIndex.git"
OUT = DATA / "pageindex_tree.json"


def clone_if_needed() -> bool:
    if VENDOR.exists() and (VENDOR / "run_pageindex.py").exists():
        return True
    VENDOR.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning PageIndex into {VENDOR} ...")
    r = subprocess.run(
        ["git", "clone", "--depth=1", PAGEINDEX_REPO, str(VENDOR)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"clone failed: {r.stderr}", file=sys.stderr)
        return False
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(VENDOR / "requirements.txt")],
        check=False,
    )
    return True


def run_pageindex() -> bool:
    if not clone_if_needed():
        return False
    env = dict(os.environ)
    if not env.get("ANTHROPIC_API_KEY") and not env.get("OPENAI_API_KEY"):
        print("No ANTHROPIC_API_KEY or OPENAI_API_KEY — PageIndex needs one.", file=sys.stderr)
        return False
    model = env.get("PAGEINDEX_MODEL", "anthropic/claude-sonnet-4-6")
    cmd = [
        sys.executable, "run_pageindex.py",
        "--md_path", str(DATA / "razorpay_tos.md"),
        "--model", model,
        "--if-add-node-text", "yes",
        "--if-add-node-id", "yes",
        "--if-add-node-summary", "no",
    ]
    print(f"Invoking PageIndex: model={model}")
    r = subprocess.run(cmd, cwd=VENDOR, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"PageIndex failed: {r.stderr[:500]}", file=sys.stderr)
        return False
    out_src = VENDOR / "results" / "razorpay_tos_structure.json"
    if not out_src.exists():
        print(f"PageIndex produced no output at {out_src}", file=sys.stderr)
        return False
    shutil.copyfile(out_src, OUT)
    print(f"Wrote real PageIndex tree to {OUT}")
    return True


def fallback_from_clause_map() -> bool:
    print("Building fallback tree from clause_map.json (NOT a real PageIndex tree).")
    cm = json.loads((DATA / "clause_map.json").read_text(encoding="utf-8"))
    tree = {
        "doc_name": "razorpay_tos",
        "note": "fallback tree derived from clause_map; NOT a real PageIndex reasoning tree",
        "structure": [
            {
                "title": c["title"],
                "node_id": f"hc-{i:04d}",
                "line_num": c["line_start"],
                "text": c["verbatim_text"],
                "nodes": [],
            }
            for i, c in enumerate(cm["clauses"])
        ],
    }
    OUT.write_text(json.dumps(tree, indent=2), encoding="utf-8")
    return True


def main() -> int:
    if run_pageindex():
        return 0
    print("Falling back.", file=sys.stderr)
    return 0 if fallback_from_clause_map() else 1


if __name__ == "__main__":
    sys.exit(main())
