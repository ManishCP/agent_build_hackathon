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
        "skills/financial_risk/SKILL.md",
        "skills/clause_risk/SKILL.md",
        "skills/exit_risk/SKILL.md",
        "skills/negotiation_playbook/SKILL.md",
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
