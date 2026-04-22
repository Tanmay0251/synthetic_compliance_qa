# Independent PS-category audit

_Done by a fresh auditor, not using the pipeline's judges. Pass/fail is against the PS criteria verbatim._

## Summary

| Category | Rows | Pass | Fail | Pass rate |
|---|---|---|---|---|
| A | 15 | 14 | 1 | 93.3% |
| B | 15 | 2 | 13 | 13.3% |
| C | 15 | 15 | 0 | 100.0% |
| Total | 45 | 31 | 14 | 68.9% |

## Category A failures

### A-007 — FAIL: cited clause scope doesn't cover the question's fact pattern
Part B Part IB §1.13 (INR 25 lakh transaction cap) sits inside "Part IB: Specific Terms Applicable to PA-CB Outward Transactions" — i.e. cross-border outward only. The question describes a merchant doing "enterprise clients pay invoices directly through our Razorpay Payment Aggregator integration" with no indication of cross-border. For a domestic INR 30 lakh invoice, §1.13 does not apply and the ToS is actually silent on a domestic per-transaction cap. The answer's blanket "No, Razorpay PA cannot process that" requires an unstated assumption (cross-border outward), so the citation does not unambiguously answer the question.

## Category B failures

### B-001 — FAIL: axis is not load-bearing; question answerable directly as Cat A
"What additional charges can Razorpay apply on top of the base fees" naturally admits both answer branches simultaneously — tax pass-through and late-payment interest are concurrent, not alternative. A good Cat A answer would list both. The "charge_type" axis is fabricated.

### B-002 — FAIL: axis does not change the answer
Both Fee-Credits and Transaction-Amount-deduction branches resolve to the same liability cap under §7.2 — "one month fees paid by You for the specific Service(s)". The method of fee payment does not change the cap calculation. The axis is not load-bearing.

### B-003 — FAIL: both branches converge on "yes, fees still owed"
The "timing of refund relative to termination" axis produces identical outcomes — §3.4 makes fees payable regardless of refund, and §16.3 preserves pre-termination obligations. A direct Cat A "yes, you still owe the fees" with both citations would satisfy the question.

### B-004 — FAIL: recycled structural flaw of B-001
Another "additional charges on top of stated fees" iteration. Same taxes-vs-late-interest split, same concurrent-not-alternative problem.

### B-005 — FAIL: question explicitly asks both sub-questions
"If I don't pay my fees on time, what additional charges will I face, AND who bears the cost of any tax increases" literally asks both parts at once. There is no missing context; a Cat A answer covering both clauses is correct.

### B-006 — FAIL: recycled structural flaw of B-001
"Charges beyond base fees if I don't pay on time or if tax rates change" — both clauses apply, no fork is needed.

### B-008 — FAIL: axis is forced; §2.25 isn't actually triggered by "failure to pay"
The question frames "If I fail to pay an amount owed". §2.25 (recovery of third-party-imposed penalties from settlement) is triggered by a regulator/Card Association/Facility Provider hitting Razorpay with a penalty attributable to the merchant — not by the merchant "failing to pay". Only §1.4(c)(i) late-payment interest is actually responsive to the question framing. The third-party-penalty branch does not answer the question the user asked.

### B-010 — FAIL: question explicitly asks both sub-questions
"Will I have to pay extra charges on top of the overdue amount, AND how does tax treatment apply to those charges" — both parts are explicit. Direct Cat A suffices.

### B-011 — FAIL: one branch is fabricated; question has a direct Cat A answer
The question explicitly references a customer contesting a convenience fee charge. The "reconciliation_discrepancy" branch is a stretched alternative interpretation not supported by the question's framing. A direct §2.20 answer is correct.

### B-012 — FAIL: recycled structural flaw of B-001
Fourth "additional charges on top of stated fees" iteration with the same tax-vs-late-interest split.

### B-013 — FAIL: second branch is a fabricated edge case; direct Cat A answer exists
"If a payment is refunded back to the customer, do I still owe Razorpay any fees?" has a direct Cat A answer under §3.4. The "Razorpay-initiated refund under §1(h)" branch is a contrived edge case — §1(h) deals with withholding unsettled funds and refunding to source, which is not really a "refund" as the question uses the term. The axis is forced.

### B-014 — FAIL: recycled structural flaw of B-001
Fifth iteration of the same "additional charges on top of base fees" question with the same split.

### B-015 — FAIL: second branch does not answer the question; axis not load-bearing
"If I issue a refund, do I still have to pay Razorpay's fees?" is answered directly by §3.4. The "right to issue refund" branch (§3.1) answers a different question (can I refund?) — not the fee-liability question that was asked. Cat A is the right category.

## Category C failures
None.

## Category A PASSES
A-001, A-002, A-003, A-004, A-005, A-006, A-008, A-009, A-010, A-011, A-012, A-013, A-014, A-015

## Category B PASSES
B-007, B-009

Notes:
- **B-007** (recovery process for penalty vs. chargeback): the process and timeline genuinely differ — penalty recovery per §2.25 has no specific deadline, chargeback recovery per §2.3 has a two-step process with a specific 7-day debit-note window. Load-bearing axis.
- **B-009** (settlement impact of a compliance issue): the "compliance issue" framing is genuinely broad; §3.4 reconciliation discrepancies vs. §9.3 card-network non-compliance produce materially different outcomes (disclaimer of Razorpay liability vs. explicit suspension/termination rights). Load-bearing axis.

## Category C PASSES
C-001, C-002, C-003, C-004, C-005, C-006, C-007, C-008, C-009, C-010, C-011, C-012, C-013, C-014, C-015

Notes on C:
- Several rows are thematic duplicates: **C-004 ≈ C-011** (chargeback rules + RBI/NPCI precedence), **C-008 ≈ C-013** (post-settlement fraud resolution), **C-005 ≈ C-014** (GST pass-through cap/notice), **C-012 ≈ C-015** (white-label IP vs. regulation). Each row individually meets the Cat C criteria, but the dataset clusters around a small number of genuinely-ambiguous topics rather than surveying ambiguity broadly across the ToS.
- **C-004 and C-011 are borderline**: §2.1–§2.4 do contain concrete chargeback mechanics (3-day document window, Facility Provider reversal power, 7-day debit-note reimbursement), which a careful reader could cite. However, both questions specifically ask about the conflict/precedence between Razorpay's Terms and external RBI/NPCI rules — and that second leg is genuinely unaddressed by the ToS, so these stay in Cat C territory.

## Overall verdict

Category A and Category C hold up honestly — A is 14/15 with a single scope-mismatch failure (A-007), and C is 15/15 though heavy on thematic duplicates. Category B is the weak spine of the dataset: 13/15 rows fail, with a dominant structural flaw where seven rows (B-001/B-004/B-005/B-006/B-010/B-012/B-014) re-use the same "statutory-tax-variation vs. 15%-late-payment-interest" split on cosmetically reworded "what additional charges" questions where both clauses apply concurrently and the axis is not load-bearing. A further five B rows fail for related reasons (both branches converge, one branch is fabricated, or the second branch doesn't address the question). The honest overall pass rate is 31/45 (~69%); any reported 100% figure would substantially overstate the dataset's integrity on the Cat B dimension.
