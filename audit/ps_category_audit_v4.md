# Independent PS-category audit (v4)

_Fresh audit of the fully-regenerated dataset produced against the expanded 151-clause / 100%-coverage clause map (`data/clause_map.json`, merged 2026-04-22 from the real PageIndex tree). All 45 rows were regenerated against new seeds; no rows were carried over verbatim from v3. Pass/fail is decided against the PS criteria verbatim; judge scores and validator reports were not consulted._

## Summary

| Category | Rows | Pass | Fail | Pass rate |
|---|---|---|---|---|
| A | 15 | 15 | 0 | 100.0% |
| B | 15 | 14 | 1 | 93.3% |
| C | 15 | 15 | 0 | 100.0% |
| Total | 45 | 44 | 1 | 97.8% |

## What changed since v3

- Dataset was fully regenerated (gen-a-v2, gen-b-v3, gen-c-v2) against the expanded clause map. Seeds now span 16 distinct sections of the ToS vs. the v3 concentration on Part A / Part B Part I.
- 26 of 30 B-seed slots (per `generation_meta.seed_clause_ids`) reference gap-filled tree clauses ("SECTION: lines X-Y" style identifiers from `pageindex_tree`); only 4 B rows still seed from hand-curated clauses. Despite the coarser seeding, 14/15 B rows land cleanly — the single remaining failure (B-004) is a reincarnation of the v2/v3 "concurrent obligations presented as alternatives" defect.
- No carry-over of the v3 defects: the v3 B-006 "pre-revealed axis" pattern (fact-pattern identical to A-006) did not reappear, and the v3 B-015 "concurrent PCI obligations" defect is gone.

## Category A — passes

All 15 A rows cite a specific clause whose verbatim text unambiguously answers the question. Topic mix now genuinely spans: penalty-recovery (A-001), refund definition (A-002), breach-report destination (A-003), GST pass-through (A-004), logo-license consent (A-005), POS device rental return (A-006 and A-009 — see diversity note below), Optimizer SaaS role (A-010), PCI card-storage prohibition (A-011), third-party orchestrator approval (A-012), KYC-doc non-submission (A-013), Chargeback definition (A-014), and E-Mandate Sponsor Bank registration prerequisite (A-015).

All citations verified verbatim against `data/clause_map.json`.

### Category A failures

None.

### Diversity note on A

**A-006 and A-009 are near-duplicates.** Both ask "how many days does the merchant have to return a rented POS device after termination" and both cite the identical verbatim excerpt from `Part IA: Additional Terms For Offline Payment Aggr: lines 673-716` ("not less than 3 days"). They pass PS criteria individually but one of the two slots is wasted. Does not affect the verdict but is worth flagging — the de-dup step (if any) on the 15 Cat A slots did not catch it.

## Category B — passes

B-001, B-002, B-003, B-005, B-006, B-007, B-008, B-009, B-010, B-011, B-012, B-013, B-014, B-015.

Spot-checks on the passing rows:

