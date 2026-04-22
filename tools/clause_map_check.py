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
    lines = md.splitlines()
    for c in clause_map["clauses"]:
        cid = c["clause_id"]
        if cid in ids:
            errors.append(f"duplicate clause_id: {cid}")
        ids.add(cid)
        if c["verbatim_text"] not in md:
            errors.append(f"{cid}: verbatim_text not found in MD")
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
