# Independent PS-category audit (v3)

_Fresh audit of the second round of regeneration. The 5 B rows that failed the v2 audit (v2 IDs B-002, B-006, B-007, B-012, B-015) were dropped and replaced under a stricter axis-first prompt (gen-b-v3). Pass/fail is decided against the PS criteria verbatim; judges and scores were not consulted._

## Summary

| Category | Rows | Pass | Fail | Pass rate |
|---|---|---|---|---|
| A | 15 | 15 | 0 | 100.0% |
| B | 15 | 13 | 2 | 86.7% |
| C | 15 | 15 | 0 | 100.0% |
| Total | 45 | 43 | 2 | 95.6% |

## Round-2 (gen-b-v3) regens

The 5 rows generated under prompt gen-b-v3 (all timestamped 2026-04-22T15:38 – 15:44, i.e. after 2026-04-21T09:10) are: **B-009, B-010, B-012, B-014, B-015**. These are the slots that replaced the v2 failures. Four of the five (B-009, B-010, B-012, B-014) are clean. One (B-015) still exhibits the v2 "concurrent obligations presented as alternatives" defect class.

## Category A — passes

All 15 A rows cite a specific clause whose verbatim text unambiguously answers the question. No new A regens were needed in round 2; A-015 is still the gen-a-v2 row (Part A §8.1 integration indemnity + survival), which resolves cleanly. A-007 still cleanly resolves the Optimizer SaaS-vs-PSP split under Part B Part I §7.1.

## Category A failures

None.

## Category B failures

### B-006 — FAIL: question's own fact pattern is directly on §1(f); §1(c) branch is unresponsive
The question text is **identical** to the Cat A question at A-006 ("Razorpay deducted some money from our next settlement payout to recover a charge that was debited from our account by one of their facility providers"). The fact pattern — a Facility-Provider debit charged to Razorpay and recovered via settlement deduction — is verbatim the trigger condition in Part B Part I §1(f): "amounts from You that are charged to Razorpay PA and/or debited by Facility Providers from accounts maintained by You ... by way of deduction from (i) the Transaction Amount to be settled to You". This is a direct Cat A. The §1(c) branch (early-settled Transaction Amount not received in escrow within 3 days) describes a fact pattern the question explicitly did not raise. Same "axis pre-revealed by question facts" failure mode that killed v2 B-002, B-006, B-012.

### B-015 — FAIL: branches are concurrent PCI / data-handling obligations, not alternatives
The question asks "beyond just not storing it, are there any additional active steps or written obligations" — a direct request for the full obligation set. §12.4 (no storage of full card credentials) and §6.1 (no-storage + immediate written notification on suspected breach + written certification on demand) are **simultaneously binding** on every merchant. Branch 1 ("obligation is solely to refrain from storing ... no additional affirmative written steps") is factually wrong under the same ToS that makes §6.1's notification and certification duties unconditional and ongoing. A Cat A answer listing §6.1's notification + on-demand certification and §6.2's PCI-DSS + annual-proof obligation directly answers the question. Same structural defect as v2 B-007 (concurrent PCI obligations collapsed into a fake fork).

## Category B passes

B-001, B-002, B-003, B-004, B-005, B-007, B-008, B-009, B-010, B-011, B-012, B-013, B-014.

Notes on the five gen-b-v3 regens:
- **B-009** (co-marketing IP direction): axis draws the §1.1 / §1.2 split from a generically-worded "logos and brand assets on promotional materials" question. Fixes the v2 B-006 defect where the question specifically said "Razorpay using our brand in their materials".
- **B-010** (source of liability for set-off): axis forks §14.2 (liability under any agreement with Razorpay PA or Group Entities, no prior notice) vs §1(f) (Facility-Provider charge, sole discretion). Question text is generic ("an amount from our settlement payout"), so the Group-Entity fact is not pre-revealed the way v2 B-002 pre-revealed it.
- **B-012** (suspension reinstatement path): forks §2.8 (KYC non-submission → merchant can cure) vs §4.1 (Facility-Provider fraud investigation → merchant cannot unilaterally cure). Fixes the v2 B-012 card-association-fine fact-pattern pre-reveal.
- **B-014** (liability cap vs post-termination): forks §7.2 (cap = 1 month fees, proportional reduction) vs §16.3 (no liability post-termination). Two distinct regimes keyed to a fact that the merchant could reasonably not volunteer. Replaces the v2 B-007 concurrent-PCI defect cleanly.
- **B-015** (storage vs breach-trigger): this is the one regen that does not land. See failure analysis above.

