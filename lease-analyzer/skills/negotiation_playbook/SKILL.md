---
name: negotiation-playbook
description: >
  Generate a prioritized negotiation action plan from lease analysis findings.
  Always load this skill after financial-risk, clause-risk, and exit-risk
  skills have run. Synthesizes all flags into a ranked list of negotiation
  asks ordered by impact. Use at the end of any commercial lease analysis.
license: MIT
metadata:
  author: lease-analyzer-team
  version: "1.0"
---

# Negotiation playbook skill

## When to activate
Load this skill last, after all other analysis skills have run.
Use it to synthesize all findings into a prioritized action plan.

## Instructions

1. Collect all 🔴 and 🟡 findings from financial, clause, and exit analysis.
2. Rank by severity: 🔴 items first, then 🟡 items.
3. For each item, produce one specific, actionable negotiation ask.
4. Identify the top 3 "must-get" changes — the ones worth walking away over.
5. Use the output template below.

## Ranking logic

Priority 1 (must-get): Personal guarantee, NNN uncapped, assignment prohibited
Priority 2 (negotiate hard): Holdover >150%, no break clause, auto-renewal <90 days
Priority 3 (nice to have): CAM cap, escalation rate, deposit reduction

## Negotiation principles encoded in this skill

- **Walk-away items**: Personal guarantee (full PG), assignment prohibited,
  holdover >200%. These fundamentally change the risk profile.
- **Always negotiate in writing**: Any verbal agreement means nothing.
  Every change must be in the lease amendment.
- **Bundle asks**: Don't negotiate one item at a time. Present all asks
  together — landlords are more likely to concede on smaller items if
  you've already agreed on the big ones.
- **Timing**: Negotiate before you signal you want the space. Leverage
  disappears once the landlord knows you're committed.

## Output template

```
## Negotiation Action Plan

### Must-get changes (walk away if refused)
1. [item]: [specific ask]
2. [item]: [specific ask]

### Negotiate hard
3. [item]: [specific ask]
4. [item]: [specific ask]

### Nice to have
5. [item]: [specific ask]

### Estimated value of successful negotiation
- [quantified savings or risk reduction per item]
- **Total potential savings: $[amount] over lease term**

### Bring to your next landlord meeting
- [ ] [specific question 1]
- [ ] [specific question 2]
- [ ] [specific question 3]
```
