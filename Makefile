.PHONY: setup fetch curate tree dry-run run test clean

PY ?= python
TS := $(shell python -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ'))")

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
	$(PY) run.py --target-per-category 15 --out runs/$(TS)

clean:
	rm -rf runs/* .pytest_cache __pycache__
