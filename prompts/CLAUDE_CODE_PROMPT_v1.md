# Claude Code Prompt — Lease Analyzer Agent Boilerplate

Paste this entire prompt into Claude Code in your repo root.

---

## THE PROMPT

You are helping me build a boilerplate for a **Lane 1 AI agent** for the TOA Agent Build Day hackathon (June 27, 2026). The agent is a **commercial lease analyzer** — it reads a commercial lease document and outputs a plain-English risk report with red flags and negotiation questions.

The project must conform to the **agentskills.io specification** and the **TOA hackathon judging rubric** (80 points: 25 shippability, 20 ADLC, 20 model selection, 15 skill quality).

Build the complete boilerplate file structure below. Every file should be real, working, and immediately runnable. Use the `agentkit` library already installed in this repo (`from agentkit.loop import run_agent, tool` and `from agentkit.llm import get_client`).

---

## File structure to create

```
lease-analyzer/
├── agent.py
├── skills/
│   ├── financial-risk/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── financial_checks.py
│   ├── clause-risk/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── clause_checks.py
│   ├── exit-risk/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── exit_checks.py
│   └── negotiation-playbook/
│       ├── SKILL.md
│       └── assets/
│           └── negotiation_template.md
├── evals/
│   ├── evals.json
│   └── files/
│       └── sample_lease.txt
├── docs/
│   ├── ADLC.md
│   └── MODEL_SELECTION.md
├── fixtures/
│   └── sample_inputs.json
├── README.md
└── LICENSE
```

---

## Exact content for each file

### agent.py

