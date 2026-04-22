# Run report (post-topup)

- Dataset rows: 45 (A=15, B=15, C=15)
- Total cost (USD): 9.4997 (initial 7.8119 + topup 1.6878)
- Wall seconds: initial 2312s + topup 494s
- LLM calls: 297

## Composite score by category

- A: mean 4.94 over 15 rows
- B: mean 4.64 over 15 rows
- C: mean 4.86 over 15 rows

## Note

Category C initial run produced 9 rows (below 15-target) due to JSON-parse failures on long-form ambiguity responses. Topup stage ran generator C a second time with higher over-generation (2×) and seed offset; see `topup_metrics.json` for cost breakdown. Failure patterns are documented in `failure_catalogue.md`.

See `judge_validation.md` and `failure_catalogue.md` for detail.