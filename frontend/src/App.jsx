import { useMemo, useState } from "react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Cell,
  BarChart,
  Bar,
} from "recharts";

// ✅ Use env var for deploy, fallback to localhost for dev
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const defaultAnswers = {
  age: 3,
  income_stability: 3,
  investment_horizon: 3,
  risk_tolerance: 3,
  experience: 3,
  liquidity_need: 3,
  loss_reaction: 3,
  goal_priority: 3,
  debt_level: 3,
  emergency_fund: 3,
};

const questionLabels = {
  age: "Age group",
  income_stability: "Income stability",
  investment_horizon: "Investment horizon",
  risk_tolerance: "Risk tolerance",
  experience: "Investment experience",
  liquidity_need: "Need cash soon?",
  loss_reaction: "Reaction to losses",
  goal_priority: "Goal priority",
  debt_level: "Debt level",
  emergency_fund: "Emergency fund readiness",
};

function classNames(...xs) {
  return xs.filter(Boolean).join(" ");
}

export default function App() {
  const [answers, setAnswers] = useState(defaultAnswers);

  // ✅ risk profile
  const [profile, setProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [profileError, setProfileError] = useState("");

  // tickers
  const [tickers, setTickers] = useState("AAPL,MSFT,GOOGL,AMZN");

  // ✅ optimize
  const [opt, setOpt] = useState(null);
  const [loadingOpt, setLoadingOpt] = useState(false);
  const [optError, setOptError] = useState("");

  // ✅ backtest
  const [backtest, setBacktest] = useState(null);
  const [backtestError, setBacktestError] = useState("");
  const [loadingBacktest, setLoadingBacktest] = useState(false);

  // ✅ report
  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState("");
  const [loadingReport, setLoadingReport] = useState(false);

  // ✅ monte carlo
  const [mc, setMc] = useState(null);
  const [mcError, setMcError] = useState("");
  const [loadingMc, setLoadingMc] = useState(false);
  const [mcYears, setMcYears] = useState(5);
  const [mcSims, setMcSims] = useState(1000);

  const tickersList = useMemo(
    () => tickers.split(",").map((t) => t.trim()).filter(Boolean),
    [tickers]
  );

  const handleChange = (k, v) => setAnswers((p) => ({ ...p, [k]: Number(v) }));

  const resetAll = () => {
    setAnswers(defaultAnswers);

    setProfile(null);
    setProfileError("");

    setOpt(null);
    setOptError("");

    setBacktest(null);
    setBacktestError("");

    setReport(null);
    setReportError("");

    setMc(null);
    setMcError("");
  };

  // ✅ Get profile with error handling
  const getProfile = async () => {
    setLoadingProfile(true);
    setProfileError("");

    try {
      const res = await axios.post(`${API}/risk-profile`, answers);
      setProfile(res.data);

      // reset downstream outputs
      setOpt(null);
      setOptError("");
      setBacktest(null);
      setBacktestError("");
      setReport(null);
      setReportError("");
      setMc(null);
      setMcError("");
    } catch (e) {
      setProfile(null);
      setProfileError(e?.response?.data?.detail || e.message);
    } finally {
      setLoadingProfile(false);
    }
  };

  const optimize = async () => {
    if (!profile) return;

    setLoadingOpt(true);
    setOptError("");

    try {
      const res = await axios.post(`${API}/optimize`, {
        tickers: tickersList,
        risk_category: profile.category,
        years: 3,
      });
      setOpt(res.data);

      setBacktest(null);
      setBacktestError("");
      setReport(null);
      setReportError("");
      setMc(null);
      setMcError("");
    } catch (e) {
      setOpt(null);
      setOptError(e?.response?.data?.detail || e.message);
    } finally {
      setLoadingOpt(false);
    }
  };

  const runBacktest = async () => {
    if (!opt?.weights) {
      setBacktestError("Optimize first to get weights.");
      return;
    }

    setLoadingBacktest(true);
    setBacktestError("");

    try {
      const res = await axios.post(`${API}/backtest`, {
        tickers: tickersList,
        weights: opt.weights,
        years: 3,
        benchmark: "SPY",
      });
      setBacktest(res.data);
    } catch (e) {
      setBacktest(null);
      setBacktestError(e?.response?.data?.detail || e.message);
    } finally {
      setLoadingBacktest(false);
    }
  };

  const generateReport = async () => {
    if (!opt?.weights || !profile) {
      setReportError("Get risk profile + optimize first.");
      return;
    }

    setLoadingReport(true);
    setReportError("");

    try {
      const metricsRes = await axios.post(`${API}/metrics`, {
        tickers: tickersList,
        weights: opt.weights,
        years: 3,
        benchmark: "SPY",
      });

      const reportRes = await axios.post(`${API}/report`, {
        risk_category: profile.category,
        tickers: tickersList,
        weights: opt.weights,
        metrics: metricsRes.data,
        benchmark: "SPY",
      });

      setReport(reportRes.data);
    } catch (e) {
      setReport(null);
      setReportError(e?.response?.data?.detail || e.message);
    } finally {
      setLoadingReport(false);
    }
  };

  const runMonteCarlo = async () => {
    if (!opt?.weights) {
      setMcError("Optimize first to get weights.");
      return;
    }

    setLoadingMc(true);
    setMcError("");

    try {
      const res = await axios.post(`${API}/monte-carlo`, {
        tickers: tickersList,
        weights: opt.weights,
        years: Number(mcYears),
        simulations: Number(mcSims),
      });
      setMc(res.data);
    } catch (e) {
      setMc(null);
      setMcError(e?.response?.data?.detail || e.message);
    } finally {
      setLoadingMc(false);
    }
  };

  const pieData =
    opt?.weights
      ? Object.entries(opt.weights).map(([name, value]) => ({ name, value }))
      : [];

  const backtestData = useMemo(() => {
    if (!backtest) return [];
    const n = backtest.dates.length;
    const step = Math.ceil(n / 220);
    const out = [];
    for (let i = 0; i < n; i += step) {
      out.push({
        date: backtest.dates[i],
        portfolio: backtest.portfolio_equity[i],
        benchmark: backtest.benchmark_equity[i],
      });
    }
    return out;
  }, [backtest]);

  const mcHistogram = useMemo(() => {
    if (!mc?.final_values?.length) return [];
    const values = mc.final_values;
    const min = Math.min(...values);
    const max = Math.max(...values);

    const bins = 25;
    const width = (max - min) / bins || 1;
    const counts = Array(bins).fill(0);

    for (const v of values) {
      const idx = Math.min(bins - 1, Math.floor((v - min) / width));
      counts[idx] += 1;
    }

    return counts.map((c, i) => ({
      bucket: `${(min + i * width).toFixed(2)} - ${(min + (i + 1) * width).toFixed(2)}`,
      count: c,
    }));
  }, [mc]);

  const mcProbLoss = useMemo(() => {
    if (!mc?.final_values?.length) return null;
    const values = mc.final_values;
    const losses = values.filter((v) => v < 1).length;
    return (losses / values.length) * 100;
  }, [mc]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-950/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-5 py-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Risk Profiling & Portfolio Optimizer
              </h1>
              <p className="text-sm text-slate-300">
                Full-stack quant mini robo-advisor: optimize, backtest, metrics, advisor report & Monte Carlo.
              </p>
            </div>
            <div className="text-xs text-slate-400">
              API: <span className="text-slate-200">{API}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-5 py-6 space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Risk Profile Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">1) Risk Questionnaire</h2>
              <p className="text-sm text-slate-300">
                Answer 10 quick questions (1–5). We estimate your risk category.
              </p>
            </div>

            <div className="grid gap-3">
              {Object.keys(defaultAnswers).map((k) => (
                <div key={k} className="flex items-center justify-between gap-4">
                  <label className="text-sm text-slate-200">
                    {questionLabels[k] || k.replaceAll("_", " ")}
                  </label>
                  <select
                    className="w-24 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                    value={answers[k]}
                    onChange={(e) => handleChange(k, e.target.value)}
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={getProfile}
                disabled={loadingProfile}
                className={classNames(
                  "rounded-xl px-4 py-2 text-sm font-medium",
                  loadingProfile
                    ? "cursor-not-allowed bg-slate-700/40 text-slate-300"
                    : "bg-indigo-500 text-white hover:bg-indigo-400 active:bg-indigo-600"
                )}
              >
                {loadingProfile ? "Calculating..." : "Get Risk Profile"}
              </button>

              <button
                onClick={resetAll}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800"
              >
                Reset
              </button>
            </div>

            {profileError && <p className="mt-3 text-sm text-red-400">{profileError}</p>}

            {profile && (
              <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs text-emerald-300">
                    Category: {profile.category}
                  </span>
                  <span className="rounded-full bg-slate-700/40 px-3 py-1 text-xs text-slate-200">
                    Score: {profile.score}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-300">
                  Suggested split:{" "}
                  <span className="text-slate-100 font-medium">Equity {profile.suggested_equity_pct}%</span>{" "}
                  / <span className="text-slate-100 font-medium">Debt {profile.suggested_debt_pct}%</span>
                </p>
              </div>
            )}
          </div>

          {/* Optimizer Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">2) Optimize Portfolio</h2>
              <p className="text-sm text-slate-300">Enter tickers → compute an allocation (no short selling).</p>
            </div>

            <label className="text-sm text-slate-200">Tickers (comma separated)</label>
            <input
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              placeholder="AAPL,MSFT,GOOGL,AMZN"
            />

            <div className="mt-4 flex flex-wrap gap-3">
              <button
                onClick={optimize}
                disabled={!profile || loadingOpt}
                className={classNames(
                  "rounded-xl px-4 py-2 text-sm font-medium",
                  !profile || loadingOpt
                    ? "cursor-not-allowed bg-slate-700/40 text-slate-300"
                    : "bg-indigo-500 text-white hover:bg-indigo-400 active:bg-indigo-600"
                )}
              >
                {loadingOpt ? "Optimizing..." : "Optimize"}
              </button>

              {opt && (
                <button
                  onClick={runBacktest}
                  disabled={loadingBacktest}
                  className={classNames(
                    "rounded-xl border px-4 py-2 text-sm",
                    loadingBacktest
                      ? "cursor-not-allowed border-slate-700 text-slate-400"
                      : "border-slate-700 text-slate-200 hover:bg-slate-800"
                  )}
                >
                  {loadingBacktest ? "Backtesting..." : "Run Backtest"}
                </button>
              )}

              {opt && (
                <button
                  onClick={generateReport}
                  disabled={loadingReport}
                  className={classNames(
                    "rounded-xl border px-4 py-2 text-sm",
                    loadingReport
                      ? "cursor-not-allowed border-slate-700 text-slate-400"
                      : "border-slate-700 text-slate-200 hover:bg-slate-800"
                  )}
                >
                  {loadingReport ? "Generating..." : "Advisor Report"}
                </button>
              )}
            </div>

            {optError && <p className="mt-3 text-sm text-red-400">{optError}</p>}

            {opt && (
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-sm text-slate-300">Expected annual return</div>
                  <div className="text-xl font-semibold">{opt.expected_annual_return}</div>

                  <div className="mt-3 text-sm text-slate-300">Annual volatility</div>
                  <div className="text-xl font-semibold">{opt.annual_volatility}</div>

                  <div className="mt-3 text-sm text-slate-300">Sharpe ratio</div>
                  <div className="text-xl font-semibold">{opt.sharpe_ratio}</div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-sm text-slate-300 mb-2">Allocation</div>
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={85} label>
                          {pieData.map((_, idx) => (
                            <Cell key={idx} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {!profile && (
              <p className="mt-4 text-sm text-slate-400">
                Tip: generate your risk profile first, then optimize.
              </p>
            )}
          </div>
        </div>

        {/* Backtest */}
        {backtest && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">3) Backtest vs Benchmark</h2>
              <p className="text-sm text-slate-300">Historical simulation of portfolio growth vs SPY.</p>
            </div>

            {backtestError && <p className="mt-2 text-sm text-red-400">{backtestError}</p>}

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={backtestData}>
                    <CartesianGrid />
                    <XAxis dataKey="date" hide />
                    <YAxis tickFormatter={(v) => v.toFixed(2)} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="portfolio" name="Portfolio" dot={false} />
                    <Line type="monotone" dataKey="benchmark" name="Benchmark (SPY)" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Advisor Report */}
        {opt && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">4) Advisor Report</h2>
              <p className="text-sm text-slate-300">Readable explanation of what the portfolio means.</p>
            </div>

            {reportError && <p className="mt-2 text-sm text-red-400">{reportError}</p>}

            {!report && (
              <p className="text-sm text-slate-400">Click “Advisor Report” above to generate.</p>
            )}

            {report && (
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-sm text-slate-200">{report.summary}</p>
                <ul className="mt-3 list-disc pl-5 space-y-2 text-sm text-slate-200">
                  {report.bullets.map((b, idx) => (
                    <li key={idx}>{b}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Monte Carlo */}
        {opt && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold">5) Monte Carlo Simulation</h2>
              <p className="text-sm text-slate-300">Estimate outcome distribution after N years.</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-200">Years</span>
                <input
                  type="number"
                  value={mcYears}
                  onChange={(e) => setMcYears(e.target.value)}
                  className="w-24 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-200">Simulations</span>
                <input
                  type="number"
                  value={mcSims}
                  onChange={(e) => setMcSims(e.target.value)}
                  className="w-32 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />
              </div>

              <button
                onClick={runMonteCarlo}
                disabled={loadingMc}
                className={classNames(
                  "rounded-xl px-4 py-2 text-sm font-medium",
                  loadingMc
                    ? "cursor-not-allowed bg-slate-700/40 text-slate-300"
                    : "bg-indigo-500 text-white hover:bg-indigo-400 active:bg-indigo-600"
                )}
              >
                {loadingMc ? "Running..." : "Run Monte Carlo"}
              </button>
            </div>

            {mcError && <p className="mt-3 text-sm text-red-400">{mcError}</p>}

            {mc && (
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={mcHistogram}>
                        <CartesianGrid />
                        <XAxis dataKey="bucket" hide />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="count" name="Final outcomes count" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                  <div className="text-sm font-medium text-slate-200 mb-3">
                    Outcome summary (starting ₹1)
                  </div>

                  <div className="space-y-3">
                    <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3">
                      <div className="text-xs text-slate-400">5% worst case (p5)</div>
                      <div className="text-lg font-semibold">{mc.p5.toFixed(2)}×</div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3">
                      <div className="text-xs text-slate-400">Median (p50)</div>
                      <div className="text-lg font-semibold">{mc.p50.toFixed(2)}×</div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3">
                      <div className="text-xs text-slate-400">5% best case (p95)</div>
                      <div className="text-lg font-semibold">{mc.p95.toFixed(2)}×</div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3">
                      <div className="text-xs text-slate-400">Chance of loss</div>
                      <div className="text-lg font-semibold">
                        {mcProbLoss === null ? "-" : `${mcProbLoss.toFixed(2)}%`}
                      </div>
                      <p className="mt-2 text-xs text-slate-400">
                        % of simulations ending below ₹1 after {mcYears} years.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="text-center text-xs text-slate-500 py-4">
          Built with FastAPI + React + SciPy Optimization + Market Data + Simulation
        </div>
      </div>
    </div>
  );
}