```python
"""
Lease Analyzer Agent — TOA Agent Build Day 2026
Analyzes commercial lease documents and outputs a risk report.

Usage:
    python agent.py "path/to/lease.txt"
    python agent.py --text "LEASE AGREEMENT Section 4.2: Tenant shall pay..."
    python agent.py "lease.txt" --no-skill    # baseline eval run
    python agent.py "lease.txt" --frontier    # use Claude instead of Granite
"""

import sys
import json
import os
import argparse
from pathlib import Path
from agentkit.loop import run_agent, tool
from agentkit.llm import get_client

# ── IMPORT TOOLS FROM SKILL SCRIPTS ──────────────────────────────────────────
from skills.financial_risk.scripts.financial_checks import (
    check_financial_terms,
    estimate_true_monthly_cost,
    benchmark_escalation_rate,
)
from skills.clause_risk.scripts.clause_checks import (
    check_legal_clauses,
    score_clause_severity,
)
from skills.exit_risk.scripts.exit_checks import (
    check_exit_terms,
    calculate_worst_case_exit_cost,
)

# ── REGISTER TOOLS ────────────────────────────────────────────────────────────

@tool
def analyze_financial_terms(
    lease_type: str,
    monthly_rent: float,
    escalation_pct: float,
    cam_cap_pct: float,
    deposit_months: float
) -> str:
    """
    Analyze financial terms of the lease. Check NNN/CAM risk, escalation rate,
    deposit size. Returns risk score and findings.
    lease_type: 'NNN', 'gross', or 'modified-gross'
    monthly_rent: base monthly rent in dollars
    escalation_pct: annual rent increase percentage
    cam_cap_pct: CAM increase cap percentage (0 if uncapped)
    deposit_months: deposit as number of months rent
    """
    result = check_financial_terms(lease_type, monthly_rent, escalation_pct, cam_cap_pct, deposit_months)
    true_cost = estimate_true_monthly_cost(lease_type, monthly_rent)
    result["estimated_true_monthly_cost"] = true_cost
    result["escalation_benchmark"] = benchmark_escalation_rate(escalation_pct)
    return json.dumps(result)


@tool
def analyze_legal_clauses(
    has_personal_guarantee: bool,
    auto_renewal_notice_days: int,
    subletting_allowed: bool,
    landlord_entry_notice_days: int
) -> str:
    """
    Analyze legal clauses for founder risk. Check personal guarantee,
    auto-renewal trap, subletting restrictions. Returns severity flags.
    has_personal_guarantee: True if lease requires personal guarantee
    auto_renewal_notice_days: days of notice required to prevent auto-renewal
    subletting_allowed: True if tenant can sublet without landlord approval
    landlord_entry_notice_days: notice days landlord must give before entering
    """
    result = check_legal_clauses(
        has_personal_guarantee,
        auto_renewal_notice_days,
        subletting_allowed,
        landlord_entry_notice_days
    )
    return json.dumps(result)


@tool
def analyze_exit_terms(
    early_termination_penalty_months: float,
    holdover_rent_multiplier: float,
    has_break_clause: bool,
    assignment_rights: str
) -> str:
    """
    Analyze exit flexibility and penalties. Check holdover trap, early
    termination cost, whether a break clause exists. Returns exit risk score.
    early_termination_penalty_months: penalty as number of months rent
    holdover_rent_multiplier: e.g. 2.0 means 200% of base rent
    has_break_clause: True if lease has a negotiated early exit option
    assignment_rights: 'free', 'consent-required', or 'prohibited'
    """
    result = check_exit_terms(
        early_termination_penalty_months,
        holdover_rent_multiplier,
        has_break_clause,
        assignment_rights
    )
    worst_case = calculate_worst_case_exit_cost(
        early_termination_penalty_months,
        holdover_rent_multiplier,
        monthly_rent=5000  # default if not extracted
    )
    result["worst_case_exit_cost_usd"] = worst_case
    return json.dumps(result)


# ── LOAD SKILLS ───────────────────────────────────────────────────────────────

def load_skills(use_skill: bool) -> str:
    """Load all skill SKILL.md files and combine into system context."""
    if not use_skill:
        return ""

    skill_dirs = [
        "skills/financial-risk/SKILL.md",
        "skills/clause-risk/SKILL.md",
        "skills/exit-risk/SKILL.md",
        "skills/negotiation-playbook/SKILL.md",
    ]

    skill_text = ""
    for skill_path in skill_dirs:
        p = Path(skill_path)
        if p.exists():
            skill_text += f"\n\n{'='*60}\n"
            skill_text += f"SKILL: {p.parent.name}\n"
            skill_text += f"{'='*60}\n"
            skill_text += p.read_text()

    return skill_text


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lease Analyzer Agent")
    parser.add_argument("input", help="Path to lease file or use --text for inline")
    parser.add_argument("--text", action="store_true", help="Treat input as raw text")
    parser.add_argument("--no-skill", action="store_true", help="Run without skills (baseline)")
    parser.add_argument("--frontier", action="store_true", help="Use Claude instead of Granite")
    args = parser.parse_args()

    # Read lease content
    if args.text:
        lease_content = args.input
    else:
        lease_path = Path(args.input)
        if not lease_path.exists():
            print(f"Error: file not found: {args.input}")
            sys.exit(1)
        lease_content = lease_path.read_text()

    # Select model
    model = "claude-sonnet-4-6" if args.frontier else "granite4:micro"

    # Load skills
    skill_text = load_skills(use_skill=not args.no_skill)

    mode = "NO-SKILL (baseline)" if args.no_skill else "WITH SKILLS"
    print(f"\n{'='*60}")
    print(f"Lease Analyzer Agent — {mode} — model: {model}")
    print(f"{'='*60}\n")

    task = f"""
Analyze the following commercial lease document and produce a complete risk report.

Extract all financial terms, legal clauses, and exit conditions you can find.
Call the analysis tools with the values you extract.
If a value is not stated in the lease, use a conservative default and note it.

LEASE DOCUMENT:
{lease_content}
"""

    result = run_agent(
        task=task,
        tools=[analyze_financial_terms, analyze_legal_clauses, analyze_exit_terms],
        skill=skill_text,
        model=model,
    )

    print(result.answer)
    print(f"\n{'─'*60}")
    print(f"turns={result.turns} | tool_calls={result.tool_calls} | "
          f"tokens={result.tokens} | cost=${result.cost:.4f} | latency={result.latency:.1f}s")


if __name__ == "__main__":
    main()
```

---

### skills/financial-risk/SKILL.md

```markdown
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
```

---

### skills/financial-risk/scripts/financial_checks.py

