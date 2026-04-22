# Failure catalogue — auto-generated

> Three lowest-scoring items per category, with root-cause notes. Not cherry-picked.
> Each item lists the lowest-scoring dimensions and a specific rubric or code change that would catch it.

## Category A

### A-001 (composite 4.86)
**Q:** If a card association imposes a penalty on Razorpay PA due to a compliance violation attributable to our merchant account, can Razorpay PA deduct that penalty amount directly from our settlement payouts?
**A:** Yes. Under Part A §2.25, if any penalty or other liability is imposed on Razorpay PA by a Card Association due to any act or failure to act attributable to the merchant, Razorpay PA is entitled to recover such amounts by deducting the amount from the merchant's settlement amount. Razorpay PA may also initiate requisite proceedings to recover such amounts.
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §2.25']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### A-002 (composite 4.86)
**Q:** Under the Razorpay PA terms, what is the formal definition of a 'Refund' — specifically what amount is returned and to which destination?
**A:** Under the Razorpay PA terms, a 'Refund' is defined as Razorpay PA processing the merchant's request to return the Transaction Amount (or part thereof) back to the Payment Instrument that was originally used to make the payment. The destination is always the same Payment Instrument used for the original transaction — not an alternate account or instrument.
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Definitions: Refund']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### A-006 (composite 4.86)
**Q:** Under Razorpay's offline payment aggregation terms, if a merchant receives a POS device on a rental basis and the arrangement is terminated, how many days does the merchant have to surrender the device back to Razorpay PA?
**A:** Under the offline payment aggregation device terms, a merchant who received a device on a rental basis must surrender the device to Razorpay PA within not less than 3 days upon termination of the arrangement for any reason. The device remains the exclusive property of Razorpay PA, and the merchant cannot claim any right, title, interest, or lien over it during or after the tenure of the arrangement.
**Lowest dims:** `clarity.concision`=4, `grounding.factual_support`=5, `grounding.citation_relevance`=5
**Root-cause trace:** validator=True; regen_count=1; seed_clauses=['Part IA: Additional Terms For Offline Payment Aggr: lines 673-716']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category B

### B-001 (composite 4.64)
**Q:** We got a notice that Razorpay intends to act on our account unilaterally — do we have any say in this, or did we already consent to it under the terms?
**Clarifier:** Can you clarify what type of action Razorpay is taking on your account? If it involves sharing your account or transactional information with third parties or Group Entities, the answer differs from a situation where Razorpay is recovering an excess or erroneous settlement amount — because the applicable clause and your recourse options are different in each case. (axis: `settlement_action_type`)
**Lowest dims:** `clarity.concision`=3, `category_fit.category_correctness`=4, `clarity.readability`=4
**Root-cause trace:** validator=True; regen_count=1; seed_clauses=['USAGE OF THE SERVICES BY THE USER: lines 156-171', 'PAYMENT PROCESSING: lines 746-760']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### B-003 (composite 4.73)
**Q:** We're deployed with Razorpay's hardware at our retail outlets and funds from some locations aren't being settled to our account. Can Razorpay PA be held liable for the missing settlements?
**Clarifier:** Is Razorpay PA also performing payment collection and aggregation services at those locations, or did Razorpay PA only supply the devices without providing aggregation/settlement services? If aggregation services are active, Razorpay PA's settlement liability is governed by the Payment Processing terms; if only devices were provided with no aggregation services, Razorpay PA has explicitly disclaimed any settlement liability. (axis: `service_scope`)
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part IA: Additional Terms For Offline Payment Aggr: lines 633-671', 'PAYMENT PROCESSING: lines 746-760']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### B-007 (composite 4.73)
**Q:** Razorpay has started deducting amounts from our settlement payouts without any prior notice. What is the contractual basis for this and what obligations does it create for us?
**Clarifier:** What is the recovery trigger type — is Razorpay recovering amounts because of a charge, penalty, or fine levied by the Sponsor Bank, NPCI, or a governmental authority (e.g., related to disputed or fraudulent transactions), or is it recovering funds that were settled to you earlier than the agreed timeline but were not subsequently received in the Escrow Account within three working days? The answer differs materially: the first scenario invokes your liability for Sponsor Bank charges and fraud-related penalties with an obligation to provide transaction information; the second invokes Razorpay's absolute right to claw back early-settled funds under a strict timing rule. (axis: `recovery_trigger_type`)
**Lowest dims:** `clarity.concision`=3, `clarity.readability`=4, `grounding.factual_support`=5
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Definitions:: lines 850-887', 'Definitions:: lines 834-848']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

## Category C

