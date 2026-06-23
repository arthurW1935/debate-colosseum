# NovaSkin — Technology Roadmap & Engineering Hiring Plan FY25–FY26
*Prepared by: Sneha Rajan (COO) & Tech Lead Kiran Deshpande*  
*Date: February 2025 | Status: Pending CEO + CFO Approval*

---

## 1. Current State of Technology

### Team Composition (as of Feb 2025)

| Role | Name | Tenure |
|------|------|--------|
| Tech Lead / Full-stack | Kiran Deshpande | 2.5 years |
| Backend Engineer (Sr.) | Rohan Pillai | 1.5 years |
| Backend Engineer (Jr.) | Tanvi Shah | 8 months |
| Frontend Engineer | Aarav Kumar | 1 year |
| Frontend Engineer (Jr.) | Megha Iyer | 4 months |
| Data Analyst (non-engineering) | Divya Krishnan | 2 years |
| Data Analyst (non-engineering) | Ankit Joshi | 1 year |
| DevOps (contractor) | Pratik Nair | 18 months |

**Total engineering headcount:** 8 (6 FTE engineers, 2 analysts, 1 contractor)

### Current Tech Stack Assessment

| System | Technology | Status | Pain Points |
|--------|-----------|--------|------------|
| E-commerce storefront | Shopify Plus | Stable | Limited customization, expensive app ecosystem |
| CRM | Klaviyo + MoEngage | Good | Duplication; some data sync issues |
| Analytics | GA4 + BigQuery | Needs improvement | BigQuery pipeline has 3–4 hour lag; no real-time |
| Customer support | Freshdesk | Adequate | Not integrated with order management |
| ERP | Zoho Books | Below par | No API integration with Shopify; manual reconciliation weekly |
| Personalization | None | Gap | Identified as #1 revenue opportunity |
| Mobile app | None | Gap | 68% of website traffic is mobile; app conversion is 40–50% better for repeat purchasers |
| Subscription management | Recharge (Shopify) | Partial | Subscription penetration only 4.2%; industry best is 15–18% |
| Loyalty program | Custom-built (fragile) | At risk | Built by a contractor who left; 2 bugs in last quarter |

---

## 2. The Case FOR Hiring 10 Engineers Now

### 2.1 Identified Revenue-Impacting Tech Gaps

The COO and Tech Lead have identified five technology gaps that are measurably limiting revenue:

**Gap 1: No Mobile App (Estimated revenue impact: INR 2.8–4.2 Cr/year)**
- 68% of NovaSkin's traffic is mobile; mobile web conversion is 2.4% vs. 3.1% desktop
- Industry data: D2C brands with dedicated apps see 38–52% higher LTV from app users (Clevertap benchmark)
- Building a native React Native app is estimated at 4 months with 2 dedicated engineers
- Ongoing app maintenance requires at least 1 mobile engineer permanently

**Gap 2: No Personalization Engine (Estimated revenue impact: INR 1.8–2.6 Cr/year)**
- NovaSkin sends the same product recommendations to all customers regardless of skin type, purchase history, or browsing behavior
- Dot & Key and Foxtale both have ML-driven recommendation engines
- A/B tested personalization typically drives 12–18% uplift in AOV
- Requires 1 ML engineer + 1 data engineer to build and maintain

**Gap 3: Real-time Inventory Visibility (Estimated operational impact: INR 60–80L/year in stockout losses)**
- Current BigQuery pipeline has 3–4 hour lag; marketing campaigns continue running to out-of-stock pages
- 3 major stockout events in FY24 (Niacinamide Serum, SPF 50, Vitamin C Serum) — estimated combined lost revenue INR 42L
- Fixing this requires a data engineer to rebuild the pipeline on Kafka/Pub-Sub with near-real-time sync

**Gap 4: Subscription Rate below Potential (Estimated opportunity: INR 1.2–1.9 Cr/year incremental)**
- Current subscription penetration: 4.2% of revenue
- Industry average for comparable brands: 14–18%
- Primary blocker: poor UX in subscription management + no "subscribe & save" incentive logic
- Requires 1 backend engineer + 1 frontend engineer for 3-month project

**Gap 5: Customer 360 / Data Unification (Estimated opportunity: compound effect on CAC)**
- Customer data is fragmented across Shopify, Klaviyo, Freshdesk, and MoEngage with no unified ID
- Results in duplicate marketing spend, poor suppression, and inability to properly attribute LTV by channel
- A proper Customer Data Platform (CDP) or custom data unification layer requires 1 data engineer for 4 months + ongoing maintenance

**Total estimated annual revenue opportunity from fixing all 5 gaps: INR 6.4–8.7 Cr**

### 2.2 Risk of Not Hiring

1. **Technical debt accumulation:** Kiran Deshpande (Tech Lead) spends 40% of his time on maintenance and firefighting rather than product development — his assessment
2. **Talent risk:** Two junior engineers (Tanvi Shah, Megha Iyer) have received recruiter approaches; without a visible tech growth roadmap, attrition risk is high in next 6 months
3. **Series B signaling:** Series B investors in D2C consistently look at tech maturity. A "we have 6 engineers" story is harder to sell than "we built our own personalization engine and app"
4. **Competitor gap widening:** Foxtale (smaller revenue than NovaSkin) launched a mobile app in Q3 FY24 and reports 22% of revenue now through app — NovaSkin is losing ground on repeat purchase experience

---

## 3. The Case AGAINST Hiring 10 Engineers Now

### 3.1 Financial Impact

