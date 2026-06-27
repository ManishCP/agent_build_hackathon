---
name: clause-risk
description: >
  Analyze legal clauses in a commercial lease for founder and tenant risk.
  Identify personal guarantees, auto-renewal traps, subletting restrictions,
  assignment limitations, and landlord entry rights. Use when the lease
  contains any of: personal guarantee, guarantor, auto-renewal, automatic
  renewal, subletting, sublease, assignment, exclusivity, landlord entry,
  right of entry, consent required.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Clause risk skill

## When to activate
Activate when analyzing legal clauses in a commercial lease. This skill
covers: personal guarantees, auto-renewal mechanics, subletting rights,
assignment on acquisition, and landlord access rights.

## Instructions

1. Call `analyze_legal_clauses` with values extracted from the lease.
2. Personal guarantee is always the highest-severity finding — surface it first.
3. For each flagged clause, provide the specific negotiation ask.
4. Use the severity table below to classify each clause.

## Gotchas — never get these wrong

- **Personal guarantee**: This means the founder's personal assets (home,
  savings, investments) are legally at risk if the company cannot pay rent.
  This is the single most dangerous clause for a startup founder. It is
  almost always negotiable — ask for a "good guy clause" instead.
- **Good guy clause**: Limits personal liability to 3–6 months rent after
  giving notice. Landlords often accept this. Always suggest it.
- **Auto-renewal under 90 days**: If you must give fewer than 90 days notice
  to prevent auto-renewal, this is an easy trap. Founders miss this constantly.
  Market standard is 90–180 days.
- **No subletting**: Startups grow fast. If you can't sublet extra space, you're
  stuck paying for desks you don't use. "Landlord consent not unreasonably
  withheld" is the minimum to negotiate for.
- **Assignment on acquisition**: If your company is acquired, the lease may not
  automatically transfer to the acquirer. This can kill M&A deals. Ensure
  assignment is allowed with landlord consent not unreasonably withheld.

## Severity classification

| Clause | 🔴 Deal-breaker | 🟡 Negotiate | 🟢 Standard |
|--------|-----------------|--------------|-------------|
| Personal guarantee | Full PG | PG >6 months | Good guy clause |
| Auto-renewal notice | <60 days | 60–90 days | >90 days |
| Subletting | Prohibited | Consent required | Allowed |
| Assignment | Prohibited | Consent required | Allowed with notice |
| Landlord entry | No notice | <24hr notice | 24–48hr notice |

## Output template

```
### Legal Clause Risk: [SCORE]/100

| Clause | Status | Severity | Negotiation ask |
|--------|--------|----------|-----------------|
| Personal guarantee | [Yes/No] | 🔴/🟡/🟢 | [ask] |
| Auto-renewal notice | [days] days | 🔴/🟡/🟢 | [ask] |
| Subletting | [status] | 🔴/🟡/🟢 | [ask] |
| Assignment | [status] | 🔴/🟡/🟢 | [ask] |
| Landlord entry | [days] days | 🔴/🟡/🟢 | [ask] |
```
