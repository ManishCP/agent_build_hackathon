---
name: clause-risk
description: >
  Analyze legal clauses in a commercial lease for founder risk. Personal
  guarantees, auto-renewal traps, subletting restrictions, assignment rights.
  Use when lease contains: personal guarantee, guarantor, auto-renewal,
  subletting, assignment, exclusivity, landlord consent.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Clause risk skill

## Instructions
1. Call `analyze_legal_clauses` with extracted values
2. Personal guarantee is always highest severity — surface it first
3. For each flagged clause, give one specific negotiation ask
4. Use severity: 🔴 deal-breaker / 🟡 negotiate / 🟢 standard

## Gotchas
- Personal guarantee = founder's personal assets at risk — always 🔴
- "Good guy clause" limits PG to 3-6 months — always suggest this
- Auto-renewal <90 days = trap — market standard is 90-180 days
- "Sole and absolute discretion" on subletting/assignment = M&A killer
- No subletting clause blocks startup growth — always flag

## Output template
### Legal Clause Risk: [SCORE]/100
| Clause | Status | Severity | Negotiation ask |
|--------|--------|----------|-----------------|
| Personal guarantee | Yes/No | 🔴/🟡/🟢 | [ask] |
| Auto-renewal notice | [days] days | 🔴/🟡/🟢 | [ask] |
| Subletting | [status] | 🔴/🟡/🟢 | [ask] |
| Assignment | [status] | 🔴/🟡/🟢 | [ask] |
