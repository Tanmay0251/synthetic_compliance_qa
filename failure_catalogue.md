# Failure catalogue — auto-generated

> Three lowest-scoring items per category, with root-cause notes. Not cherry-picked.
> Each item lists the lowest-scoring dimensions and a specific rubric or code change that would catch it.

## Category A

### A-002 (composite 4.86)
**Q:** We're building an in-person payments flow using Razorpay's card terminals where the card and the POS device are both physically present at checkout. Which section of Razorpay's Terms of Use actually governs this setup, and does it replace the general terms or sit on top of them?
**A:** Your in-person card-present flow falls under Part IA of Razorpay's Terms, which applies to use of Devices and offline payment aggregation — defined as 'facilitating transactions where both the acceptance device and payment instrument are physically present in close proximity while making the transaction.' Part IA does not replace the general terms; it is supplementary. The clause states that Part IA 'shall be read in conjunction with and is supplementary to the Part A (General Terms and Conditions) and Part I (Payment Aggregation Services)' and that 'All terms and conditions detailed in Part A and Part I remain in full force and effect.' Part IA provisions only take precedence in the narrow case of an irreconcilable conflict, and even then 'only to the extent necessary to govern the specific requirements of offline payment aggregation.'
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part IA §1.1']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### A-006 (composite 4.86)
**Q:** We just got notified that Razorpay deducted some money from our next settlement payout to recover a charge that was debited from our account by one of their facility providers. Is this something they're allowed to do unilaterally, or do they need our approval first?
**A:** Yes, Razorpay is contractually entitled to do this without needing your prior approval. Under Part B Part I §1(f), you agreed that Razorpay PA is entitled, at its sole discretion, to recover any amounts charged to Razorpay PA or debited by Facility Providers from your accounts by deducting from (i) the Transaction Amount to be settled to you and/or (ii) any of your other funds held by Razorpay PA. Additionally, if that set-off doesn't fully cover what you owe, you are required to pay Razorpay PA a sum equal to any shortfall.
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §1(f)']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### A-008 (composite 4.86)
**Q:** We're integrating Razorpay's Optimizer to route payments across multiple gateways. Our legal team wants to know: is Razorpay acting as a payment service provider for these routed transactions, or is their role something different? And who's on the hook if one of those gateways raises a dispute against us?
**A:** For Optimizer Services, Razorpay PA's role is strictly that of a SaaS provider — not a payment service provider. The clause explicitly states that 'Razorpay PA's role will strictly be that of a SaaS provider and will not be that of a payment service provider.' On the liability question, if any payment gateway or payment aggregator raises a dispute or claim related to Optimizer Services due to your actions or omissions, you are responsible: you must 'indemnify and hold Razorpay PA, its directors, managers, officers, employees and agents harmless from and against all losses arising from claims, demands, actions or other proceedings as a result of disputes or claims raised by any payment gateway / payment aggregator in relation to Optimizer Services.'
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §7.1']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category B

