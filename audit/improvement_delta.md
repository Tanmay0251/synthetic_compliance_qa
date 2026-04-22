# Audit delta (v1 → v2 → v3)

| Category | v1 | v2 | v3 |
|---|---|---|---|
| A | 14/15 | 15/15 | 15/15 |
| B | 2/15 | 10/15 | 13/15 |
| C | 15/15 | 15/15 | 15/15 |
| **Total** | **31/45** | **40/45** | **43/45** |

## Changes v1 → v2
- The dominant v1 failure pattern — seven B rows recycling a "statutory-tax-variation vs. 15% late-payment-interest" fork on cosmetically reworded "what additional charges apply" questions where both clauses applied concurrently — is entirely gone in v2. B rows now use a diverse set of axes (refund scenario, KYC issue type, fee trigger, recovery trigger, compliance-issue type, cross-border direction, fee-credit availability, settlement status, checkout type), and each passing row forks on a clause-grounded fact that materially changes the operational conclusion.
- New residual B-failure class (5 rows): fake forks driven by either (a) the axis being pre-answered by facts already in the question (v2 B-002, v2 B-006, v2 B-012), (b) two concurrent obligations being presented as alternatives when a Cat A can list both (v2 B-007), or (c) both branches citing the same clause with a fork on a factual state the merchant already knows (v2 B-015). The single v1 Category A scope-mismatch (PA-CB-Outward §1.13 applied to a domestic scenario) has been removed and the new A-007 (Optimizer SaaS-vs-PSP under Part B Part I §7.1) resolves cleanly.

## Changes v2 → v3
- The five v2 failures (B-002, B-006, B-007, B-012, B-015 in v2 numbering) were dropped and replaced with fresh gen-b-v3 generations at slots B-009, B-010, B-012, B-014, B-015 under a stricter axis-first prompt (forbid pre-revealing the axis value in the question; forbid both branches citing the same excerpt). Four of the five regens land cleanly; the B-015 slot swaps the v2 "same-excerpt" defect for a v2-style "concurrent obligations as alternatives" defect.
- The "same-excerpt" pattern (both branches citing identical verbatim text) is fully eliminated in v3.
- The "pre-revealed axis" pattern reappears at **B-006** (a gen-b-v2 row the v2 auditor passed): its question is functionally identical to the A-006 question and the fact pattern is directly on §1(f); the §1(c) branch answers a scenario the user never raised.
- Net: +3 B passes over v2 (40 → 43), A and C unchanged at 15/15.
