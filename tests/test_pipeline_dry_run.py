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