```python
"""
Financial term checks for commercial leases.
Pure Python — no LLM, no API calls, deterministic.
"""


def check_financial_terms(
    lease_type: str,
    monthly_rent: float,
    escalation_pct: float,
    cam_cap_pct: float,
    deposit_months: float,
) -> dict:
    """Score financial terms and return findings."""
    findings = []
    score = 100  # start at 100, deduct for risks

    # Lease type check
    lease_type_upper = lease_type.upper().replace(" ", "")
    if "NNN" in lease_type_upper or "TRIPLENET" in lease_type_upper:
        if cam_cap_pct == 0:
            findings.append({
                "term": "lease_type",
                "severity": "red",
                "label": "NNN lease with NO CAM cap",
                "detail": "Tenant pays taxes + insurance + maintenance with no limit. "
                          "True cost is 20–40% above stated rent.",
                "negotiation_ask": "Add a 5% annual CAM increase cap to the lease.",
            })
            score -= 30
        else:
            findings.append({
                "term": "lease_type",
                "severity": "yellow",
                "label": f"NNN lease with {cam_cap_pct}% CAM cap",
                "detail": f"NNN lease but CAM increases capped at {cam_cap_pct}%/yr. "
                          f"True cost still 20–40% above stated rent.",
                "negotiation_ask": "Ensure CAM cap is clearly defined in writing.",
            })
            score -= 15
    elif "MODIFIED" in lease_type_upper or "MG" in lease_type_upper:
        findings.append({
            "term": "lease_type",
            "severity": "green",
            "label": "Modified gross lease",
            "detail": "Some operating expenses shared. Review which costs are tenant vs landlord.",
            "negotiation_ask": None,
        })
    else:
        # Gross lease — best for tenant
        findings.append({
            "term": "lease_type",
            "severity": "green",
            "label": "Gross lease",
            "detail": "Landlord covers most operating expenses. Favorable for tenant.",
            "negotiation_ask": None,
        })

    # Escalation check
    if escalation_pct > 5:
        findings.append({
            "term": "escalation",
            "severity": "red",
            "label": f"Rent escalation {escalation_pct}%/yr — significantly above market",
            "detail": f"Market standard is 2–3%/yr. {escalation_pct}% compounds aggressively.",
            "negotiation_ask": "Request escalation at 3% or CPI, whichever is lower.",
        })
        score -= 20
    elif escalation_pct > 3:
        findings.append({
            "term": "escalation",
            "severity": "yellow",
            "label": f"Rent escalation {escalation_pct}%/yr — slightly above market",
            "detail": "Market standard is 2–3%/yr.",
            "negotiation_ask": "Try to negotiate down to 3% or CPI.",
        })
        score -= 10

    # Deposit check
    if deposit_months > 3:
        findings.append({
            "term": "deposit",
            "severity": "red",
            "label": f"Security deposit {deposit_months} months — above market",
            "detail": "Market standard is 1–2 months. This ties up significant capital.",
            "negotiation_ask": f"Request deposit reduction to 2 months (save ${monthly_rent * (deposit_months - 2):,.0f}).",
        })
        score -= 15
    elif deposit_months > 2:
        findings.append({
            "term": "deposit",
            "severity": "yellow",
            "label": f"Security deposit {deposit_months} months — slightly above market",
            "detail": "Market standard is 1–2 months.",
            "negotiation_ask": "Request reduction to 2 months.",
        })
        score -= 5

    return {
        "risk_score": max(0, score),
        "findings": findings,
    }


def estimate_true_monthly_cost(lease_type: str, base_rent: float) -> dict:
    """Estimate true monthly cost including NNN load."""
    lease_type_upper = lease_type.upper().replace(" ", "")
    if "NNN" in lease_type_upper or "TRIPLENET" in lease_type_upper:
        low = base_rent * 1.20
        high = base_rent * 1.40
        return {
            "base_rent": base_rent,
            "nnn_load_estimate_low": round(low - base_rent, 2),
            "nnn_load_estimate_high": round(high - base_rent, 2),
            "true_cost_low": round(low, 2),
            "true_cost_high": round(high, 2),
            "note": "NNN load (taxes + insurance + maintenance) adds 20–40% to base rent.",
        }
    return {
        "base_rent": base_rent,
        "true_cost_low": base_rent,
        "true_cost_high": base_rent,
        "note": "Gross lease — true cost approximates base rent.",
    }


def benchmark_escalation_rate(escalation_pct: float) -> str:
    """Compare escalation rate to market benchmark."""
    if escalation_pct <= 3:
        return "at-or-below-market"
    elif escalation_pct <= 5:
        return "above-market"
    else:
        return "significantly-above-market"
```

---

### skills/clause-risk/SKILL.md

```markdown
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
```

---

### skills/clause-risk/scripts/clause_checks.py

