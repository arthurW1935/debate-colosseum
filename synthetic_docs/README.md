# NovaSkin — Synthetic RAG Document Index
*For use in Debate Colosseum eval scenarios*

---

## Company

**NovaSkin Brands Pvt. Ltd.** — A Bengaluru-based D2C skincare brand, founded 2020.  
Mid-premium positioning (INR 600–2,800/SKU). FY24 revenue: INR 31 Cr. Series B fundraise active.

---

## Documents

| File | Contents | Primary Use |
|------|---------|-------------|
| `00_company_profile.md` | Full company overview: team, funding, revenue, product portfolio, competitive landscape | All agents — baseline context |
| `01_financial_projections_fy25_fy27.md` | 3-year P&L model, unit economics, cash flow, EU cost model, engineer hiring cost model | Finance agent (primary), Risk agent |
| `02_eu_market_expansion_research.md` | EU market sizing, regulatory requirements, GTM strategy, competitive analysis, 18-month EU financial model | Growth + Risk agents (Scenario 1) |
| `03_competitor_acquisition_analysis.md` | GlowLab India acquisition target analysis, valuation, due diligence findings, strategic cases for/against | Finance + Risk agents (Scenario 2) |
| `04_tech_roadmap_and_hiring_plan.md` | Engineering team state, 5 tech gaps, 10-hire plan vs phased plan, revenue impact estimates | Growth + Finance agents (Scenario 3) |
| `05_burn_rate_and_cash_management.md` | Monthly burn, fixed vs variable costs, cash position, covenant details, seasonal pattern | Finance + Risk agents (Scenario 3) |
| `06_market_research_consumer_insights.md` | Market size, NovaSkin customer survey, competitive perception, international research, channel analytics | Growth agent (all scenarios) |
| `07_risk_register.md` | Full enterprise risk register across 6 categories; EU-specific risks | Risk agent (all scenarios) |
| `08_board_meeting_minutes_jan2025.md` | Board discussion and consensus on all 3 decisions; investor perspectives; action items | All agents — strategic context |

---

## Eval Scenario → Recommended Doc Set

| Eval Scenario | Problem Statement | Recommended Docs |
|--------------|------------------|--------------------|
| Scenario 1 | "Should we expand into the EU market?" | `00`, `01`, `02`, `06`, `07`, `08` |
| Scenario 2 | "Should we acquire GlowLab at 5x revenue?" | `00`, `01`, `03`, `07`, `08` |
| Scenario 3 | "Should we hire 10 engineers ahead of revenue?" | `00`, `01`, `04`, `05`, `07`, `08` |

---

## Agent Retrieval Query Suggestions

Each agent uses a role-framed query to retrieve relevant chunks. Suggested starting queries:

**Growth Agent**
- Scenario 1: `"EU market expansion opportunity growth potential NovaSkin"`
- Scenario 2: `"GlowLab acquisition strategic growth offline channel haircare"`
- Scenario 3: `"mobile app personalization revenue impact engineering hiring"`

**Finance Agent**
- Scenario 1: `"EU expansion financial projections cost model break-even"`
- Scenario 2: `"GlowLab valuation acquisition cost EBITDA cash position"`
- Scenario 3: `"engineer hiring cost burn rate EBITDA covenant cash runway"`

**Risk Agent**
- Scenario 1: `"EU regulatory compliance risk brand awareness zero state"`
- Scenario 2: `"acquisition risk due diligence misrepresentation covenant GlowLab"`
- Scenario 3: `"hiring risk covenant breach EBITDA cash stress engineering attrition"`
