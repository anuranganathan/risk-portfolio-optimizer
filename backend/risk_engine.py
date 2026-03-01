from models import RiskAnswers, RiskProfile

def compute_risk_profile(a: RiskAnswers) -> RiskProfile:
    # Simple scoring: sum of 10 answers (each 1..5) => 10..50
    score = (
        a.age + a.income_stability + a.investment_horizon + a.risk_tolerance +
        a.experience + a.liquidity_need + a.loss_reaction + a.goal_priority +
        a.debt_level + a.emergency_fund
    )

    # Buckets (tuneable)
    if score <= 22:
        category = "Conservative"
        equity, debt = 30, 70
    elif score <= 36:
        category = "Moderate"
        equity, debt = 55, 45
    else:
        category = "Aggressive"
        equity, debt = 75, 25

    return RiskProfile(
        score=score,
        category=category,
        suggested_equity_pct=equity,
        suggested_debt_pct=debt
    )