```python
"""
Legal clause checks for commercial leases.
Pure Python — no LLM, no API calls, deterministic.
"""


def check_legal_clauses(
    has_personal_guarantee: bool,
    auto_renewal_notice_days: int,
    subletting_allowed: bool,
    landlord_entry_notice_days: int,
) -> dict:
    """Check legal clauses and return severity findings."""
    findings = []
    score = 100

    # Personal guarantee
    if has_personal_guarantee:
        findings.append({
            "clause": "personal_guarantee",
            "severity": "red",
            "label": "Personal guarantee present — CRITICAL RISK",
            "detail": "Founder's personal assets (home, savings) are legally at risk "
                      "if the company cannot pay rent. This is the #1 risk for startup founders.",
            "negotiation_ask": "Request a 'good guy clause' limiting personal liability "
                               "to 3–6 months rent after proper notice. Most landlords accept this.",
        })
        score -= 35
    else:
        findings.append({
            "clause": "personal_guarantee",
            "severity": "green",
            "label": "No personal guarantee",
            "detail": "Favorable. Personal assets are not at risk.",
            "negotiation_ask": None,
        })

    # Auto-renewal
    if auto_renewal_notice_days < 60:
        findings.append({
            "clause": "auto_renewal",
            "severity": "red",
            "label": f"Auto-renewal notice: {auto_renewal_notice_days} days — dangerously short",
            "detail": f"Only {auto_renewal_notice_days} days to prevent auto-renewal. Very easy to miss.",
            "negotiation_ask": "Extend notice window to at least 180 days and require written confirmation.",
        })
        score -= 20
    elif auto_renewal_notice_days < 90:
        findings.append({
            "clause": "auto_renewal",
            "severity": "yellow",
            "label": f"Auto-renewal notice: {auto_renewal_notice_days} days — below market",
            "detail": "Market standard is 90–180 days.",
            "negotiation_ask": "Request extension to 180 days.",
        })
        score -= 10
    else:
        findings.append({
            "clause": "auto_renewal",
            "severity": "green",
            "label": f"Auto-renewal notice: {auto_renewal_notice_days} days — adequate",
            "detail": "Sufficient time to evaluate renewal decision.",
            "negotiation_ask": None,
        })

    # Subletting
    if not subletting_allowed:
        findings.append({
            "clause": "subletting",
            "severity": "yellow",
            "label": "Subletting requires landlord consent",
            "detail": "Standard for commercial leases but can be a growth trap for startups. "
                      "Ensure consent is 'not unreasonably withheld.'",
            "negotiation_ask": "Add language: 'Landlord consent shall not be unreasonably withheld, "
                               "conditioned, or delayed.'",
        })
        score -= 10
    else:
        findings.append({
            "clause": "subletting",
            "severity": "green",
            "label": "Subletting allowed",
            "detail": "Favorable. Flexibility to sublet if space needs change.",
            "negotiation_ask": None,
        })

    # Landlord entry
    if landlord_entry_notice_days < 1:
        findings.append({
            "clause": "landlord_entry",
            "severity": "red",
            "label": "Landlord entry: no notice required",
            "detail": "Landlord can enter at any time. Privacy and security risk.",
            "negotiation_ask": "Require minimum 48 hours written notice except in emergencies.",
        })
        score -= 15
    elif landlord_entry_notice_days < 2:
        findings.append({
            "clause": "landlord_entry",
            "severity": "yellow",
            "label": f"Landlord entry: {landlord_entry_notice_days} day notice",
            "detail": "Less than the 48-hour market standard.",
            "negotiation_ask": "Request 48-hour written notice.",
        })
        score -= 5

    return {
        "risk_score": max(0, score),
        "findings": findings,
    }


def score_clause_severity(findings: list) -> dict:
    """Aggregate severity counts across all clause findings."""
    counts = {"red": 0, "yellow": 0, "green": 0}
    for f in findings:
        severity = f.get("severity", "green")
        counts[severity] = counts.get(severity, 0) + 1
    return counts
```

---

### skills/exit-risk/SKILL.md

```markdown
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
```

---

### skills/exit-risk/scripts/exit_checks.py

