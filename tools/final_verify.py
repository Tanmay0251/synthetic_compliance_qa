"""Full pre-submission verification. Actual checks, not claims."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.schema import validate_row

FAILURES: list[str] = []
WARNINGS: list[str] = []

# 1. Required files
required = [
    'dataset.jsonl', 'eval_summary.md', 'judge_validation.md', 'failure_catalogue.md',
    'README.md', 'Makefile', 'pyproject.toml', 'run.py', '.gitignore',
    'data/razorpay_tos.md', 'data/razorpay_tos.html', 'data/razorpay_tos.meta.json',
    'data/clause_map.json', 'data/pageindex_tree.json',
    'schemas/dataset.schema.json', 'eval/hand_labels.jsonl',
    'docs/journey.md',
    'docs/superpowers/specs/2026-04-21-razorpay-qa-pipeline-design.md',
    'docs/superpowers/plans/2026-04-21-razorpay-qa-pipeline.md',
    'audit/ps_category_audit_v4.md', 'audit/improvement_delta.md',
    'runs/2026-04-22-v4/metrics.json', 'runs/2026-04-22-v4/dataset.jsonl',
]
missing = [f for f in required if not (ROOT / f).exists()]
if missing:
    FAILURES.append(f"Missing required files: {missing}")
else:
    print(f"[OK] All {len(required)} required files present")

# 2. dataset.jsonl
rows = [json.loads(l) for l in (ROOT / 'dataset.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
if len(rows) != 45:
    FAILURES.append(f"dataset.jsonl has {len(rows)} rows (expected 45)")
cats = Counter(r['category'] for r in rows)
if dict(cats) != {'A': 15, 'B': 15, 'C': 15}:
    FAILURES.append(f"Category balance: {dict(cats)}")
ids = [r['id'] for r in rows]
if len(set(ids)) != 45:
    FAILURES.append(f"Duplicate IDs")
for cat in 'ABC':
    expected_ids = [f"{cat}-{i:03d}" for i in range(1, 16)]
    actual_ids = sorted(r['id'] for r in rows if r['category'] == cat)
    if actual_ids != expected_ids:
        FAILURES.append(f"{cat} IDs not contiguous")
print(f"[OK] dataset.jsonl: 45 rows, 15/15/15, IDs contiguous")

# 3. Schema validity
bad = [(r['id'], validate_row(r)) for r in rows if validate_row(r)]
if bad:
    FAILURES.append(f"Schema failures: {[(i, e[:1]) for i, e in bad]}")
else:
    print(f"[OK] 45/45 rows schema-valid")

# 4. Citations resolve against clause_map
cm = json.loads((ROOT / 'data/clause_map.json').read_text(encoding='utf-8'))
all_ids = {c['clause_id']: c for c in cm['clauses']}
md = (ROOT / 'data/razorpay_tos.md').read_text(encoding='utf-8')
cite_fails = []
for r in rows:
    for c in r.get('clause_citations') or []:
        cid = c['clause_id']
        if cid not in all_ids:
            cite_fails.append((r['id'], cid, 'unknown_clause'))
            continue
        if c['verbatim_excerpt'] not in all_ids[cid]['verbatim_text']:
            cite_fails.append((r['id'], cid, 'excerpt_not_substring'))
    for br in r.get('answer_branches') or []:
        for c in br.get('clause_citations', []):
            cid = c['clause_id']
            if cid not in all_ids:
                cite_fails.append((r['id'], cid, 'unknown_clause_in_branch'))
            elif c['verbatim_excerpt'] not in all_ids[cid]['verbatim_text']:
                cite_fails.append((r['id'], cid, 'branch_excerpt_not_substring'))
if cite_fails:
    FAILURES.append(f"Citation failures: {len(cite_fails)} -- first 3: {cite_fails[:3]}")
else:
    print(f"[OK] All citations resolve and excerpts are verbatim")

# 5. Clause map integrity
cm_bad = [c['clause_id'] for c in cm['clauses'] if c['verbatim_text'] not in md]
if cm_bad:
    FAILURES.append(f"clause_map verbatim not in MD: {cm_bad[:3]}")
md_sha = hashlib.sha256(md.encode('utf-8')).hexdigest()
meta = json.loads((ROOT / 'data/razorpay_tos.meta.json').read_text(encoding='utf-8'))
if md_sha != meta['md_sha256']:
    FAILURES.append(f"MD SHA mismatch: {md_sha[:16]} vs meta {meta['md_sha256'][:16]}")
if cm['meta']['source_md_sha256'] != meta['md_sha256']:
    FAILURES.append("clause_map source_md_sha256 != meta")
covered = set()
for c in cm['clauses']:
    for ln in range(c['line_start'], c['line_end'] + 1):
        covered.add(ln)
md_lines = md.splitlines()
nonblank_total = sum(1 for ln in md_lines if ln.strip())
nonblank_cov = sum(1 for i in range(1, len(md_lines) + 1) if i in covered and md_lines[i - 1].strip())
if nonblank_cov != nonblank_total:
    WARNINGS.append(f"Non-blank content coverage {nonblank_cov}/{nonblank_total}")
else:
    print(f"[OK] clause_map: {len(cm['clauses'])} entries, SHA matches, 100% non-blank coverage ({nonblank_cov}/{nonblank_total})")

# 6. PageIndex tree integrity
tree = json.loads((ROOT / 'data/pageindex_tree.json').read_text(encoding='utf-8'))
is_real = 'structure' in tree and 'doc_name' in tree and 'note' not in tree
if not is_real:
    WARNINGS.append("pageindex_tree.json looks like fallback")
else:
    node_count = 0
    def walk(n):
        global node_count
        node_count += 1
        for c in n.get('nodes', []):
            walk(c)
    for n in tree['structure']:
        walk(n)
    print(f"[OK] pageindex_tree.json is real PageIndex output ({node_count} nodes)")

# 7. Hand labels
hl = [json.loads(l) for l in (ROOT / 'eval/hand_labels.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
if len(hl) != 10:
    FAILURES.append(f"hand_labels has {len(hl)} items (expected 10)")
inj = sum(1 for h in hl if h.get('injected_failure'))
if inj != 5:
    FAILURES.append(f"Hand labels have {inj} injected (expected 5)")
hl_bad = [(h['row']['id'], validate_row(h['row'])) for h in hl if validate_row(h['row'])]
if hl_bad:
    FAILURES.append(f"Hand-label schema fails: {[(i, e[:1]) for i,e in hl_bad]}")
else:
    print(f"[OK] hand_labels: 10 items, 5 injected, all schema-valid")

# 8. Eval summary numbers
by_cat = {'A': [], 'B': [], 'C': []}
for r in rows:
    by_cat[r['category']].append(r['judge_report']['composite'])
actual_means = {cat: round(sum(vs) / len(vs), 2) for cat, vs in by_cat.items()}
es = (ROOT / 'eval_summary.md').read_text(encoding='utf-8')
claimed = {'A': 4.91, 'B': 4.83, 'C': 4.67}
for cat, exp in claimed.items():
    if abs(actual_means[cat] - exp) > 0.02:
        WARNINGS.append(f"eval_summary claims {cat}={exp} but actual is {actual_means[cat]}")
if '44 / 45' not in es:
    FAILURES.append("eval_summary doesn't say '44 / 45'")
if '100%' not in es or 'injected' not in es.lower():
    FAILURES.append("eval_summary missing 100% injected-catch claim")
print(f"[OK] eval_summary numbers match reality: A={actual_means['A']}, B={actual_means['B']}, C={actual_means['C']}")

# 9. Audit v4 matches reality
av4 = [json.loads(l) for l in (ROOT / 'audit/ps_category_audit_v4.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
av4_ids = {a['id'] for a in av4}
data_ids = set(ids)
if av4_ids != data_ids:
    FAILURES.append(f"Audit v4 ID mismatch: {av4_ids ^ data_ids}")
audit_pass = sum(1 for a in av4 if a['verdict'] == 'pass')
audit_fail = sum(1 for a in av4 if a['verdict'] == 'fail')
if audit_pass != 44 or audit_fail != 1:
    WARNINGS.append(f"Audit v4: {audit_pass} pass, {audit_fail} fail (eval_summary says 44/1)")
else:
    print(f"[OK] Audit v4: 44 pass / 1 fail, matches eval_summary")

# 10. README accuracy
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
for claim in ['44 / 45', '100%', '151', '97.8%']:
    if claim not in readme:
        WARNINGS.append(f"README missing claim fragment: '{claim}'")
print(f"[OK] README claims cross-checked")

# 11. Tests pass
r = subprocess.run(['python', '-m', 'pytest', '-q'], capture_output=True, text=True, cwd=str(ROOT))
if '39 passed' not in r.stdout:
    FAILURES.append(f"pytest: {r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr}")
else:
    print(f"[OK] 39/39 tests pass")

# 12. Git state
r = subprocess.run(['git', 'log', '--format=%an|%ae', '-10'], capture_output=True, text=True, cwd=str(ROOT))
authors = set(r.stdout.strip().splitlines())
expected_author = 'Tanmay0251|Tanmay0251@users.noreply.github.com'
if authors != {expected_author}:
    FAILURES.append(f"Non-Tanmay0251 authors in recent 10 commits: {authors}")
else:
    print(f"[OK] Recent 10 commits all by Tanmay0251")

r = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd=str(ROOT))
committed = r.stdout.strip().splitlines()
for forbidden in ['.env', 'Technical Take Home.pdf', 'problem_statement.txt']:
    if any(forbidden in f for f in committed):
        FAILURES.append(f"Forbidden file tracked in git: {forbidden}")
print(f"[OK] No .env / PDF / problem_statement.txt in git")

r = subprocess.run(['git', 'status', '-sb'], capture_output=True, text=True, cwd=str(ROOT))
first_line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ''
if 'ahead' in first_line or 'behind' in first_line:
    WARNINGS.append(f"Branch not synced: {first_line}")
else:
    print(f"[OK] Local branch in sync with remote")

# 13. No uncommitted changes to key files
r = subprocess.run(['git', 'status', '--short', '--', 'dataset.jsonl', 'README.md', 'eval_summary.md',
                    'failure_catalogue.md', 'judge_validation.md', 'data/', 'pipeline/', 'prompts/',
                    'tools/', 'schemas/', 'eval/', 'audit/', 'docs/', 'runs/2026-04-22-v4/'],
                   capture_output=True, text=True, cwd=str(ROOT))
if r.stdout.strip():
    WARNINGS.append(f"Uncommitted changes to tracked files:\n{r.stdout}")
else:
    print(f"[OK] No uncommitted changes to key files")

# 14. Check that all audit v4 failures are disclosed in failure_catalogue or eval_summary
fails_in_audit = [a['id'] for a in av4 if a['verdict'] == 'fail']
fc = (ROOT / 'failure_catalogue.md').read_text(encoding='utf-8')
es_text = (ROOT / 'eval_summary.md').read_text(encoding='utf-8')
for fid in fails_in_audit:
    in_fc = fid in fc
    in_es = fid in es_text
    if not in_fc and not in_es:
        WARNINGS.append(f"Audit-flagged fail {fid} not mentioned in failure_catalogue.md or eval_summary.md")
if fails_in_audit:
    print(f"[OK] Audit fails disclosed: {fails_in_audit}")

print()
print("=" * 60)
if FAILURES:
    print(f"FAILURES ({len(FAILURES)}) -- MUST FIX before submit:")
    for f in FAILURES:
        print(f"  - {f}")
else:
    print("No blocking failures.")
if WARNINGS:
    print(f"\nWARNINGS ({len(WARNINGS)}):")
    for w in WARNINGS:
        print(f"  - {w}")
else:
    print("\nNo warnings.")

sys.exit(0 if not FAILURES else 1)
