"""
Lease Analyzer Agent — TOA Agent Build Day 2026
Analyzes commercial lease documents and outputs a risk report.

Usage:
    python agent.py lease.txt
    python agent.py lease1.txt lease2.txt lease3.txt
    python agent.py --dir leases/
    python agent.py --text "LEASE AGREEMENT Section 4.2: Tenant shall pay..."
    python agent.py lease.txt --no-skill    # baseline eval run
    python agent.py lease.txt --frontier    # use Claude instead of Granite
"""

import sys
import json
import re
import argparse
from datetime import datetime, timezone
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

# ── SCORE STATE — populated by tool calls during a run ───────────────────────
_run_scores: dict = {}


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
    _run_scores["financial_score"] = result.get("risk_score")
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
    _run_scores["clause_score"] = result.get("risk_score")
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
        monthly_rent=5000
    )
    result["worst_case_exit_cost_usd"] = worst_case
    _run_scores["exit_score"] = result.get("risk_score")
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


# ── PDF EXTRACTION ────────────────────────────────────────────────────────────

def extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() for page in reader.pages)
    except ImportError:
        return f"[PDF: {path.name} — install pypdf to extract text: uv add pypdf]"
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


# ── COMBINED SCORECARD ────────────────────────────────────────────────────────

def print_combined_scorecard(results: list[dict]) -> None:
    """Print a combined scorecard table across all analyses."""
    print("\n" + "=" * 70)
    print("COMBINED SCORECARD — ALL SKILLS")
    print("=" * 70)
    print(f"\n{'Lease':<30} {'Financial':>10} {'Clauses':>10} {'Exit':>10} {'Overall':>10}")
    print("-" * 70)

    for r in results:
        name = Path(r.get("filename", "unknown")).stem[:28]
        fin  = r.get("financial_score")
        cla  = r.get("clause_score")
        ex   = r.get("exit_score")

        scores = [s for s in [fin, cla, ex] if isinstance(s, (int, float))]
        overall = round(sum(scores) / len(scores)) if scores else None

        if isinstance(overall, (int, float)):
            if overall >= 70:
                label = "🟢 LOW RISK"
            elif overall >= 40:
                label = "🟡 MEDIUM"
            else:
                label = "🔴 HIGH RISK"
        else:
            label = "—"

        fin_str = f"{fin}/100"     if fin     is not None else "N/A"
        cla_str = f"{cla}/100"     if cla     is not None else "N/A"
        ex_str  = f"{ex}/100"      if ex      is not None else "N/A"
        ov_str  = f"{overall}/100" if overall is not None else "N/A"

        print(f"{name:<30} {fin_str:>10} {cla_str:>10} {ex_str:>10} {ov_str:>10}  {label}")

    print("=" * 70)
    print("\nScore guide: 0–39 = high risk  |  40–69 = review carefully  |  70–100 = acceptable\n")


# ── LOGGING ───────────────────────────────────────────────────────────────────