```python
"""
Exit term checks for commercial leases.
Pure Python — no LLM, no API calls, deterministic.
"""


def check_exit_terms(
    early_termination_penalty_months: float,
    holdover_rent_multiplier: float,
    has_break_clause: bool,
    assignment_rights: str,
) -> dict:
    """Check exit terms and return risk findings."""
    findings = []
    score = 100

    # Early termination
    if early_termination_penalty_months > 6:
        findings.append({
            "term": "early_termination",
            "severity": "red",
            "label": f"Early termination penalty: {early_termination_penalty_months} months rent",
            "detail": "Above-market penalty. Locks you in effectively.",
            "negotiation_ask": "Negotiate penalty down to 3–4 months and ask for the full formula in writing.",
        })
        score -= 25
    elif early_termination_penalty_months > 3:
        findings.append({
            "term": "early_termination",
            "severity": "yellow",
            "label": f"Early termination penalty: {early_termination_penalty_months} months rent",
            "detail": "Slightly above the 3-month market standard.",
            "negotiation_ask": "Request reduction to 3 months.",
        })
        score -= 10

    # Holdover
    if holdover_rent_multiplier > 1.5:
        findings.append({
            "term": "holdover",
            "severity": "red",
            "label": f"Holdover rent: {int(holdover_rent_multiplier * 100)}% of base rent",
            "detail": f"One day past lease end = rent at {int(holdover_rent_multiplier * 100)}% automatically. "
                      "This trap catches people constantly.",
            "negotiation_ask": f"Request holdover be reduced to 125% for first 90 days, "
                               "then 150% thereafter.",
        })
        score -= 25
    elif holdover_rent_multiplier > 1.25:
        findings.append({
            "term": "holdover",
            "severity": "yellow",
            "label": f"Holdover rent: {int(holdover_rent_multiplier * 100)}% of base rent",
            "detail": "Slightly above the 125% market standard.",
            "negotiation_ask": "Request reduction to 125%.",
        })
        score -= 10

    # Break clause
    if not has_break_clause:
        findings.append({
            "term": "break_clause",
            "severity": "yellow",
            "label": "No break clause",
            "detail": "No negotiated early exit option. For leases over 3 years, "
                      "this is a significant risk for a growing startup.",
            "negotiation_ask": "Request a break clause at year 2 or 3 with 6 months notice. "
                               "Landlords often accept for a 1–2 month premium.",
        })
        score -= 15
    else:
        findings.append({
            "term": "break_clause",
            "severity": "green",
            "label": "Break clause present",
            "detail": "Favorable. You have a negotiated early exit option.",
            "negotiation_ask": None,
        })

    # Assignment rights
    assignment_lower = assignment_rights.lower()
    if "prohibit" in assignment_lower:
        findings.append({
            "term": "assignment",
            "severity": "red",
            "label": "Assignment prohibited",
            "detail": "Cannot assign lease to an acquirer. This is an M&A deal-killer.",
            "negotiation_ask": "Assignment must be allowed with landlord consent not unreasonably withheld.",
        })
        score -= 20
    elif "sole discretion" in assignment_lower or "sole and absolute" in assignment_lower:
        findings.append({
            "term": "assignment",
            "severity": "red",
            "label": "Assignment requires landlord sole discretion",
            "detail": "Landlord can refuse assignment for any reason. M&A risk.",
            "negotiation_ask": "Change to 'consent not unreasonably withheld.'",
        })
        score -= 20
    elif "consent" in assignment_lower:
        findings.append({
            "term": "assignment",
            "severity": "yellow",
            "label": "Assignment requires landlord consent",
            "detail": "Standard. Ensure 'not unreasonably withheld' is included.",
            "negotiation_ask": "Confirm language includes 'not unreasonably withheld, conditioned, or delayed.'",
        })
        score -= 5

    return {
        "risk_score": max(0, score),
        "findings": findings,
    }


def calculate_worst_case_exit_cost(
    early_termination_penalty_months: float,
    holdover_rent_multiplier: float,
    monthly_rent: float,
) -> dict:
    """Calculate worst-case cost of exiting the lease."""
    termination_cost = early_termination_penalty_months * monthly_rent
    holdover_3_months = holdover_rent_multiplier * monthly_rent * 3
    total = termination_cost + holdover_3_months
    return {
        "early_termination_cost": round(termination_cost, 2),
        "holdover_3_months_cost": round(holdover_3_months, 2),
        "total_worst_case": round(total, 2),
        "note": "Worst case = early termination penalty + 3 months holdover rent",
    }
```

---

### skills/negotiation-playbook/SKILL.md

```markdown
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
```

---

### skills/negotiation-playbook/assets/negotiation_template.md

```markdown
# Negotiation Letter Template

Dear [Landlord/Agent name],

Thank you for providing the lease draft for [address]. We are interested in
moving forward and have reviewed the lease in detail.

We would like to propose the following modifications before executing:

**Priority modifications:**
1. Section [X] — Personal guarantee: We request replacement with a good guy
   clause limiting personal liability to [3-6] months rent after [60-90] days
   written notice of our intent to vacate.

2. Section [X] — Auto-renewal: We request the notice period be extended to
   [180] days, with landlord's written acknowledgment of receipt required.

**Additional modifications:**
3. [Add based on analysis findings]

We are committed to moving forward promptly and look forward to finalizing
these points. Please let us know if you would like to discuss by phone.

Sincerely,
[Name]
```

---

### evals/evals.json

