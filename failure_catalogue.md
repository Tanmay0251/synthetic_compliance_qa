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

### A-007 (composite 4.86)
**Q:** We're integrating Razorpay's Optimizer to route payments across multiple gateways. Our legal team wants to know: is Razorpay acting as a payment service provider for these routed transactions, or is their role something different? And who's on the hook if one of those gateways raises a dispute against us?
**A:** For Optimizer Services, Razorpay PA's role is strictly that of a SaaS provider — not a payment service provider. The clause explicitly states that 'Razorpay PA's role will strictly be that of a SaaS provider and will not be that of a payment service provider.' On the liability question, if any payment gateway or payment aggregator raises a dispute or claim related to Optimizer Services due to your actions or omissions, you are responsible: you must 'indemnify and hold Razorpay PA, its directors, managers, officers, employees and agents harmless from and against all losses arising from claims, demands, actions or other proceedings as a result of disputes or claims raised by any payment gateway / payment aggregator in relation to Optimizer Services.'
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part B Part I §7.1']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category B

### B-001 (composite 4.64)
**Q:** We have a situation where funds need to be refunded — can Razorpay handle the refund, or is that entirely on us?
**Clarifier:** Can you clarify the refund scenario type? Is this a customer requesting a refund for a product or service your business sold (in which case Razorpay has no responsibility and the obligation falls entirely on you), or is this Razorpay determining it cannot settle funds held in escrow — for example due to a regulatory mandate — and returning them to the source account (in which case Razorpay has the right to act unilaterally after giving you prior notice)? (axis: `refund_scenario_type`)
**Lowest dims:** `clarity.concision`=2, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §2.9', 'Part B Part I §1(h)']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### B-002 (composite 4.73)
**Q:** We just got flagged by Razorpay and they're threatening to suspend our payment services over a KYC issue. What's the worst-case outcome here and can we recover from it?
**Clarifier:** Is the KYC issue about information you already submitted being found inaccurate or incomplete, or is it about Razorpay requesting additional KYC documents that you haven't submitted yet? If it's the former (inaccurate existing info), Razorpay can immediately suspend and also terminate your account entirely; if it's the latter (non-submission of newly requested docs), suspension and settlement stoppage apply but the relationship can be restored once you submit the documents to their satisfaction. (axis: `kyc_issue_type`)
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §2.2', 'Part A §2.8']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### B-003 (composite 4.73)
**Q:** We just got a notice that our Razorpay fees are going up. Do we have any option to push back or avoid the increase, or are we just obligated to pay it?
**Clarifier:** What is the trigger for the fee increase — is it a statutory tax change (e.g., a GST rate revision), or is it Razorpay's own pricing decision on a service or value-added feature you're using? If it's a statutory tax change, you have no opt-out and must bear it automatically; if it's a Razorpay pricing decision on a service, your continued use constitutes consent but you could avoid the fee by not using that service. (axis: `fee_increase_trigger`)
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §3.2', 'Part A §14.3']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category C

### C-014 (composite 4.6)
**Q:** We updated our GST registration number after Razorpay had already generated invoices for that billing period with the old GSTIN. Is Razorpay contractually obligated to issue amended invoices or credit notes, and will they refile the GST returns to correct the earlier ones?
**A:** Part A §3.7 places the obligation to update the GST number squarely on the merchant *before* invoice generation, and states Razorpay will file returns 'as per the statutory timelines' based on the information you provide — but the clause is entirely silent on what happens after an invoice has already been raised with incorrect or outdated GSTIN details. The ToS does not define whether Razorpay will issue a credit note, raise a revised invoice, or file an amended GSTR-1, all of which are procedures governed externally by CGST Act §34 and GST amendment return rules rather than by this agreement. The clause's only post-error mechanism is Razorpay's right to recover liabilities from you — it creates no corresponding affirmative obligation on Razorpay to remediate already-filed returns. Given this gap, you should raise a formal dashboard support ticket with Razorpay's GST/finance team requesting a written confirmation of their amendment and credit-note policy, and simultaneously engage external GST counsel to assess your own rectification obligations under CGST rules so you are not exposed to input tax credit denial on your buyers' end.
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `ambiguity_framing.names_silence_type`=4
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §3.7']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

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

### C-012 (composite 4.7)
**Q:** Our escrow credit from the acquiring bank sometimes arrives at Razorpay in two partial batches for a single settlement cycle — does the 5-day domestic settlement clock start from the first partial credit or only once the full Transaction Amount is received in the Escrow Account?
**A:** The clause states that the 5-day domestic settlement timeline runs 'from the date of receipt of Transaction Amount in the Escrow Account,' and that settlement is 'subject to credit to / receipt of funds by Razorpay PA in the Escrow Account from our Facility Providers.' This anchors the clock to Escrow Account receipt, but the ToS does not define what constitutes 'receipt' when funds arrive in multiple partial tranches for a single transaction or batch — specifically, whether the clock starts on first partial credit or only upon full receipt. The Payment Aggregator Guidelines issued by RBI are referenced as the governing standard for these timelines, but the ToS does not reproduce or summarise those rules, leaving the partial-credit scenario unresolved from the document alone. To get a binding interpretation, raise a formal written support ticket via the Razorpay Dashboard (Disputes & Settlement section) requesting clarification on partial-credit escrow receipt treatment, and separately have legal counsel review the RBI Payment Aggregator Guidelines (RBI/2020-21/254 DPSS.CO.PD No.1810/02.14.008/2020-21 and any subsequent circulars) to confirm whether those regulations specify a trigger event for the settlement clock in partial-funding scenarios.
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=1; seed_clauses=['Part B Part I §1.1']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.
