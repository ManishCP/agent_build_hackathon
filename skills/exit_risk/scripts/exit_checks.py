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