- **B-001** (unilateral account action): forks Usage-Data sharing consent (§2.27) vs. excess-settlement clawback (§1.10). Two genuinely different kinds of "action" on the account (data disclosure vs. money movement). Load-bearing and the question is generic enough that neither axis value is pre-revealed.
- **B-002** (indemnity scope): forks Sub-Merchant indemnity (PP §1.14–1.18, which only applies "if you are accepting payments on behalf of sellers/clients") vs. TokenHQ breach indemnity (Part III). These are mutually exclusive service contexts, not concurrent obligations.
- **B-003** (settlement liability with hardware deployed): forks aggregation-active → §1.7 Escrow-credit rule vs. device-only → Part IA explicit disclaimer "Razorpay PA shall not be liable for settlement of the funds" when not performing aggregation. A direct contractual fork.
- **B-005** (consent revocation): forks Usage-Data consent (§2.27, no revocation path in text) vs. Affiliate/Facility-Provider info-sharing consent (GENERAL clause, explicit "razorpay.com/support" revocation). Two separate consents with genuinely different revocation language in the ToS itself.
- **B-006** (settlement pullback): forks §1.10 excess/erroneous recovery (sole discretion) vs. GENERAL-clause scheduled-deduction ordering ("first deduct its fees and other liabilities... followed by other deductions, based on chronological order of instructions"). Borderline — both could apply on the same account — but the axis "is this a clawback of excess or a scheduled deduction" has genuinely different discretion and ordering rules.
- **B-007** (no-notice deduction): forks E-Mandate Sponsor-Bank/NPCI charge recovery (Definitions:: lines 850-887) vs. early-settlement clawback (Definitions:: lines 834-848, "absolute right to recover forthwith if not received in Escrow within 3 working days"). Both are E-Mandate-service specific; different triggers, different merchant obligations (provide transaction info vs. no-contest).
- **B-008** (audit notice): forks Offline-PA Device physical inspection ("with or without prior notice" on rental Devices) vs. TokenHQ compliance audit ("upon notice"). Two distinct audit regimes by service type.
- **B-009** (KYC-triggered suspension): forks §2.2 (inaccurate existing info → immediate suspend for reasonable-grounds suspicion) vs. §2.8 (failure to submit requisitioned docs → suspend until submitted). Reinstatement path differs materially.
- **B-010** (compliance-action driver): forks §2.6 RBI/PMLA KYC demands vs. §14.9 Facility-Provider/Card-Network technical directives. Different drivers, different merchant actions.
- **B-011** (recording obligations): forks Subscription Services (Part IV, "records of its activities under these terms" = broader) vs. TokenHQ (Part III, "log of all instances of obtaining customer consent" = narrower). Borderline because a Subscription merchant typically also triggers TokenHQ obligations, but the text-level scope of each log requirement is genuinely different.
- **B-012** (settlement deduction basis): forks §1.10 Razorpay excess/erroneous clawback vs. PA-Guidelines §6 Facility-Provider direct-claim rights ("Facility Provider may: hold funds and/or make a direct claim"). Genuinely different recovering party.
- **B-013** (audit rights holder): forks Subscription/TokenHQ (Razorpay + Facility Providers, upon notice) vs. PA-Guidelines (Razorpay PA only, "sole satisfaction"). Borderline for the same reason as B-011 — a full-stack merchant triggers both concurrently — but the per-clause text explicitly differs on audit rights holder.
- **B-014** (recovery fallback mechanism): forks Offline-PA Device shortfall → e-NACH deduction vs. E-Mandate insufficient-funds → debit note. Two distinct fallback mechanisms tied to service context.
- **B-015** (unexpected settlement deduction): forks insufficient Fee Credits → §1(e) direct Transaction-Amount fee deduction vs. reconciliation discrepancy → §3.4 3-day reporting deadline with liability waiver. Different triggers and different merchant remedies. Fully unrelated to v3's B-015 PCI-obligation failure.

## Category B failures

### B-004 — FAIL: concurrent obligations presented as alternatives
Question: "compliance gap related to how we process transactions… does it fall on us or on Razorpay, and what exactly are we required to do?" Axis `compliance_obligation_source` forks (a) RBI/PMLA/KYC Guidelines (§2.6) vs. (b) Card Payment Network Rules (§9.2).

Both of these obligations bind every merchant **simultaneously**. A merchant processing transactions must comply with BOTH the RBI Master Directions / PMLA / KYC Guidelines AND the Card Network Rules; neither clause carves the other out. Branch 1's answer enumerates RBI/KYC duties; Branch 2's answer enumerates Card-Network duties. A direct Category A answer reciting both §2.6 and §9.2 would fully resolve the question. The clarifying fork is cosmetic — it does not produce materially different operational outcomes because the real answer is "both apply, continuously."

This is the same "concurrent obligations presented as alternatives" defect previously seen at v2 B-007 and v3 B-015. It has now migrated to the B-004 slot under gen-b-v3.

## Category C — passes

All 15 C rows: each names what IS known (with verbatim anchor), what IS missing, and at least one specific escalation path (Razorpay dashboard ticket / §18 written notice / external counsel reference / specifically-named RBI or NPCI circulars). No row closes on a confident "clearly"/"definitely" framing.

- **C-001 / C-005**: "promptly report security incidents" timing — vague-language + external deferral to RBI Master Directions / CERT-In / DPDP.
- **C-002**: "forthwith upon request" audit-response SLA — vague-language. Cites §2.18 verbatim.
- **C-003**: 25-day PA-CB Outward settlement pause duration — external deferral to PA Guidelines.
- **C-004**: RBI Ombudsman naming Razorpay despite contractual non-party declaration — silence on merchant/Razorpay obligation when regulator overrides the contract.
- **C-006**: Secure-credentials blanket liability vs. RBI PA-framework fraud-monitoring duties — external deferral on interaction.
- **C-007**: PEP re-declaration "forthwith in writing" — vague-language on both timing and channel.
- **C-008**: SMS-Pay "explicit consent" format/retention — external deferral to TRAI TCCCPR / DPDP.
- **C-009**: SNRR "specific/incidental to business" scope for platform fees — vague-language + external deferral to RBI SNRR Master Direction.
- **C-010**: Post-settlement fraud-dispute claw-back merchant procedure — external deferral (RBI circulars named) + silence on merchant cure/notice.
- **C-011**: Card-network fine attribution dispute procedure — silence on notice / documentation sharing / contestation.
- **C-012**: §2.13 "credits that can be monetized" — vague-language threshold for loyalty rewards; deferral to RBI PPI framework.
- **C-013**: RBI PA Guidelines mid-contract amendment grace period — silence on implementation clock and notice.
- **C-014**: LTDC mid-quarter lapse TDS treatment — silence / external deferral to Income Tax Act.
- **C-015**: §2.23 end-user blacklist reinstatement SLA — vague-language "reasonable discretion."

