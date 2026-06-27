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
