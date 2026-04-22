# Audit delta (v1 → v2)

| Category | v1 pass | v2 pass | delta |
|---|---|---|---|
| A | 14/15 | 15/15 | +1 |
| B | 2/15 | 10/15 | +8 |
| C | 15/15 | 15/15 | 0 |
| **Total** | **31/45** | **40/45** | **+9** |

## Changes
- The dominant v1 failure pattern — seven B rows recycling a "statutory-tax-variation vs. 15% late-payment-interest" fork on cosmetically reworded "what additional charges apply" questions where both clauses applied concurrently — is entirely gone in v2. B rows now use a diverse set of axes (refund scenario, KYC issue type, fee trigger, recovery trigger, compliance-issue type, cross-border direction, fee-credit availability, settlement status, checkout type), and each passing row forks on a clause-grounded fact that materially changes the operational conclusion.
- New residual B-failure class (5 rows): fake forks driven by either (a) the axis being pre-answered by facts already in the question (B-002, B-006, B-012), (b) two concurrent obligations being presented as alternatives when a Cat A can list both (B-007), or (c) both branches citing the same clause with a fork on a factual state the merchant already knows (B-015). The single v1 Category A scope-mismatch (PA-CB-Outward §1.13 applied to a domestic scenario) has been removed and the new A-007 (Optimizer SaaS-vs-PSP under Part B Part I §7.1) resolves cleanly.