### B-015 (composite 4.27)
**Q:** If I issue a refund to a customer, do I still have to pay Razorpay's fees on that transaction?
**Clarifier:** To give you a precise answer, could you clarify which aspect of the refund_fee_obligation you are asking about — specifically, are you asking (A) whether you have the discretion to issue the refund in the first place (which depends on Escrow fund availability), or (B) whether Razorpay's processing fees remain payable on a transaction after you have already decided to refund it? The answer differs significantly: the first concerns your right to refund, while the second concerns your ongoing fee liability regardless of that refund. (axis: `refund_fee_obligation`)
**Lowest dims:** `category_fit.category_correctness`=2, `clarity.concision`=3, `clarifier_quality.names_axis`=3
**Flags:** axis_not_load_bearing, wrong_category
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §3.1', 'Part B Part I §3.4']
**Mitigation proposal:** generator B over-produces borderline questions that could also be answered as Category A (the axis exists but isn't load-bearing). Code fix: tighten `pipeline/generators/b.py` `_select_pairs` to require that the two clauses in a pair disagree on a numeric/temporal dimension (not just share a topic). Rubric fix: add a `axis_is_load_bearing` gate to the validator that fails if a single clause can answer the question directly.

### B-013 (composite 4.36)
**Q:** If a payment is refunded back to the customer, do I still owe Razorpay any fees on that transaction?
**Clarifier:** To give you an accurate answer, I need to know the refund_initiating_party — specifically, was the refund initiated by **you (the merchant)** voluntarily returning funds to your customer, or was it initiated by **Razorpay PA** acting on its own discretion or under a regulatory mandate and refunding the amount back to the source account? The answer changes significantly depending on who triggered the refund: if you initiated the refund, fee obligations under the fee clause apply; if Razorpay PA initiated the refund due to an internal decision or regulatory mandate, the basis and context of the refund is governed by a different clause and the fee obligation may be disputed. (axis: `refund_initiating_party`)
**Lowest dims:** `category_fit.category_correctness`=3, `clarity.concision`=3, `grounding.factual_support`=4
**Flags:** borderline
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §1(h)', 'Part B Part I §3.4']
**Mitigation proposal:** generator B over-produces borderline questions that could also be answered as Category A (the axis exists but isn't load-bearing). Code fix: tighten `pipeline/generators/b.py` `_select_pairs` to require that the two clauses in a pair disagree on a numeric/temporal dimension (not just share a topic). Rubric fix: add a `axis_is_load_bearing` gate to the validator that fails if a single clause can answer the question directly.

### B-002 (composite 4.45)
**Q:** If Razorpay PA causes a loss related to payment processing, how are fees calculated for determining my compensation or liability cap?
**Clarifier:** To give you an accurate answer, I need to know your fee_payment_method: are you paying fees through purchased Fee Credits (where fees are deducted from a pre-loaded credit balance), or are fees deducted directly from each Transaction Amount? This matters because the basis for calculating 'one month fees paid by You' — which sets the liability cap — could differ depending on whether your fees are tracked as deductions from Fee Credits or from transaction settlements. (axis: `fee_payment_method`)
**Lowest dims:** `clarity.concision`=3, `citation_accuracy.excerpt_is_verbatim`=3, `category_fit.category_correctness`=4
**Flags:** non_contiguous_excerpt, paraphrase_not_verbatim
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §7.2', 'Part B Part I §1(e)']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category C

### C-008 (composite 4.7)
**Q:** If a fraudulent transaction is discovered after the settlement amount has already been paid out to my account, how exactly will the dispute be resolved — and what does that mean for how much money I might have to return, and within what timeframe?
**A:** This is a genuinely uncertain area where the Razorpay Terms of Service defer almost entirely to external regulation rather than spelling out the mechanics themselves.

What the ToS does say: Part B Part I §4.2 states that if a fraudulent transaction has already been settled to you, any resulting dispute 'shall be resolved in accordance with the RBI's notification DBR.No.Leg.BC.78/09.07.005/2017-18, dated July 6, 2017 read with RBI's notification DBOD. LEG. BC 86/09.07.007/2001-02 dated April 8, 2002, and other notifications, circulars and guidelines issued by the RBI in this regard from time to time.' So there is a clear pointer to an external regulatory framework.

What the ToS does not say: The clause does not define the specific procedural steps Razorpay will follow after flagging a post-settlement fraud dispute — for example, whether funds will be immediately debited from your account, held in escrow, or recovered through future settlements. It does not specify the timeline within which you must respond or contest a fraud allegation, nor does it describe what evidence you may submit in your defence. It does not clarify how liability is apportioned between you, the payment gateway, and the acquiring/issuing bank. The referenced RBI circulars themselves contain nuanced conditions (e.g., distinguishing merchant negligence from third-party fraud, and the 'zero liability' vs. 'limited liability' framework for cardholders), and the ToS provides no guidance on how those conditions map onto a merchant's specific obligations. Additionally, the phrase 'other notifications, circulars and guidelines issued by the RBI in this regard from time to time' means the applicable rules could have changed since the ToS was drafted.

Given this external deferral, it would not be appropriate to assume a particular outcome — whether that is full recovery of the settled amount, partial liability, or no clawback at all.

Recommended escalation paths:
1. **Razorpay Merchant Support** — Request a written explanation of their internal post-settlement fraud dispute process, including timelines and recovery mechanics, before any debit occurs.
2. **Legal counsel** familiar with RBI payment system regulations — to interpret the cited circulars (DBR.No.Leg.BC.78/09.07.005/2017-18 and DBOD.LEG.BC 86/09.07.007/2001-02) in the context of your specific transaction type and merchant category.
3. **RBI's Banking Ombudsman or direct RBI guidance** — if you believe the process being applied to you is inconsistent with the current regulatory framework.

Do not assume the matter is resolved in your favour or against you until you have obtained written clarification from Razorpay and, if necessary, independent legal advice.
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §4.2']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### C-011 (composite 4.7)
**Q:** If a fraudulent transaction on my Razorpay integration results in a chargeback, exactly which rules and timelines apply — and does RBI's chargeback framework or NPCI's dispute resolution mechanism take precedence over what Razorpay's Terms say?
**A:** This is a genuinely ambiguous area where Razorpay's Terms of Service provide only a partial answer, and the full picture requires looking beyond the document itself.

**What the ToS does say:** Part B Part I §4.3 states that 'if the Fraudulent Transaction results in a Chargeback, then such Chargeback shall be resolved in accordance with the provisions set out in the Terms.' This confirms that a chargeback pathway exists for fraudulent transactions and that the Terms govern it — but only to the extent that the Terms themselves define the process.

**What the ToS does not say:** The clause does not specify: (a) which external regulatory framework — RBI's chargeback circulars, NPCI's dispute resolution rules for UPI/RuPay, card network rules (Visa/Mastercard), or applicable state/central law — controls in the event of a conflict or gap; (b) the precise timelines a merchant must follow to raise or respond to a chargeback; (c) how liability is allocated between Razorpay, the acquiring bank, and the merchant when fraud is alleged but not yet proven; and (d) whether RBI's Zero Liability / Limited Liability framework for unauthorised transactions overrides any contractual term in the ToS.

The clause effectively defers resolution to 'the Terms,' but the Terms themselves appear to defer — at least implicitly — to external regulation without drawing clear boundaries between what the contract controls and what RBI/NPCI mandates control. This creates a regulatory gap that the document alone cannot resolve.

**Recommended escalation path:**
1. **Razorpay Merchant Support** — Request a written clarification of the specific chargeback procedure, timelines, and liability allocation applicable to your payment method (card, UPI, netbanking).
2. **Legal Counsel** — Engage a payments-law specialist to assess how RBI's Master Direction on Prepaid Payment Instruments, the RBI circular on customer protection in unauthorised electronic transactions (DBR.No.Leg.BC.78/09.07.005/2017-18), and relevant NPCI operating guidelines interact with your merchant agreement.
3. **RBI / NPCI Guidance** — If the dispute involves a systemic or regulatory question, the RBI Ombudsman for Digital Transactions or NPCI's dispute portal may provide authoritative direction.

No confident resolution can be offered here without knowing your specific payment instrument, the applicable card/network scheme rules, and how Razorpay's internal chargeback policy operationalises §4.3.
**Lowest dims:** `grounding.factual_support`=4, `grounding.citation_relevance`=4, `clarity.concision`=4
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §4.3']
**Mitigation proposal:** a numeric or temporal claim in the answer isn't backed by any cited clause. The deterministic grounding check only matches literal day/percentage patterns; this is a miss where the model paraphrased the number into different units. Code fix: extend `_check_grounding` in `pipeline/validator.py` to normalise numeric units before matching.

### C-004 (composite 4.8)
**Q:** If a fraudulent transaction on my Razorpay integration results in a chargeback, exactly which rules govern the resolution process — and what happens if RBI or NPCI guidelines conflict with what Razorpay's Terms say?
**A:** This is a genuinely ambiguous area where Razorpay's Terms of Service provide only a partial answer, and the full picture requires consulting external sources.

**What the ToS does say:** Part B Part I §4.3 states that if a fraudulent transaction results in a chargeback, 'such Chargeback shall be resolved in accordance with the provisions set out in the Terms.' This tells you that a chargeback process exists and that Razorpay's own Terms are the stated reference point for resolution.

**What the ToS does not say:** The clause does not define which specific provisions within 'the Terms' govern chargeback timelines, merchant liability caps, evidence submission windows, or dispute escalation procedures. More critically, the Terms do not explicitly delineate how — or whether — RBI's chargeback and dispute resolution guidelines (such as those under the Payment and Settlement Systems Act, 2007, or RBI's Master Directions on Prepaid Payment Instruments) or NPCI's network-level chargeback rules (which vary by instrument: UPI, RuPay, IMPS, etc.) interact with or override Razorpay's internal provisions. There is no stated hierarchy of authority when a conflict arises between Razorpay's Terms and these external regulatory frameworks.

**Why this matters practically:** RBI and NPCI each publish their own chargeback timelines and liability rules, which card networks (Visa, Mastercard) also layer on top of. If Razorpay's Terms set a shorter dispute window than RBI mandates, or if NPCI rules assign liability differently than Razorpay's Terms suggest, a merchant could unknowingly waive rights or face unexpected financial exposure.

**Recommended escalation path:**
1. **Razorpay Merchant Support** — Request a written clarification on which specific clauses govern chargeback resolution for your payment instruments, and ask how external regulatory rules are incorporated.
2. **Legal counsel** familiar with Indian payment regulations — To assess whether RBI's Master Directions or NPCI operating circulars create enforceable rights that supersede any contractual terms.
3. **RBI / NPCI directly** — RBI's consumer grievance portal and NPCI's published operating guidelines can clarify the regulatory floor for chargeback rights that no private contract can contractually waive.

Given the external deferral without defined boundaries, no confident resolution can be offered here without those additional clarifications.
**Lowest dims:** `grounding.factual_support`=4, `clarity.concision`=4, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §4.3']
**Mitigation proposal:** a numeric or temporal claim in the answer isn't backed by any cited clause. The deterministic grounding check only matches literal day/percentage patterns; this is a miss where the model paraphrased the number into different units. Code fix: extend `_check_grounding` in `pipeline/validator.py` to normalise numeric units before matching.
