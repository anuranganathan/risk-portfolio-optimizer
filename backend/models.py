from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from typing import Literal, Optional, List, Dict


class RiskAnswers(BaseModel):
    # each answer is an int score 1..5 (we’ll map them to points)
    age: int = Field(ge=1, le=5)
    income_stability: int = Field(ge=1, le=5)
    investment_horizon: int = Field(ge=1, le=5)
    risk_tolerance: int = Field(ge=1, le=5)
    experience: int = Field(ge=1, le=5)
    liquidity_need: int = Field(ge=1, le=5)
    loss_reaction: int = Field(ge=1, le=5)
    goal_priority: int = Field(ge=1, le=5)
    debt_level: int = Field(ge=1, le=5)
    emergency_fund: int = Field(ge=1, le=5)

class RiskProfile(BaseModel):
    score: int
    category: str
    suggested_equity_pct: int
    suggested_debt_pct: int

class OptimizeRequest(BaseModel):
    tickers: List[str]
    risk_category: str  # "Conservative" | "Moderate" | "Aggressive"
    years: int = Field(default=3, ge=1, le=10)

class OptimizeResponse(BaseModel):
    tickers: List[str]
    weights: Dict[str, float]
    expected_annual_return: float
    annual_volatility: float
    sharpe_ratio: float


class OptimizeModesRequest(BaseModel):
    tickers: List[str]
    risk_category: str
    years: int = Field(default=3, ge=1, le=10)
    mode: Literal["max_sharpe", "min_variance", "target_return"]
    target_return: Optional[float] = None  # only needed for target_return mode

class EfficientFrontierRequest(BaseModel):
    tickers: List[str]
    years: int = Field(default=3, ge=1, le=10)
    points: int = Field(default=30, ge=10, le=100)

class EfficientFrontierResponse(BaseModel):
    tickers: List[str]
    frontier: List[Dict[str, float]]  # [{"return":..., "vol":...}, ...]
    min_variance: Dict[str, float]    # weights
    max_sharpe: Dict[str, float]      # weights




class MetricsRequest(BaseModel):
    tickers: List[str]
    weights: Dict[str, float]  # must sum ~1
    years: int = Field(default=3, ge=1, le=10)
    benchmark: str = "SPY"     # you can switch later (e.g., ^NSEI)

class MetricsResponse(BaseModel):
    cagr: float
    annual_volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    beta_vs_benchmark: float


class BacktestRequest(BaseModel):
    tickers: List[str]
    weights: Dict[str, float]
    years: int = 3
    benchmark: str = "SPY"

class BacktestResponse(BaseModel):
    portfolio_equity: List[float]
    benchmark_equity: List[float]
    dates: List[str]
    portfolio_final_return: float
    benchmark_final_return: float
    portfolio_max_drawdown: float
    benchmark_max_drawdown: float


class ReportRequest(BaseModel):
    risk_category: str
    tickers: List[str]
    weights: Dict[str, float]
    metrics: MetricsResponse
    benchmark: str = "SPY"

class ReportResponse(BaseModel):
    summary: str
    bullets: List[str]

class MonteCarloRequest(BaseModel):
    tickers: List[str]
    weights: Dict[str, float]
    years: int = 5
    simulations: int = 1000

class MonteCarloResponse(BaseModel):
    final_values: List[float]
    p5: float
    p50: float
    p95: float