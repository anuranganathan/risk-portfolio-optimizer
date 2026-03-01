from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    RiskAnswers,
    RiskProfile,
    OptimizeRequest,
    OptimizeResponse,
    OptimizeModesRequest,
    EfficientFrontierRequest,
    EfficientFrontierResponse,
    MetricsRequest,
    MetricsResponse,
    BacktestRequest, 
    BacktestResponse,
    ReportRequest, 
    ReportResponse,
    MonteCarloRequest, 
    MonteCarloResponse
)
from risk_engine import compute_risk_profile
from optimizer import fetch_returns, optimize_portfolio, efficient_frontier, compute_metrics,backtest_portfolio,monte_carlo_simulation
from report_engine import build_report
app = FastAPI(title="Personal Investment Risk Profiling & Portfolio Optimizer")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only; restrict later for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "API running 🚀"}


@app.post("/risk-profile", response_model=RiskProfile)
def risk_profile(answers: RiskAnswers):
    return compute_risk_profile(answers)


# Backward-compatible endpoint: keep it as MAX SHARPE
@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    try:
        returns = fetch_returns(req.tickers, years=req.years)

        w, port_ret, port_vol, sharpe = optimize_portfolio(
            returns=returns,
            risk_category=req.risk_category,
            mode="max_sharpe",
        )

        weights = {t: float(round(w[i], 4)) for i, t in enumerate(req.tickers)}

        return OptimizeResponse(
            tickers=req.tickers,
            weights=weights,
            expected_annual_return=round(port_ret, 4),
            annual_volatility=round(port_vol, 4),
            sharpe_ratio=round(sharpe, 4),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# New endpoint: choose optimization mode
@app.post("/optimize/modes", response_model=OptimizeResponse)
def optimize_modes(req: OptimizeModesRequest):
    try:
        returns = fetch_returns(req.tickers, years=req.years)

        w, port_ret, port_vol, sharpe = optimize_portfolio(
            returns=returns,
            risk_category=req.risk_category,
            mode=req.mode,
            target_return=req.target_return,
        )

        weights = {t: float(round(w[i], 4)) for i, t in enumerate(req.tickers)}

        return OptimizeResponse(
            tickers=req.tickers,
            weights=weights,
            expected_annual_return=round(port_ret, 4),
            annual_volatility=round(port_vol, 4),
            sharpe_ratio=round(sharpe, 4),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Efficient frontier endpoint
@app.post("/efficient-frontier", response_model=EfficientFrontierResponse)
def get_efficient_frontier(req: EfficientFrontierRequest):
    try:
        returns = fetch_returns(req.tickers, years=req.years)

        # For frontier we still need a cap category; you can wire this to user later
        frontier, w_min_var, w_max_sharpe = efficient_frontier(
            returns=returns,
            risk_category="Moderate",
            points=req.points,
        )

        min_var = {t: float(round(w_min_var[i], 4)) for i, t in enumerate(req.tickers)}
        max_sharpe = {t: float(round(w_max_sharpe[i], 4)) for i, t in enumerate(req.tickers)}

        return EfficientFrontierResponse(
            tickers=req.tickers,
            frontier=frontier,
            min_variance=min_var,
            max_sharpe=max_sharpe,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/metrics", response_model=MetricsResponse)
def metrics(req: MetricsRequest):
    try:
        out = compute_metrics(
            tickers=req.tickers,
            weights=req.weights,
            years=req.years,
            benchmark=req.benchmark,
        )
        return MetricsResponse(**out)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/backtest", response_model=BacktestResponse)
def backtest(req: BacktestRequest):
    try:
        result = backtest_portfolio(
            tickers=req.tickers,
            weights=req.weights,
            years=req.years,
            benchmark=req.benchmark,
        )
        return BacktestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/report", response_model=ReportResponse)
def report(req: ReportRequest):
    try:
        out = build_report(
            risk_category=req.risk_category,
            tickers=req.tickers,
            weights=req.weights,
            metrics=req.metrics.model_dump() if hasattr(req.metrics, "model_dump") else dict(req.metrics),
            benchmark=req.benchmark
        )
        return ReportResponse(**out)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/monte-carlo", response_model=MonteCarloResponse)
def monte_carlo(req: MonteCarloRequest):
    try:
        result = monte_carlo_simulation(
            tickers=req.tickers,
            weights=req.weights,
            years=req.years,
            simulations=req.simulations,
        )
        return MonteCarloResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))