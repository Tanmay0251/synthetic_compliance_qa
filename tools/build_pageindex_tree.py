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
    pageindex = None
    try:
        import pageindex  # type: ignore[no-redef]
    except ImportError:
        print("pageindex not installed; using clause-map-derived fallback tree", file=sys.stderr)
    # pageindex typical usage: build a tree from text. Exact API depends on version.
    # The wrapper calls whichever entry point exists; if the library changes, fall back.
    tree: dict | None = None
    if pageindex is not None:
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