def log_run(result: dict) -> None:
    """Append run metrics to logs/runs.jsonl."""
    Path("logs").mkdir(exist_ok=True)

    scores = [s for s in [
        result.get("financial_score"),
        result.get("clause_score"),
        result.get("exit_score"),
    ] if isinstance(s, (int, float))]
    overall = round(sum(scores) / len(scores)) if scores else None

    log_entry = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "filename":        result.get("filename"),
        "model":           result.get("model"),
        "skill_used":      result.get("skill_used"),
        "financial_score": result.get("financial_score"),
        "clause_score":    result.get("clause_score"),
        "exit_score":      result.get("exit_score"),
        "overall_score":   overall,
        "turns":           result.get("turns"),
        "tokens":          result.get("tokens"),
        "cost_usd":        result.get("cost"),
        "latency_seconds": result.get("latency"),
    }
    with open("logs/runs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"[logged to logs/runs.jsonl]")


# ── SINGLE FILE ANALYSIS ──────────────────────────────────────────────────────

def run_lease_analysis(filename: str, content: str, model: str,
                       skill_text: str, use_skill: bool) -> dict:
    """Run full analysis on one lease document. Returns result dict."""
    global _run_scores
    _run_scores = {}  # reset scores for this run

    mode = "WITH SKILLS" if use_skill else "NO-SKILL (baseline)"
    print(f"\n{'='*60}")
    print(f"Analyzing: {filename}")
    print(f"Mode: {mode} | Model: {model}")
    print(f"{'='*60}\n")

    task = f"""
Analyze the following commercial lease document and produce a complete risk report.

Extract all financial terms, legal clauses, and exit conditions you can find.
Call ALL THREE analysis tools (analyze_financial_terms, analyze_legal_clauses,
analyze_exit_terms) with the values you extract.
If a value is not stated in the lease, use a conservative default and note it.

LEASE DOCUMENT:
{content}
"""

    agent_result = run_agent(
        task=task,
        tools=[analyze_financial_terms, analyze_legal_clauses, analyze_exit_terms],
        skill=skill_text,
        model=model,
    )

    print(agent_result.answer)
    print(f"\n{'─'*60}")
    print(f"turns={agent_result.turns} | tool_calls={agent_result.tool_calls} | "
          f"tokens={agent_result.tokens} | cost=${agent_result.cost:.4f} | latency={agent_result.latency:.1f}s")

    result = {
        "filename":        filename,
        "model":           model,
        "skill_used":      use_skill,
        "financial_score": _run_scores.get("financial_score"),
        "clause_score":    _run_scores.get("clause_score"),
        "exit_score":      _run_scores.get("exit_score"),
        "turns":           agent_result.turns,
        "tool_calls":      agent_result.tool_calls,
        "tokens":          agent_result.tokens,
        "cost":            agent_result.cost,
        "latency":         agent_result.latency,
        "answer":          agent_result.answer,
    }
    return result


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lease Analyzer Agent")
    parser.add_argument("inputs", nargs="*", help="Lease file path(s)")
    parser.add_argument("--text", type=str, help="Analyze inline text directly")
    parser.add_argument("--dir", type=str, help="Analyze all .txt/.pdf files in a directory")
    parser.add_argument("--no-skill",  action="store_true", help="Run without skills (baseline)")
    parser.add_argument("--frontier",  action="store_true", help="Use Claude Sonnet instead of Granite")
    args = parser.parse_args()

    model      = "claude-sonnet-4-6" if args.frontier else "granite4:micro"
    use_skill  = not args.no_skill
    skill_text = load_skills(use_skill)

    # ── Collect files to process ──────────────────────────────────────────────
    files_to_process: list[tuple[str, str]] = []  # (filename, content)

    if args.text:
        files_to_process = [("inline-text", args.text)]
    elif args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            print(f"Error: not a directory: {args.dir}")
            sys.exit(1)
        for ext in ["*.txt", "*.pdf"]:
            for f in sorted(d.glob(ext)):
                if f.name == "README.md":
                    continue
                content = extract_pdf_text(f) if f.suffix == ".pdf" else f.read_text()
                files_to_process.append((str(f), content))
        if not files_to_process:
            print(f"No .txt or .pdf files found in {args.dir}")
            sys.exit(1)
    elif args.inputs:
        for inp in args.inputs:
            p = Path(inp)
            if not p.exists():
                print(f"Warning: file not found: {inp}, skipping")
                continue
            content = extract_pdf_text(p) if p.suffix == ".pdf" else p.read_text()
            files_to_process.append((str(p), content))
    else:
        # Default: sample lease
        default = Path("evals/files/sample_lease.txt")
        if not default.exists():
            print("Error: no input provided and default sample not found")
            sys.exit(1)
        files_to_process = [(str(default), default.read_text())]

    # ── Process each file ─────────────────────────────────────────────────────
    all_results = []
    for filename, content in files_to_process:
        result = run_lease_analysis(filename, content, model, skill_text, use_skill)
        log_run(result)
        all_results.append(result)

    # ── Combined scorecard (always shown) ─────────────────────────────────────
    print_combined_scorecard(all_results)


if __name__ == "__main__":
    main()
