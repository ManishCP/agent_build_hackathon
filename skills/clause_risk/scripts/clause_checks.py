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