```json
{
  "skill_name": "lease-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "Analyze this lease: NNN lease at $8,500/mo with 4% annual escalation, no CAM cap, 3-month deposit, personal guarantee required, 60-day auto-renewal notice, subletting requires landlord consent, holdover at 200% of base rent, no break clause, early termination penalty of 8 months.",
      "expected_output": "Risk report flagging personal guarantee, NNN true cost, uncapped CAM, above-market escalation, short auto-renewal notice, high holdover rate, no break clause, and high termination penalty. Should include negotiation asks for each.",
      "files": [],
      "assertions": [
        "Output flags personal guarantee as high severity",
        "Output mentions NNN true cost estimate or NNN load",
        "Output flags holdover at 200% or mentions holdover trap",
        "Output includes at least 3 specific negotiation asks",
        "Output includes an overall risk score or rating"
      ]
    },
    {
      "id": 2,
      "prompt": "Review this office lease: Gross lease, $5,000/month, 3% annual escalation, 2-month deposit, no personal guarantee, 180-day auto-renewal notice, subletting allowed, holdover at 125%, has break clause at year 3.",
      "expected_output": "Clean report showing mostly favorable terms. Should identify this as a relatively tenant-friendly lease with minimal red flags.",
      "files": [],
      "assertions": [
        "Output does not flag personal guarantee (there is none)",
        "Output identifies lease as gross (favorable)",
        "Output notes break clause is present",
        "Output gives a relatively low risk score (under 40/100)"
      ]
    },
    {
      "id": 3,
      "prompt": "I'm signing a commercial lease. It has a personal guarantee, the landlord can enter with just 12 hours notice, and the assignment clause says landlord has sole and absolute discretion to approve any assignment.",
      "expected_output": "Should flag all three items as serious risks: personal guarantee, short entry notice, and assignment clause that blocks M&A.",
      "files": [],
      "assertions": [
        "Output flags personal guarantee",
        "Output flags landlord entry notice as insufficient",
        "Output flags assignment clause as M&A risk or deal-killer",
        "Output includes good guy clause as negotiation suggestion"
      ]
    }
  ]
}
```

---

### evals/files/sample_lease.txt

```
COMMERCIAL LEASE AGREEMENT

This Lease Agreement ("Lease") is entered into as of June 1, 2026, between
Fort Point Properties LLC ("Landlord") and StartupCo Inc ("Tenant").

SECTION 1 — PREMISES
Tenant agrees to lease Suite 400 at 123 Congress Street, Boston, MA 02210
("Premises"), consisting of approximately 2,400 rentable square feet.

SECTION 2 — LEASE TERM
The Lease term shall commence July 1, 2026, and expire June 30, 2031
(a period of 60 months, or 5 years).

SECTION 3 — BASE RENT
Tenant shall pay base rent of $8,500 per month for the first year.
Base rent shall increase by 4% per annum on each anniversary of the
commencement date.

SECTION 4 — LEASE TYPE AND ADDITIONAL RENT
This is a triple net (NNN) lease. In addition to base rent, Tenant shall
pay Tenant's proportionate share of real estate taxes, building insurance
premiums, and common area maintenance (CAM) charges. There is no cap on
annual CAM charge increases.

SECTION 5 — SECURITY DEPOSIT
Tenant shall deposit three (3) months base rent ($25,500) as a security
deposit upon execution of this Lease.

SECTION 6 — PERSONAL GUARANTEE
As a condition of this Lease, the principal officer(s) of Tenant shall
execute a personal guarantee of all obligations under this Lease. The
personal guarantee shall remain in effect for the full term of the Lease.

SECTION 7 — AUTO-RENEWAL
This Lease shall automatically renew for successive one-year terms unless
Tenant provides written notice of non-renewal at least sixty (60) days
prior to the expiration of the then-current term.

SECTION 8 — SUBLETTING AND ASSIGNMENT
Tenant shall not sublet the Premises or assign this Lease without the
prior written consent of Landlord. Landlord's consent may be withheld
in Landlord's sole and absolute discretion.

SECTION 9 — HOLDOVER
If Tenant remains in possession of the Premises after the expiration of
the Lease term without a signed renewal, such holdover tenancy shall be
deemed a month-to-month tenancy at a rent equal to two hundred percent
(200%) of the base rent in effect at expiration.

SECTION 10 — EARLY TERMINATION
Tenant may terminate this Lease early upon payment of a termination fee
equal to eight (8) months of then-current base rent, plus any unamortized
tenant improvement allowance and leasing commissions.

SECTION 11 — LANDLORD ACCESS
Landlord may enter the Premises at any time with twenty-four (24) hours
prior notice, or without notice in the case of emergency.

END OF LEASE EXCERPT
```

---

### docs/ADLC.md

