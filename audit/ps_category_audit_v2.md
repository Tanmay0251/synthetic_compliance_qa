# Independent PS-category audit (v2)

_Fresh audit of the regenerated 45-row dataset. Pass/fail is against the PS criteria verbatim; judges and scores were not consulted._

## Summary

| Category | Rows | Pass | Fail | Pass rate |
|---|---|---|---|---|
| A | 15 | 15 | 0 | 100.0% |
| B | 15 | 10 | 5 | 66.7% |
| C | 15 | 15 | 0 | 100.0% |
| Total | 45 | 40 | 5 | 88.9% |

## Category A — passes

All 15 A rows cite a specific clause whose verbatim text unambiguously answers the question. No hedging, no scope mismatches this time. Notes:

- **A-007** — the v1 scope-mismatch failure (INR 25 lakh PA-CB-Outward cap being applied to a domestic scenario) is gone. The current A-007 is the Optimizer SaaS-vs-PSP question under Part B Part I §7.1, which resolves cleanly.
- **A-015** — regenerated under gen-a-v2. Part A §8.1 is cited for both the integration-harm indemnity and the survival-after-termination leg; both excerpts are verbatim.

## Category A failures
None.

## Category B failures

### B-002 — FAIL: axis already pre-answered by the question's own facts
The question explicitly states: "outstanding balance owed to Razorpay under a separate lending product agreement with one of their Group Entities." Part A §14.2 directly covers set-off against "any other agreement between You and Razorpay PA or its Group Entities" — direct Cat A. The clarifying question's "is this under the current Services agreement or a separate one?" fork pretends the user hasn't already told us it's the Group-Entity case. The §1(f) branch answers a scenario the user didn't describe.

### B-006 — FAIL: question specifies whose materials are in question; direct Cat A exists
Question text: "does Razorpay need to ask us before featuring our brand in their promotional materials." That is specifically about Razorpay using the merchant's materials → Part A §1.2 (irrevocable license, no incremental consent). The "merchant using Razorpay's marks" branch (§1.1) answers a different question than the one asked. Axis "whose_materials_are_in_question" is fabricated by stripping a fact out of the question.

