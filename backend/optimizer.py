import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

RISK_FREE_RATE = 0.04  # 4% default risk-free rate


def fetch_returns(tickers, years: int = 3) -> pd.DataFrame:
    """
    Downloads historical prices and returns daily % returns.
    Uses auto_adjust=True so 'Close' is reliable (no 'Adj Close' issues).
    """
    data = yf.download(
        tickers,
        period=f"{years}y",
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    # Prefer Close
    if isinstance(data, pd.DataFrame) and "Close" in data.columns:
        close = data["Close"]
    else:
        # Fallback: some yfinance versions may return close-like DF already
        close = data

    # Single ticker may return Series
    if isinstance(close, pd.Series):
        name = tickers[0] if isinstance(tickers, list) else str(tickers)
        close = close.to_frame(name=name)

    close = close.dropna(how="any")
    returns = close.pct_change().dropna(how="any")

    if returns.empty or returns.shape[0] < 40:
        raise ValueError("Not enough price data returned for the selected tickers/time window.")

    return returns


def _risk_cap(risk_category: str) -> float:
    return {"Conservative": 0.35, "Moderate": 0.45, "Aggressive": 0.60}.get(risk_category, 0.45)


def _annual_stats(returns: pd.DataFrame):
    mu = returns.mean() * 252
    cov = returns.cov() * 252
    return mu, cov


def _portfolio_return(w, mu):
    return float(np.dot(w, mu))


def _portfolio_vol(w, cov):
    return float(np.sqrt(np.dot(w.T, np.dot(cov, w))))


def optimize_portfolio(
    returns: pd.DataFrame,
    risk_category: str,
    mode: str = "max_sharpe",
    target_return: float | None = None,
):
    """
    mode: "max_sharpe" | "min_variance" | "target_return"
    """
    mu, cov = _annual_stats(returns)
    n = len(mu)

    cap = _risk_cap(risk_category)
    bounds = [(0.0, cap)] * n

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    if mode == "target_return":
        if target_return is None:
            raise ValueError("target_return is required when mode='target_return'")
        constraints.append({"type": "eq", "fun": lambda w: _portfolio_return(w, mu) - float(target_return)})

    def objective(w):
        port_ret = _portfolio_return(w, mu)
        port_vol = _portfolio_vol(w, cov)

        if mode == "min_variance" or mode == "target_return":
            return port_vol  # minimize volatility

        if mode == "max_sharpe":
            sharpe = (port_ret - RISK_FREE_RATE) / (port_vol + 1e-12)
            return -sharpe

        raise ValueError("Invalid mode. Use: max_sharpe | min_variance | target_return")

    w0 = np.array([1.0 / n] * n)

    res = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 300},
    )

    if not res.success:
        raise RuntimeError("Optimization failed: " + res.message)

    w = res.x
    port_ret = _portfolio_return(w, mu)
    port_vol = _portfolio_vol(w, cov)
    sharpe = float((port_ret - RISK_FREE_RATE) / (port_vol + 1e-12))

    return w, port_ret, port_vol, sharpe


def efficient_frontier(returns: pd.DataFrame, risk_category: str, points: int = 30):
    """
    Generates efficient frontier points by solving min-variance for a range of target returns.
    Returns:
      frontier: list of {"return": r, "vol": v}
      w_min_var, w_max_sharpe
    """
    mu, cov = _annual_stats(returns)

    # endpoints: min variance and max sharpe
    w_min_var, r_min_var, v_min_var, s_min_var = optimize_portfolio(
        returns, risk_category=risk_category, mode="min_variance"
    )
    w_max_sharpe, r_ms, v_ms, s_ms = optimize_portfolio(
        returns, risk_category=risk_category, mode="max_sharpe"
    )

    # target returns grid (avoid impossible extremes)
    r_low = max(min(mu) * 0.9, r_min_var * 0.9)
    r_high = max(mu) * 0.95
    if r_high <= r_low:
        r_low = float(min(mu)) * 0.9
        r_high = float(max(mu)) * 0.95

    targets = np.linspace(r_low, r_high, points)

    frontier = []
    for tr in targets:
        try:
            w, pr, pv, ps = optimize_portfolio(
                returns,
                risk_category=risk_category,
                mode="target_return",
                target_return=float(tr),
            )
            frontier.append({"return": float(pr), "vol": float(pv)})
        except Exception:
            # skip infeasible targets
            continue

    # Make sure we at least have a couple points
    if len(frontier) < 5:
        # fallback: include min var and max sharpe points
        frontier = [{"return": float(r_min_var), "vol": float(v_min_var)}, {"return": float(r_ms), "vol": float(v_ms)}]

    return frontier, w_min_var, w_max_sharpe


def _to_weight_vector(tickers: list[str], weights: dict[str, float]) -> np.ndarray:
    w = np.array([float(weights.get(t, 0.0)) for t in tickers], dtype=float)
    s = w.sum()
    if s <= 0:
        raise ValueError("Weights sum to 0. Provide valid weights.")
    return w / s  # normalize