```markdown
# ADLC Worksheet — Lease Analyzer Agent
**TOA Agent Build Day · June 27, 2026**

---

## Phase 1: Scope

**Problem:** Startup founders sign commercial leases without understanding
the risks. 20–40 pages of dense legal language contains traps (personal
guarantees, holdover clauses, uncapped NNN) that cost them significantly.

**Target user:** First-time founders or early-stage startup operators
signing their first commercial office or retail lease.

**Success metric:** Agent surfaces every major red flag in a lease that a
founder would miss — personal guarantee, NNN true cost, holdover trap,
auto-renewal window — and provides specific negotiation asks.

**Out of scope:** Tax implications, industry-specific compliance,
residential leases, detailed legal advice (always recommend a lawyer).

**Lane:** Lane 1 — Build from scratch.

---

## Phase 2: Design

**Agent type:** Single-agent loop with 4 skills and 3 deterministic tools.

**Skills:**
- `financial-risk` — NNN, CAM, escalation, deposit
- `clause-risk` — personal guarantee, auto-renewal, subletting
- `exit-risk` — holdover, break clause, assignment
- `negotiation-playbook` — synthesizes all findings into action plan

**Tools (deterministic Python scripts):**
- `analyze_financial_terms()` — scores financial risk
- `analyze_legal_clauses()` — scores legal clause risk
- `analyze_exit_terms()` — scores exit term risk

**Model:** `granite4:micro` (local, free, private) as default.
Claude Sonnet via `--frontier` flag for richer narrative synthesis.

---

## Phase 3: Build

[Fill in during the hackathon — what you built, what changed from design]

---

## Phase 4: Evaluate

**Test cases:** 3 cases in `evals/evals.json`
- Case 1: High-risk lease (all bad clauses)
- Case 2: Clean lease (mostly favorable terms)
- Case 3: Specific clause focus (PG, entry, assignment)

**Without skill:** [fill in after running]
**With skills:** [fill in after running]
**Delta:** [fill in after running]

---

## Phase 5: Deploy

- Public repo: [your GitHub URL]
- Runs locally: `python agent.py evals/files/sample_lease.txt`
- README includes setup + example outputs

---

## Phase 6: Observe

[Fill in after running evals — what the model got wrong, what you fixed]

---

## Phase 7: Iterate

**Planned next improvements:**
- Add `tenant-improvement` skill (TI allowance adequacy)
- Add `force-majeure` skill (pandemic/disaster coverage)
- PDF upload support via pypdf
- Multi-state lease rule variations
```

---

### docs/MODEL_SELECTION.md

```markdown
# Model Selection Rationale
**TOA Agent Build Day · June 27, 2026**

---

## Decision summary

| Task | Model | Reason |
|------|-------|--------|
| Tool calls (extract + score) | `granite4:micro` (local) | Free, private, fast, offline |
| Final synthesis (optional) | `claude-sonnet-4-6` (frontier) | Richer narrative, nuanced explanations |

---

## Default: granite4:micro (local)

**Cost:** $0.00 — runs on device via Ollama
**Latency:** ~2–4 seconds per tool call
**Privacy:** Lease document never leaves the machine
**Quality:** Sufficient for structured tool calls and JSON handling

Granite4:micro handles the agent loop — reading the lease, deciding which
tools to call, passing extracted values. The deterministic scripts do the
actual scoring, so model quality is less critical for the analytical steps.

## Optional: claude-sonnet-4-6 (frontier)

**Cost:** ~$0.003–0.008 per run
**Latency:** +3–5 seconds
**Quality:** Substantially better narrative synthesis and nuanced explanations
**Use:** Run with `--frontier` flag

The frontier model is used optionally for the final synthesis step, where
natural language explanation of complex legal traps benefits from higher
reasoning quality.

## Why this routing makes sense

This mirrors the RouteLLM finding: routing 85%+ of tasks to local models
achieves 95% of frontier quality at a fraction of the cost.

For legal document analysis specifically, keeping data local is a feature —
founders may not want their lease terms processed by a cloud API.

## Trade-off table

| | granite4:micro | claude-sonnet-4-6 |
|--|----------------|-----------------|
| Cost per run | $0.00 | ~$0.005 |
| Latency | ~5s | ~10s |
| Privacy | 100% local | Cloud API |
| Narrative quality | Good | Excellent |
| Tool call reliability | Good | Excellent |

**Default recommendation:** granite4:micro for demos and local use.
Switch to frontier for high-stakes real lease reviews.
```

---

### fixtures/sample_inputs.json