Other passes (unchanged from v2):
- **B-001** refund scenario type — §2.9 vs §1(h).
- **B-002** KYC issue type — §2.2 (inaccurate info → termination) vs §2.8 (non-submission → cure). (This is a fresh regen in v3, not the v2 B-002 text.)
- **B-003** fee increase trigger — §3.2 vs §14.3.
- **B-004** recovery trigger — §2.25 vs §2.3.
- **B-005** compliance issue type — §3.4 vs §9.3.
- **B-007** cross-border direction — Part I §1.1 (15 days, inward) vs Part IB §1.2 (25 days, outward).
- **B-008** fee-credit availability — §1(e) branches cited with different excerpts covering two operationally distinct settlement flows. Borderline but accepted on the same rationale as v2 B-011.
- **B-011** e-mandate settlement status — §4.2 (already-settled, RBI dispute process) vs Part II Withholding (not-yet-settled, pre-emptive withhold).
- **B-013** TokenHQ checkout type — Part III Consent carve-out explicitly draws the standard-vs-custom axis.

## Category C — passes

All 15 pass. Each C row names what IS known (with verbatim cite), what is missing, and at least one specific escalation path (Razorpay support / external counsel / named RBI or NPCI circulars). No row closes with a confident "clearly" / "definitely" framing.

- **C-001 / C-006**: "reasonable grounds" vague-language questions. Qualitative standard with no threshold.
- **C-002 / C-007 / C-010 / C-015**: silence on merchant procedural protections (contest/audit, wind-down, fee cap/notice, indemnified-fee reasonableness benchmark).
- **C-003**: AFA-succeeded-first-txn-failed retry gap. Genuine silence.
- **C-004 / C-008 / C-011**: external deferral to RBI / NPCI (chargeback precedence, post-settlement fraud circulars, white-label IP + PA guidelines).
- **C-005**: GST pass-through mechanics (cap, notice, calculation, retro demands).
- **C-009**: non-resident TDS rate + DTAA certificate equivalence. External deferral to Indian income tax law and home-jurisdiction rules.
- **C-012**: escrow "receipt" meaning for partial credits — RBI PA Guidelines deferral.
- **C-013**: §14.3 notice period and RBI-PA constraints on unilateral fee change.
- **C-014**: post-invoice GST remediation when GSTIN was outdated at invoice time. §3.7 silent; deferral to CGST Act.

## Did the two v2-era defect patterns disappear?

- **"Pre-revealed axis" (question's own facts already pin the answer):** Mostly yes. The gen-b-v3 regens (B-009 generic co-marketing, B-010 generic set-off, B-012 generic suspension, B-014 generic loss-recovery) are all properly axis-blind. But the pattern re-surfaced at **B-006**, which was a gen-b-v2 row the v2 auditor had *passed*. On closer reading, B-006's question is near-identical to A-006's and the Facility-Provider fact pattern is directly on §1(f) — the §1(c) branch answers a scenario the user never described.
- **"Both branches citing the same excerpt":** Gone. No B row in v3 has this defect (v2 B-015 was the only instance).
- **"Concurrent obligations as alternatives":** Partially recurred. Gone from the regens at B-007 and B-012 positions (which now correctly fork on either mutually-exclusive fact patterns or genuinely different regimes), but re-appeared at the B-015 slot itself — the new B-015 collapses the standing data-handling obligation set (§6.1 + §6.2 + §12.4) into a fake baseline-vs-breach fork.

## Overall verdict

v3 shows real progress: 43/45 (95.6%) vs 40/45 in v2. Of the 5 targeted regens, 4 land cleanly; only the B-015 slot swapped one concurrent-obligations defect for another. One previously-passed row (B-006) fails on closer inspection because its question is functionally a duplicate of A-006's. Honest overall pass rate: **43/45 (95.6%)**.