### B-007 — FAIL: both branches are concurrent obligations, so Cat A can list both
Branch 1 (§12.4: don't store card data) and Branch 2 (§6.2: PCI-DSS + annual report) are **simultaneously binding** on any merchant — not mutually-exclusive operational regimes. A Cat A answer "comply with PCI-DSS/PA-DSS, submit annual proof of compliance, and do not store sensitive card credentials in your systems" directly satisfies the question. The clarification collapses the obligation set rather than forking it. Same structural flaw as the v1 "concurrent charges" pattern.

### B-012 — FAIL: question's fact pattern is already on §2.25; branch 2 is unresponsive
"We got hit with a fine from a card association that Razorpay says it's going to recover from our settlement." Card-association fine → §2.25 directly ("in case any penalty/other liability is imposed/passed on to Razorpay PA by a law enforcement agency, regulatory body, Card Association, or Facility Provider..."). Direct Cat A: yes, settlement deduction PLUS separate proceedings. The Permissible-Deductions-only branch applies to a fact pattern (direct Razorpay fee / chargeback) that contradicts what the question describes.

### B-015 — FAIL: both branches cite the same clause; fork is a factual pre-condition, not an ambiguity
Both answer_branches cite the same verbatim excerpt of Part B Part I §3.1 ("subject to availability of funds received in the Escrow Account, You are entitled to effect Refunds at Your sole discretion"). The clause itself already encodes the condition. A direct Cat A answer "no Razorpay approval is needed — you can trigger refunds at your sole discretion, subject to sufficient funds in the Escrow Account" covers both states. The merchant already knows their own escrow balance; Razorpay has no privileged information to clarify here.

## Category B passes

B-001, B-003, B-004, B-005, B-008, B-009, B-010, B-011, B-013, B-014.

Notes on passes:
- **B-001** (refund handling): genuine fork between customer refund (§2.9: merchant's sole responsibility) vs. Razorpay-initiated withhold-and-refund-to-source (§1(h)). Two distinct operational regimes.
- **B-003** (KYC issue suspension): §2.2 (inaccurate existing info → immediate suspend + terminate) vs. §2.8 (non-submission of requested docs → suspend until submitted, no termination). Worst-case outcomes materially differ; axis load-bearing.
- **B-004** (fee increase): trigger-type fork. Statutory tax (§3.2, no opt-out on any service) vs. Razorpay-priced VAS (§14.3, continued use = consent, avoidable by not using the service). For a given specific fee hike, the answer is one or the other; clarification is legitimate.
- **B-005** (recovery process): penalty (§2.25 — deduction + separate legal proceedings, no timeline) vs. chargeback (§2.3 — two-step with 7-day debit-note window). Process and timeline genuinely differ.
- **B-008** (settlement impact of compliance issue): §3.4 reconciliation discrepancy (Razorpay-liability disclaimer if late) vs. §9.3 card-network non-compliance (forthwith reimburse + suspend/terminate). Materially different settlement consequences.
- **B-009** (recovery mechanism): §1(c) early-settled transaction not received in escrow within 3 days → absolute recovery right vs. §1(f) Facility-Provider-attributable debits → discretionary set-off + shortfall obligation.
- **B-010** (cross-border settlement timeline): PA-CB Inward 15 days (§1.1) vs. PA-CB Outward 25 days (§IB.1.2). Directly different numeric timelines.
- **B-011** (fee billing mechanism): Fee Credits present → fees from credits, full settlement vs. no credits → fees from Transaction Amount as Permissible Deduction, reduced settlement. §1(e) covers both paths; the merchant's Fee-Credit balance determines which applies.
- **B-013** (e-mandate fraud settlement): already-settled → §4.2 RBI-circular dispute process (Razorpay can't unilaterally claw back) vs. not-yet-settled → Part B Part II Withholding Rights (Razorpay can withhold pre-emptively). Materially different merchant exposure.
- **B-014** (TokenHQ consent UI): Part B Part III Consent text is literally "You shall, except in the case of standard checkout..." — the carve-out is explicit and the fork on checkout_type is drawn directly from the clause structure. Operational work differs materially.

## Category C — passes

All 15 pass. Each C row names what IS known (with citation), what is missing, and specific escalation paths (Razorpay support, external counsel, RBI/NPCI guidance). No row resolves with confident language like "clearly" or "definitely".

- **C-001 / C-006**: "reasonable grounds" vague-language questions — genuinely qualitative standard without thresholds.
- **C-002 / C-007 / C-010 / C-015**: silence on procedural protections (contest/audit, wind-down, fee-cap/notice, reasonableness of indemnified fees).
- **C-003**: AFA-succeeded-but-first-transaction-failed retry gap — genuinely silent.
- **C-004 / C-008 / C-011**: external deferral to RBI/NPCI rules (chargeback precedence, post-settlement fraud, white-label IP + PA guidelines).
- **C-005**: GST pass-through mechanics (cap, notice, calculation, retro demands) — vague.
- **C-009**: TDS withholding rate + DTAA-certificate equivalence — external deferral to Indian income tax law and home jurisdiction.
- **C-012** (v2): escrow "receipt" meaning for partial credits — genuine silence, deferred to RBI PA Guidelines.
- **C-013** (v2): §14.3 notice period and regulatory constraints on unilateral fee changes — external deferral to RBI PA framework.
- **C-014** (v2): amended-invoice / credit-note / GSTR rectification obligations when GSTIN was outdated at invoice time — §3.7 is silent on post-invoice remediation.

## Overall verdict

v2 is a material improvement. Category A is now clean (15/15), the recycled tax-vs-late-interest B split is gone, and Category B rises from 2/15 to 10/15. The five remaining B failures are a different and more nuanced class of defect: the axis either strips facts from the question (B-002, B-006, B-012), collapses two concurrent obligations into a fake choice (B-007), or forks on a factual state the merchant already knows (B-015). Category C still leans on thematic duplicates but every row individually meets the criteria. Honest overall pass rate: **40/45 (88.9%)**.