def portfolio_daily_returns(asset_returns: pd.DataFrame, tickers: list[str], weights: dict[str, float]) -> pd.Series:
    w = _to_weight_vector(tickers, weights)
    # align tickers order with dataframe columns
    cols = [t for t in tickers if t in asset_returns.columns]
    if len(cols) != len(tickers):
        missing = sorted(set(tickers) - set(cols))
        raise ValueError(f"Missing returns for tickers: {missing}")
    r = asset_returns[cols]
    return (r @ w)


def compute_metrics(
    tickers: list[str],
    weights: dict[str, float],
    years: int = 3,
    benchmark: str = "SPY",
) -> dict:
    # Fetch asset returns
    asset_returns = fetch_returns(tickers, years=years)
    port_ret = portfolio_daily_returns(asset_returns, tickers, weights)

    # Benchmark daily returns
    bench_returns_df = fetch_returns([benchmark], years=years)
    bench_ret = bench_returns_df[benchmark]

    # Align dates
    df = pd.concat([port_ret.rename("p"), bench_ret.rename("b")], axis=1).dropna()
    p = df["p"]
    b = df["b"]

    # Equity curve
    equity = (1 + p).cumprod()
    peak = equity.cummax()
    drawdown = (equity / peak) - 1.0
    max_dd = float(drawdown.min())  # negative number

    # Annualized stats
    ann_ret = float((equity.iloc[-1]) ** (252 / len(p)) - 1)  # CAGR approx
    ann_vol = float(p.std() * np.sqrt(252))

    # Sharpe/Sortino
    rf_daily = RISK_FREE_RATE / 252
    excess = p - rf_daily
    sharpe = float((excess.mean() / (p.std() + 1e-12)) * np.sqrt(252))

    downside = p[p < 0]
    downside_std = float(downside.std() * np.sqrt(252)) if len(downside) > 1 else 0.0
    sortino = float(((p.mean() - rf_daily) / (downside.std() + 1e-12)) * np.sqrt(252)) if len(downside) > 1 else 0.0

    # VaR / CVaR (historical, 95%)
    alpha = 0.05
    var_95 = float(np.quantile(p, alpha))  # e.g., -0.02 = -2% in a day
    cvar_95 = float(p[p <= var_95].mean()) if (p <= var_95).any() else var_95

    # Beta vs benchmark: cov(p,b)/var(b)
    beta = float(np.cov(p, b)[0, 1] / (np.var(b) + 1e-12))

    return {
        "cagr": round(ann_ret, 4),
        "annual_volatility": round(ann_vol, 4),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "max_drawdown": round(max_dd, 4),
        "var_95": round(var_95, 4),
        "cvar_95": round(cvar_95, 4),
        "beta_vs_benchmark": round(beta, 4),
    }

def backtest_portfolio(
    tickers: list[str],
    weights: dict[str, float],
    years: int = 3,
    benchmark: str = "SPY",
):
    # Fetch returns
    asset_returns = fetch_returns(tickers, years=years)
    w = _to_weight_vector(tickers, weights)

    # Portfolio daily returns
    port_daily = asset_returns[tickers] @ w

    # Benchmark returns
    bench_df = fetch_returns([benchmark], years=years)
    bench_daily = bench_df[benchmark]

    # Align
    df = pd.concat([port_daily.rename("p"), bench_daily.rename("b")], axis=1).dropna()
    p = df["p"]
    b = df["b"]

    # Equity curves
    port_equity = (1 + p).cumprod()
    bench_equity = (1 + b).cumprod()

    # Drawdowns
    port_dd = (port_equity / port_equity.cummax()) - 1
    bench_dd = (bench_equity / bench_equity.cummax()) - 1

    return {
        "portfolio_equity": port_equity.tolist(),
        "benchmark_equity": bench_equity.tolist(),
        "dates": df.index.strftime("%Y-%m-%d").tolist(),
        "portfolio_final_return": float(port_equity.iloc[-1] - 1),
        "benchmark_final_return": float(bench_equity.iloc[-1] - 1),
        "portfolio_max_drawdown": float(port_dd.min()),
        "benchmark_max_drawdown": float(bench_dd.min()),
    }

def monte_carlo_simulation(
    tickers: list[str],
    weights: dict[str, float],
    years: int = 5,
    simulations: int = 1000,
):
    returns = fetch_returns(tickers, years=3)

    w = _to_weight_vector(tickers, weights)
    port_daily = returns[tickers] @ w

    mu = port_daily.mean()
    sigma = port_daily.std()

    days = 252 * years

    final_values = []

    for _ in range(simulations):
        simulated_daily = np.random.normal(mu, sigma, days)
        equity = (1 + simulated_daily).cumprod()
        final_values.append(float(equity[-1]))

    final_values = np.array(final_values)

    return {
        "final_values": final_values.tolist(),
        "p5": float(np.percentile(final_values, 5)),
        "p50": float(np.percentile(final_values, 50)),
        "p95": float(np.percentile(final_values, 95)),
    }