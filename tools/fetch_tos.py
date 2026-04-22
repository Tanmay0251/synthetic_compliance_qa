"""Fetch razorpay.com/terms once, clean to markdown, pin with SHA."""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import trafilatura

URL = "https://razorpay.com/terms"
DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> int:
    DATA.mkdir(exist_ok=True)
    print(f"Fetching {URL} ...")
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (research fetch)"})
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
        print("ERROR: trafilatura returned no content", file=sys.stderr)
        return 1
    (DATA / "razorpay_tos.html").write_text(html, encoding="utf-8")
    (DATA / "razorpay_tos.md").write_text(md, encoding="utf-8")
    meta = {
        "url": URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
        "md_chars": len(md),
        "md_lines": md.count("\n") + 1,
    }
    (DATA / "razorpay_tos.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {len(md)} chars ({meta['md_lines']} lines) of cleaned markdown.")
    print(f"SHA-256: {meta['md_sha256'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