```json
{
  "description": "Sample inputs for offline testing and demos",
  "inputs": [
    {
      "id": "high-risk",
      "label": "High-risk NNN lease (demo input)",
      "text": "NNN lease at $8,500/mo. 4% annual escalation. No CAM cap. Personal guarantee required. 60-day auto-renewal notice. Subletting requires landlord consent sole discretion. Holdover at 200%. No break clause. Early termination: 8 months penalty. Assignment: landlord sole discretion."
    },
    {
      "id": "clean-lease",
      "label": "Clean gross lease (baseline comparison)",
      "text": "Gross lease at $5,000/mo. 3% annual escalation. No personal guarantee. 180-day auto-renewal notice. Subletting allowed. Holdover at 125%. Break clause at year 3 with 6 months notice. Assignment allowed with landlord consent not unreasonably withheld."
    },
    {
      "id": "foreign-founder",
      "label": "Focus: foreign founder edge case",
      "text": "Standard NNN commercial lease. Two co-founders, neither is a US citizen. Personal guarantee clause present. Assignment prohibited without landlord written consent, sole discretion."
    }
  ]
}
```

---

### README.md

```markdown
# Lease Analyzer Agent

**TOA Agent Build Day 2026 · Lane 1**

A commercial lease analyzer that reads a lease document and produces a
plain-English risk report — flagging every major trap with specific
negotiation asks.

Built on the [agentskills.io](https://agentskills.io) standard with 4
specialized skills and 3 deterministic analysis tools.

---

## The problem

Startup founders sign commercial leases blind. Personal guarantees,
uncapped NNN charges, 200% holdover clauses, and 60-day auto-renewal
traps are buried in 20–40 pages of legal language. By the time they find
them, they've already signed.

This agent is the equalizer.

---

## Skills

| Skill | What it checks |
|-------|----------------|
| `financial-risk` | NNN true cost, CAM caps, rent escalation, deposit |
| `clause-risk` | Personal guarantee, auto-renewal window, subletting |
| `exit-risk` | Holdover trap, break clause, early termination cost |
| `negotiation-playbook` | Synthesizes all flags into a prioritized action plan |

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://astral.sh/uv) installed
- [Ollama](https://ollama.com) installed with `granite4:micro` pulled

```bash
ollama pull granite4:micro
```

### Install

```bash
git clone <your-repo-url>
cd lease-analyzer
uv sync
```

### Validate skills

```bash
skills-ref validate skills/financial-risk
skills-ref validate skills/clause-risk
skills-ref validate skills/exit-risk
skills-ref validate skills/negotiation-playbook
```

---

## Usage

### Analyze a lease file

```bash
uv run python agent.py evals/files/sample_lease.txt
```

### Analyze pasted text

```bash
uv run python agent.py --text "NNN lease at $8,500/mo, personal guarantee required, holdover at 200%..."
```

### Baseline run (no skill — for eval comparison)

```bash
uv run python agent.py evals/files/sample_lease.txt --no-skill
```

### Use frontier model (Claude Sonnet)

```bash
uv run python agent.py evals/files/sample_lease.txt --frontier
```

---

## Demo

Run the baseline first, then with skills:

```bash
# Baseline — generic response
uv run python agent.py evals/files/sample_lease.txt --no-skill

# With skills — full risk report + negotiation asks
uv run python agent.py evals/files/sample_lease.txt
```

---

## Evals

```bash
# Run full eval suite
uv run python -m agentkit.evals evals/evals.json
```

Results saved to `evals/benchmark.json`.

---

## Model selection

Default model: `granite4:micro` (local, free, private — lease data never leaves your machine).

Optional: `--frontier` flag uses Claude Sonnet for richer narrative synthesis.

See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for full rationale.

---

## ADLC

See [docs/ADLC.md](docs/ADLC.md) for the full Agent Development Life Cycle worksheet.

---

## License

MIT
```

---

### LICENSE

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## INSTRUCTIONS FOR CLAUDE CODE

1. Create every file listed above with exactly the content shown.
2. Create all directories as needed.
3. After creating all files, run:
   ```bash
   skills-ref validate skills/financial-risk
   skills-ref validate skills/clause-risk  
   skills-ref validate skills/exit-risk
   skills-ref validate skills/negotiation-playbook
   ```
4. Fix any validation errors.
5. Then run the smoke test:
   ```bash
   uv run python agent.py evals/files/sample_lease.txt --no-skill
   ```
   Then:
   ```bash
   uv run python agent.py evals/files/sample_lease.txt
   ```
6. Show me the output of both runs side by side.
7. If there are import errors (agentkit structure may differ slightly), 
   check how the existing starter projects import from agentkit and match 
   that pattern exactly. Look at `projects/everyday/fridge-whisperer/agent.py`
   for the correct import pattern.
8. Finally, stage all files and show me the git status.

Do not ask for confirmation — create all files and run the validation immediately.
```
