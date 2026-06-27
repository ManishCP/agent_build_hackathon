---
name: financial-risk
description: >
  Analyze financial terms in a commercial lease. NNN charges, CAM fees,
  rent escalation, deposit size, true monthly cost. Use when lease contains:
  NNN, triple net, CAM, base rent, additional rent, escalation, deposit,
  operating expenses.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Financial risk skill

## Instructions
1. Call `analyze_financial_terms` with all extracted values
2. If a value is missing, use conservative defaults and note it
3. Always surface the estimated true monthly cost (NNN adds 20-40%)
4. Compare escalation to 2-3%/yr market benchmark
5. Use the output template below — no prose rambling

## Gotchas
- NNN uncapped = unlimited tenant exposure — always flag 🔴
- "Additional rent" phrase = NNN charges incoming — flag even if amounts unstated
- Escalation >3%/yr = above market; >5%/yr = red flag
- Deposit >2 months = above market
- Never trust stated rent as true cost on NNN leases

## Output template
### Financial Risk: [SCORE]/100
| Term | Value | Benchmark | Risk |
|------|-------|-----------|------|
| Lease type | [type] | Gross preferred | 🟢/🟡/🔴 |
| True monthly cost | $[total]/mo | = base rent on gross | 🟢/🟡/🔴 |
| Escalation | [pct]%/yr | 2–3%/yr | 🟢/🟡/🔴 |
| CAM cap | [pct]% or None | 3–5%/yr cap | 🟢/🟡/🔴 |
| Deposit | [months] months | 1–2 months | 🟢/🟡/🔴 |
**Key findings:** [2-3 bullet points max]
