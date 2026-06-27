---
name: financial-risk
description: >
  Analyze financial terms in a commercial lease document. Identify NNN charges,
  CAM fees and caps, rent escalation rates, deposit requirements, and estimate
  the true monthly cost beyond stated base rent. Use when the lease contains
  any of: NNN, triple net, CAM, common area maintenance, base rent, additional
  rent, operating expenses, rent escalation, CPI adjustment, deposit, security
  deposit.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Financial risk skill

## When to activate
Activate when analyzing financial terms in a commercial lease. This skill
covers: lease type classification, true cost estimation, escalation analysis,
and CAM risk assessment.

## Instructions

1. Call `analyze_financial_terms` with all values you can extract from the lease.
2. If monthly rent is not stated, note this explicitly in the output.
3. Always calculate and surface the estimated true monthly cost (base + NNN load).
4. Compare escalation rate to the 2–3%/yr market benchmark.

## Gotchas — never get these wrong

- **NNN true cost**: A "triple net" lease means tenant pays base rent PLUS
  property taxes, building insurance, and maintenance. The NNN load is
  typically 20–40% on top of stated rent. Always surface this.
- **Uncapped CAM**: CAM with no annual cap = unlimited exposure. Flag as 🔴.
  Market standard cap is 3–5% per year.
- **Rent escalation over 3%/yr**: Flag as above-market. Over 5%/yr = red flag.
- **Deposit over 2 months**: Flag. More than 2 months is above market for most
  commercial spaces.
- **"Additional rent"**: This phrase in a lease almost always means NNN or CAM
  charges are coming. Flag it even if amounts aren't specified.

## Benchmark thresholds

| Term | 🟢 Standard | 🟡 Flag | 🔴 Red flag |
|------|-------------|---------|-------------|
| Lease type | Gross | Modified gross | NNN uncapped |
| Escalation | ≤3%/yr | 3–5%/yr | >5%/yr or uncapped |
| CAM cap | 3–5%/yr cap | >5%/yr cap | No cap |
| Deposit | 1–2 months | 2–3 months | >3 months |

## Output template

```
### Financial Risk: [SCORE]/100

| Term | Value | Benchmark | Risk |
|------|-------|-----------|------|
| Lease type | [type] | Gross preferred | 🟢/🟡/🔴 |
| Base rent | $[amount]/mo | — | — |
| Estimated true cost | $[total]/mo | — | 🟡/🔴 if NNN |
| Escalation | [pct]%/yr | 2–3%/yr | 🟢/🟡/🔴 |
| CAM cap | [pct]% or None | 3–5%/yr | 🟢/🟡/🔴 |
| Deposit | [months] months | 1–2 months | 🟢/🟡/🔴 |

**Key findings:**
- [finding 1]
- [finding 2]
```
