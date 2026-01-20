from typing import Dict, List, Any

# Risk scoring weights
RISK_WEIGHTS = {
    # Legal Risks
    "missing_indemnity_cap": 2.0,
    "unilateral_termination": 1.5,
    "governing_law_foreign": 1.0,
    "liabilities_uncapped": 2.5,
    "consequential_damages_included": 1.0,
    
    # Financial Risks
    "payment_terms_long": 1.0,
    "auto_renewal_price_uncapped": 1.5,
    "late_payment_penalty_high": 0.5,
    
    # Operational/Compliance Risks
    "sla_uptime_low": 1.5,
    "missing_gdpr_clause": 2.0,
    "audit_rights_missing": 1.0
}

BASE_RISK_SCORE = 1.0

def calculate_risk_score(features: Dict[str, Any]) -> float:
    """
    Calculate risk score (1-10) based on extracted features.
    Higher score = Higher risk
    """
    score = BASE_RISK_SCORE
    
    # Legal Features
    if features.get("indemnity_cap_present") is False:
        score += RISK_WEIGHTS["missing_indemnity_cap"]
    
    if features.get("termination_for_convenience") is False:
        score += RISK_WEIGHTS["unilateral_termination"] * 0.5
        
    if features.get("liability_cap_present") is False:
        score += RISK_WEIGHTS["liabilities_uncapped"]
        
    if features.get("consequential_damages_waiver") is False:
        score += RISK_WEIGHTS["consequential_damages_included"]

    # Finance Features
    payment_days = features.get("payment_terms_days", 30)
    if isinstance(payment_days, (int, float)) and payment_days > 60:
        score += RISK_WEIGHTS["payment_terms_long"]
    
    if features.get("price_increase_cap_present") is False and features.get("auto_renewal") is True:
        score += RISK_WEIGHTS["auto_renewal_price_uncapped"]

    # Compliance/Ops Features
    sla = features.get("sla_uptime", 99.9)
    if isinstance(sla, (int, float)) and sla < 99.0:
        score += RISK_WEIGHTS["sla_uptime_low"]
        
    if features.get("gdpr_addressed") is False:
        score += RISK_WEIGHTS["missing_gdpr_clause"]
        
    # Cap score at 10, min 1
    return max(1.0, min(10.0, score))

def determine_risk_level(score: float) -> str:
    """Determine risk level category from score"""
    if score >= 7.5:
        return "Critical"
    elif score >= 5.0:
        return "High"
    elif score >= 3.0:
        return "Medium"
    else:
        return "Low"