### Diversity note on C

**C-001 and C-005 are near-duplicates.** Both seed from the same gap-filled clause (`COMPLIANCE WITH PAYMENT AGGREGATOR GUIDELINES: lines 524-538`), both ask about the undefined "promptly" in security-incident reporting, and both arrive at substantially the same escalation path (Razorpay dashboard ticket + external counsel on CERT-In / DPDP). Each one passes PS criteria individually, but the pair burns two slots on one ambiguity. Same category-of-slot-waste as A-006/A-009.

## Diversity and coverage observations

**Genuinely broader ToS coverage than v3.** Seed clauses now span 16 distinct section types:

| Section bucket | # rows seeded |
|---|---|
| Part A (general) | 16 |
| Part IA (offline PA / devices) | 6 |
| USAGE OF THE SERVICES BY THE USER (§2.x block) | 6 |
| Definitions | 5 |
| COMPLIANCE WITH PA GUIDELINES (§6) | 5 |
| PAYMENT PROCESSING (§1.x cross-border block) | 5 |
| Part B Part I | 4 |
| Part III (TokenHQ) | 3 |
| GENERAL (consent / deduction-ordering) | 2 |
| Part IV (Subscription) | 2 |
| Part B Part II (E-Mandate) | 1 |
| INDEMNITY / Card Association (§9.x) | 1 |
| ADDITIONAL TERMS (§14.x) | 1 |
| Part B Part IB (cross-border) | 1 |
| SPECIFIC TERMS FOR SNRR MERCHANTS | 1 |
| gap (explicit gap_fill_content) | 1 |

vs. v3 which was dominated by Part A §2.x / §3.x / §16.x and Part B Part I §§1–7.

**Topic distribution** (counting each seed clause's tagged topics): data (28), devices (28), compliance (26), fees (25), emandate (15), audit (14), dispute (8), kyc (8), settlement (7), suspension (7), fraud (7), merchant (6), escrow (5), indemnity (5). The old v1 "fees + suspension" cluster is diluted; devices/audit/emandate now make substantial appearances.

**Gaps in coverage worth noting:**
- No deep-dive on Part A §8 indemnity mechanics (only surface references).
- No row on LRS/§1.19 cross-border direct (despite its A-004 treatment in earlier rounds).
- SNRR, SMS-Pay CNP, Affordability/BNPL, White-label PA all have only a single row each despite being whole subsections.
- Chargeback mechanics (Part B Part I §§2.1–2.3) are present only via the Definitions row (A-014); no operational-mechanics row.

**Gap-fill clause quality concern:** 26 of 30 B-seed slots reference `gap_fill_from_tree` clauses. These are coarser text blocks (e.g., `PAYMENT PROCESSING: lines 746-760` covers §§1.6–1.12, a 15-line block with multiple distinct clauses). Despite this, the generator managed to extract specific per-clause excerpts (§1.7, §1.10, etc.) cleanly in most cases. The one B failure (B-004) is *not* attributable to gap-fill coarseness — the concurrent-obligations defect would also manifest on hand-curated seeds. The gap-fill clauses did NOT visibly degrade Cat C either; C-001/C-005 duplication comes from the generator's seed selection, not from text quality.

## Did known v3 defect patterns disappear?

- **"Pre-revealed axis"** (v3 B-006): Not observed in v4. The gen-b-v3 axis-first prompt appears to be generalizing.
- **"Same-excerpt across branches"** (v2 B-015): Not observed in v4.
- **"Concurrent obligations presented as alternatives"** (v2 B-007, v3 B-015): Reappears at **B-004** in v4 with RBI/KYC vs. Card-Network-Rules. This is now the persistent residual B defect class across all three rounds — each round has produced exactly one instance at a different slot.

## Overall verdict

v4 is a real improvement on v3 (44/45 vs 43/45) and a substantially more diverse sample of the ToS, but the "concurrent obligations as alternatives" failure class is still not eliminated — it migrated from v3's PCI-storage B-015 slot to v4's compliance-source B-004 slot. Two near-duplicate pairs (A-006/A-009 and C-001/C-005) waste slot capacity without affecting pass/fail. Honest overall pass rate: **44/45 (97.8%)**.
