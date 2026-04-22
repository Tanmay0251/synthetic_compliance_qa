# Audit delta (v1 → v2 → v3 → v4)

| Category | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| A | 14/15 | 15/15 | 15/15 | 15/15 |
| B | 2/15 | 10/15 | 13/15 | 14/15 |
| C | 15/15 | 15/15 | 15/15 | 15/15 |
| **Total** | **31/45** | **40/45** | **43/45** | **44/45** |

## Changes v1 → v2
- The dominant v1 failure pattern — seven B rows recycling a "statutory-tax-variation vs. 15% late-payment-interest" fork on cosmetically reworded "what additional charges apply" questions where both clauses applied concurrently — is entirely gone in v2. B rows now use a diverse set of axes (refund scenario, KYC issue type, fee trigger, recovery trigger, compliance-issue type, cross-border direction, fee-credit availability, settlement status, checkout type), and each passing row forks on a clause-grounded fact that materially changes the operational conclusion.
- New residual B-failure class (5 rows): fake forks driven by either (a) the axis being pre-answered by facts already in the question (v2 B-002, v2 B-006, v2 B-012), (b) two concurrent obligations being presented as alternatives when a Cat A can list both (v2 B-007), or (c) both branches citing the same clause with a fork on a factual state the merchant already knows (v2 B-015). The single v1 Category A scope-mismatch (PA-CB-Outward §1.13 applied to a domestic scenario) has been removed and the new A-007 (Optimizer SaaS-vs-PSP under Part B Part I §7.1) resolves cleanly.

## Changes v2 → v3
- The five v2 failures (B-002, B-006, B-007, B-012, B-015 in v2 numbering) were dropped and replaced with fresh gen-b-v3 generations at slots B-009, B-010, B-012, B-014, B-015 under a stricter axis-first prompt (forbid pre-revealing the axis value in the question; forbid both branches citing the same excerpt). Four of the five regens land cleanly; the B-015 slot swaps the v2 "same-excerpt" defect for a v2-style "concurrent obligations as alternatives" defect.
- The "same-excerpt" pattern (both branches citing identical verbatim text) is fully eliminated in v3.
- The "pre-revealed axis" pattern reappears at **B-006** (a gen-b-v2 row the v2 auditor passed): its question is functionally identical to the A-006 question and the fact pattern is directly on §1(f); the §1(c) branch answers a scenario the user never raised.
- Net: +3 B passes over v2 (40 → 43), A and C unchanged at 15/15.

## Changes v3 → v4
- **Clause map expanded from 80 clauses (hand-curated, ~19% of ToS text by earlier audits) to 151 clauses covering the full ToS.** The expansion pulled in 36 `gap_fill_from_tree` clauses, 19 `gap_fill_content` clauses, and 16 `pageindex_tree` clauses alongside the original 80 hand-curated clauses, plus a merged PageIndex tree (`data/pageindex_tree.json`).
- **Full dataset regeneration.** All 45 rows are fresh; no carry-over from v3. Seeds now span 16 distinct section buckets of the ToS (v3 was concentrated in Part A + Part B Part I).
- 26 of 30 B-seed slots use `gap_fill_from_tree` coarser-text clauses (e.g., `PAYMENT PROCESSING: lines 746-760` bundles §§1.6–1.12). Despite coarser seeds, Cat B extraction quality did not degrade — most rows cleanly pinned specific sub-clauses in both branches. The gap-fill path did not produce category-specific failures; the single v4 B failure (B-004) is the same "concurrent obligations as alternatives" defect class that recurs across all rounds.
- **v3 B-006 "pre-revealed axis" and v3 B-015 "concurrent PCI-obligations" are both gone.** The generator's axis-blind discipline held on the v3-era failure patterns.
- **"Concurrent obligations as alternatives" defect migrates to B-004** (RBI/KYC vs. Card Network Rules). A merchant processing transactions must comply with both frameworks simultaneously; the axis fork is cosmetic because a direct Cat A answer covering both §2.6 and §9.2 resolves the question. This defect class now has exactly one B-row instance in each of v2, v3, and v4 — just at different slots each round.
- **Two diversity wastes introduced by regeneration**:
  - A-006 and A-009 are near-duplicate questions (both ask "how many days to return rental POS device", both cite the same verbatim excerpt from Part IA lines 673-716).
  - C-001 and C-005 both seed from PA-Guidelines §6 and both ask about undefined "promptly" in breach reporting. Each passes PS criteria individually; the pair still burns two slots on one ambiguity.
- **Topic and section diversity genuinely improved**: distinct sections touched in seeds include Part IA offline-PA (6), PA-Guidelines §6 (5), PAYMENT PROCESSING cross-border block (5), USAGE block §2.x (6), Definitions (5), Part III TokenHQ (3), Part IV Subscription (2), Part B Part II E-Mandate (1), SNRR (1), Part B Part IB cross-border (1), plus INDEMNITY/§9 Card-Association (1) and ADDITIONAL TERMS §14.x (1). v3 was dominated by Part A §§2–3–9 and Part B Part I §§1–7.
- **Remaining gaps worth flagging**: Part A §8 indemnity mechanics, LRS §1.19, white-label PA, Affordability/BNPL, and Chargeback operational mechanics (§§2.1–2.3) each have ≤1 row.
- Net: +1 B pass over v3 (43 → 44), A and C unchanged at 15/15. Overall 44/45 (97.8%).
