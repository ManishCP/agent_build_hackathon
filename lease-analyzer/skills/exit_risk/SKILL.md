---
name: exit-risk
description: >
  Analyze exit flexibility and termination terms in a commercial lease.
  Check early termination penalties, holdover rent clauses, break clause
  availability, and assignment rights on company sale or acquisition. Use
  when the lease contains any of: holdover, early termination, break clause,
  lease expiry, assignment, surrender, notice to vacate, termination penalty.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Exit risk skill

## When to activate
Activate when analyzing exit terms and termination flexibility in a
commercial lease. This skill covers: holdover traps, early exit costs,
break clause negotiation, and acquisition assignment rights.

## Instructions

1. Call `analyze_exit_terms` with extracted values.
2. Always calculate and surface the worst-case exit cost in dollars.
3. Flag absence of a break clause for leases over 3 years.
4. For startups, flag no-assignment clause as it blocks acquisitions.

## Gotchas — never get these wrong

- **Holdover clause**: If a tenant stays even ONE DAY past the lease end
  without a signed renewal, holdover rent kicks in automatically. Most
  holdover clauses set rent at 150–200% of base rent. This catches people
  every single time. Always surface it.
- **No break clause**: A 5-year lease with no break clause is a 5-year trap.
  Startups should always negotiate a break clause at year 2 or 3.
  Landlords often accept a small premium (1–3 months rent) for this.
- **Assignment on acquisition**: "Assignment prohibited" or "landlord consent
  required with sole discretion" means a potential acquirer cannot take on
  your lease. This is a deal-killer in M&A. Must be negotiable.
- **Early termination formula**: Penalties are often structured as "remaining
  rent + unamortized TI allowance + leasing commissions." Always ask for
  the full formula in writing before signing.

## Risk thresholds

| Term | 🟢 Standard | 🟡 Flag | 🔴 Red flag |
|------|-------------|---------|-------------|
| Early termination | ≤3 months | 3–6 months | >6 months or not allowed |
| Holdover rate | ≤125% | 125–150% | >150% |
| Break clause | At yr 2–3 | Not present on 5yr+ lease | Not present on any lease |
| Assignment | Consent not unreasonably withheld | Landlord sole discretion | Prohibited |

## Output template

```
### Exit Risk: [SCORE]/100

| Term | Value | Risk |
|------|-------|------|
| Early termination penalty | [months] months rent | 🟢/🟡/🔴 |
| Holdover rate | [pct]% of base rent | 🟢/🟡/🔴 |
| Break clause | [Yes/No, at yr X] | 🟢/🟡/🔴 |
| Assignment rights | [status] | 🟢/🟡/🔴 |

**Worst-case exit cost: $[amount]**
```