### C-004 (composite 4.5)
**Q:** A customer filed a complaint with the RBI Ombudsman naming Razorpay as a party because Razorpay's name appeared on the payment confirmation page. Clause 14.5 says Razorpay can't be made a party to product disputes — but the regulator has already named them. What are our obligations here, and does Razorpay have any duty to assist us in responding to the ombudsman?
**A:** Clause 14.5 establishes that Razorpay PA and Facility Providers 'shall not be liable for any risk/dispute/issue associated with product(s)/services provided by You, and in no event shall be made a party to any such risk/dispute/issue' — but this is a contractual allocation between you and Razorpay, not a directive binding on a regulator. The ToS does not define what the merchant must do when the RBI Ombudsman or NPCI independently names Razorpay in a grievance proceeding, nor does it specify any cooperation, indemnification, or notification obligation on either side in that scenario. There is no clause that addresses whether Razorpay is obligated to provide transaction records, respond to the regulator on your behalf, or coordinate a joint response. Given this gap, you should immediately raise a formal support ticket via the Razorpay merchant dashboard (Compliance/Legal category) to notify Razorpay of the ombudsman complaint and request their position in writing; simultaneously, review the applicable RBI Ombudsman Scheme for Payment System Participants (2019) to understand your own direct obligations as the merchant of record. External legal counsel familiar with RBI grievance procedures should be engaged to assess whether the contractual non-party clause has any practical force against a regulatory body.
**Lowest dims:** `clarity.concision`=3, `grounding.factual_support`=4, `grounding.citation_relevance`=4
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['gap: lines 273-273']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### C-006 (composite 4.5)
**Q:** Our API credentials were compromised by a rogue contractor who pushed through ~₹8L in fraudulent payouts before we caught it. §2.1 says we're fully responsible for anyone using our Secure Credentials — but does RBI's PA framework impose any fraud-monitoring or reversal obligation on Razorpay that would limit our absolute liability here, or are we truly on the hook for the entire amount?
**A:** §2.1 unambiguously assigns full liability to the merchant for all activities conducted under their Secure Credentials, including unauthorized access by third parties, and states that Razorpay PA shall not be liable for any such actions. However, the clause invokes 'Applicable Laws' without defining how RBI's Payment Aggregator guidelines (RBI circular DPSS.CO.PD No.1810/02.14.008/2019-20, March 2020) interact with this blanket merchant liability — those guidelines impose specific fraud monitoring, transaction velocity, and grievance redressal obligations on Razorpay as a licensed PA, which could create regulatory duties that qualify the ToS's absolute liability assignment. The ToS does not specify whether Razorpay's own PA-license obligations under RBI (e.g., mandatory fraud reporting, escrow account rules, or customer/merchant grievance timelines) create any shared responsibility or reversal pathway in a credential-compromise scenario. Given this gap, you should: (1) immediately raise a formal dispute ticket via the Razorpay merchant dashboard citing the fraud incident and requesting their PA-license grievance process; (2) send written notice under §18 of the ToS preserving your rights; and (3) engage external legal counsel with RBI PA regulatory expertise to assess whether Razorpay's obligations under the PA circular limit the enforceability of §2.1's absolute liability clause in your jurisdiction.
**Lowest dims:** `clarity.concision`=3, `grounding.factual_support`=4, `clarity.readability`=4
**Flags:** ungrounded_claim
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['Part A §2.1']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.

### C-001 (composite 4.6)
**Q:** The ToS says we must 'promptly report' security incidents to Razorpay's grievances URL — but what does 'promptly' actually mean in practice? Is there a specific hour or day window we need to hit, and does Razorpay have its own internal SLA on top of whatever RBI mandates?
**A:** The clause requires merchants to 'promptly report security incidents or breaches involving customer data to https://razorpay.com/grievances/' and to comply with 'Applicable Laws,' but the ToS does not define a numeric timeframe for what 'promptly' means in this context. The RBI Master Directions on Payment Aggregators (October 2020 and subsequent circulars) do impose specific incident reporting obligations on regulated entities, but the ToS only defers to those external rules without reproducing or summarising the applicable windows. It is therefore unclear whether Razorpay's own internal policy imposes a stricter timeline (e.g., 2-hour, 6-hour, or 24-hour notification) on top of any RBI-mandated deadline, or whether the merchant's obligation runs solely to the regulatory floor. To get a definitive answer, raise a formal written inquiry via a Razorpay dashboard support ticket requesting Razorpay PA's internal breach-notification SLA in writing, and separately have external legal counsel review the current RBI PA Master Directions and CERT-In breach notification rules (which impose a 6-hour window for certain incidents) to ensure you are meeting the strictest applicable standard.
**Lowest dims:** `clarity.concision`=3, `grounding.factual_support`=4, `clarity.readability`=4
**Root-cause trace:** validator=True; regen_count=0; seed_clauses=['COMPLIANCE WITH PAYMENT AGGREGATOR GUIDELINES: lines 524-538']
**Mitigation proposal:** long answers with redundant framing. Prompt fix: `prompts/gen_*_v1.md` — add a `< 150 words` cap on answers and `< 80 words` on clarifiers. Post-processing fix: validator could add a `word_count` structural check.
