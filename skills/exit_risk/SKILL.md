---
name: exit-risk
description: >
  Analyze exit flexibility and termination terms in a commercial lease.
  Holdover rent, early termination penalties, break clauses, assignment
  on acquisition. Use when lease contains: holdover, early termination,
  break clause, lease expiry, assignment, surrender, termination penalty.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Exit risk skill

## Instructions
1. Call `analyze_exit_terms` with extracted values
2. Always calculate and surface worst-case exit cost in dollars
3. Flag missing break clause on leases >3 years
4. Flag assignment restrictions as M&A risk

## Gotchas
- Holdover at 200% = one day late doubles rent — always explain in plain English
- No break clause on 5yr lease = startup trap — always flag 🟡
- "Assignment prohibited" = M&A deal-killer — always flag 🔴
- Early termination penalty >6 months = very high — flag 🔴
- Get exit penalty formula in writing — it often includes TI + commissions

## Output template
### Exit Risk: [SCORE]/100
| Term | Value | Risk |
|------|-------|------|
| Early termination | [months] months rent | 🟢/🟡/🔴 |
| Holdover rate | [pct]% of base rent | 🟢/🟡/🔴 |
| Break clause | Yes/No | 🟢/🟡/🔴 |
| Assignment rights | [status] | 🟢/🟡/🔴 |
**Worst-case exit cost: $[amount]**