As modeled in the financial projections document:
- Adding 10 engineers costs approximately **INR 3.15 Cr/year** in salaries alone
- One-time recruitment + onboarding cost: **INR 34L**
- NovaSkin's current EBITDA: **INR 2.3 Cr** (FY25 projection)
- **Net effect: NovaSkin goes EBITDA-negative by approximately INR 0.85 Cr**
- This **breaches the EBITDA ≥ 0 covenant** on the Trifecta Capital bridge loan

This is not a modeled risk — it is a near-certainty at current revenue levels.

### 3.2 Hiring Capacity

NovaSkin has no dedicated HR or recruiting function. Hiring 10 engineers requires:
- Kiran Deshpande spending ~50% of his time for 4–5 months on interviews and onboarding
- Expanding office space (current Bengaluru office is at 85% capacity)
- This effectively halts current engineering velocity during the hiring period

### 3.3 Management Overhead

Going from 6 to 16 engineers requires an Engineering Manager — a hire NovaSkin doesn't currently have. Without an EM:
- Kiran Deshpande becomes a manager by default, losing his technical contribution
- Communication overhead increases non-linearly (Brooks's Law applies)
- Risk of poor onboarding for junior engineers in a fast-moving environment

### 3.4 Revenue Lags Hiring by 12–18 Months

The revenue impact of a personalization engine, mobile app, or CDP does not arrive immediately:
- 3–4 months to hire and onboard
- 3–4 months to build the first version
- 2–3 months to instrument, test, and iterate
- **Total time to revenue impact: 8–11 months minimum**

If NovaSkin's Series B is delayed or the market softens, committing INR 3.15 Cr/year before seeing revenue benefits from the investment creates a dangerous cash position.

---

## 4. Alternative: Phased Hiring Plan

The COO proposes a **phased alternative** to the 10-engineer plan:

### Phase 1 (FY25 Q1–Q2): Hire 3 Critical Roles — INR 1.0 Cr/year
- 1× Senior Backend Engineer (subscription + loyalty)
- 1× Data Engineer (real-time pipeline + CDP foundation)
- 1× Engineering Manager (bring Kiran back to IC work)

**EBITDA impact:** -INR 1.0 Cr → EBITDA goes from 2.3 to 1.3 Cr (still positive, no covenant breach)

### Phase 2 (FY25 Q3–Q4, post-Series B close): Hire 4 more — INR 1.4 Cr/year
- 2× Mobile engineers (React Native app)
- 1× ML / Personalization Engineer
- 1× Frontend Engineer (app + web)

**Trigger:** Series B cash in hand. EBITDA impact buffered by Series B proceeds.

### Phase 3 (FY26 Q1–Q2): Hire 3 more — INR 1.0 Cr/year
- 1× DevOps / Platform Engineer (convert contractor to FTE)
- 1× Senior Backend Engineer (scalability)
- 1× Data Analyst upgrade to Data Engineer

**Trigger:** Mobile app and personalization showing measurable revenue impact.

**Phased plan total cost:** Same INR 3.15 Cr/year steady-state but distributed across 15 months rather than hitting in month 1.

---

## 5. Priority Project Roadmap (If Hiring Approved)

| Project | Priority | Eng Resources | Timeline | Est. Revenue Impact |
|---------|----------|---------------|----------|---------------------|
| Subscription UX overhaul | P0 | 1 BE + 1 FE | 10 weeks | INR 1.2–1.9 Cr/year |
| Real-time inventory pipeline | P0 | 1 DE | 8 weeks | INR 60–80L/year |
| Customer data unification | P1 | 1 DE | 16 weeks | CAC reduction ~8% |
| Mobile app (iOS + Android) | P1 | 2 Mobile | 20 weeks | INR 2.8–4.2 Cr/year |
| Personalization engine v1 | P2 | 1 ML + 1 BE | 24 weeks | INR 1.8–2.6 Cr/year |
| Freshdesk ↔ Shopify integration | P2 | 1 BE | 6 weeks | CSAT improvement |
| Zoho Books API integration | P3 | 1 BE | 8 weeks | 3 days/month saved |

---

## 6. Benchmarks: Engineering Team Size vs. Revenue

| Company | Revenue (FY24) | Eng Team Size | Eng Cost % of Revenue |
|---------|----------------|---------------|----------------------|
| NovaSkin (current) | INR 31 Cr | 6 engineers | ~5.4% |
| NovaSkin (10 hire plan) | INR 36 Cr (proj.) | 16 engineers | ~11.8% |
| Foxtale | ~INR 45 Cr | ~14 engineers | ~9.2% |
| Dot & Key | ~INR 120 Cr | ~28 engineers | ~7.0% |
| Minimalist | ~INR 300 Cr | ~40 engineers | ~4.0% |

*At INR 36 Cr revenue, 16 engineers would put NovaSkin at 11.8% of revenue in engineering costs — significantly above comparable companies at similar revenue stages.*

---

## 7. Recommendation

The COO and Tech Lead recommend the **Phased Hiring Plan** (Section 4) rather than the immediate 10-engineer hire.

The 10-engineer plan is the right destination — NovaSkin genuinely needs this team by FY26 to compete effectively. But executing it before Series B close creates an unacceptable EBITDA covenant breach and concentrates hiring/onboarding risk in a 3-month window.

The phased plan delivers the same team by Month 15 with significantly lower financial and operational risk.

**Decision required from CEO + CFO by March 15, 2025.**

---

*Prepared by: Sneha Rajan (COO) | Kiran Deshpande (Tech Lead)*  
*For CEO + CFO review only*
