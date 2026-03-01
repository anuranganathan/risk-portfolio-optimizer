def build_report(risk_category: str, tickers: list[str], weights: dict[str, float], metrics: dict, benchmark: str = "SPY"):
    # helper: top holdings
    top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
    top_str = ", ".join([f"{t} ({round(w*100,1)}%)" for t, w in top])

    cagr = metrics["cagr"] * 100
    vol = metrics["annual_volatility"] * 100
    sharpe = metrics["sharpe"]
    sortino = metrics["sortino"]
    mdd = metrics["max_drawdown"] * 100
    var95 = metrics["var_95"] * 100
    cvar95 = metrics["cvar_95"] * 100
    beta = metrics["beta_vs_benchmark"]

    tone = {
        "Conservative": "You prefer safety and stability over high returns.",
        "Moderate": "You can handle some ups and downs for better long-term growth.",
        "Aggressive": "You’re comfortable with higher volatility in exchange for higher potential returns."
    }.get(risk_category, "Your risk preference is balanced.")

    summary = (
        f"Your risk category is {risk_category}. {tone} "
        f"This portfolio spreads your investment across {len(tickers)} assets. "
        f"Top allocations are: {top_str}."
    )

    bullets = [
        f"Estimated annual growth (CAGR): {cagr:.2f}%.",
        f"Volatility (how much it fluctuates): {vol:.2f}% per year.",
        f"Sharpe ratio (return per risk): {sharpe:.2f} (higher is better).",
        f"Sortino ratio (focuses on downside risk): {sortino:.2f}.",
        f"Worst historical crash (max drawdown): {mdd:.2f}%.",
        f"Bad-day risk (VaR 95%): about {var95:.2f}% loss on a bad day.",
        f"Very bad-day risk (CVaR 95%): about {cvar95:.2f}% loss on the worst days.",
        f"Compared to {benchmark}, your portfolio moves about {beta:.2f}× as much (beta).",
        "Tip: If you want lower risk, choose Min Variance mode. If you want best risk-adjusted return, choose Max Sharpe.",
    ]

    return {"summary": summary, "bullets": bullets}