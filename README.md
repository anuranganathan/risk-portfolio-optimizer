# Risk Profiling & Portfolio Optimizer 🚀

A full-stack quant mini robo-advisor built using **FastAPI + React (Vite) + Tailwind + Recharts**.

This application:
- Computes an investor’s **risk category** from a 10-question questionnaire
- Generates an **optimized portfolio allocation**
- Runs **backtesting vs benchmark**
- Calculates **risk metrics**
- Generates an **advisor report**
- Performs **Monte Carlo simulations**

---

## 🌐 Live Demo

Frontend (Vercel):  
https://risk-portfolio-optimizer.vercel.app  

Backend (Render):  
https://risk-portfolio-optimizer.onrender.com  

---

## 📌 Features

### 1️⃣ Risk Profiling
- 10-question scoring system (1–5 scale)
- Outputs:
  - Risk Score
  - Risk Category
  - Suggested Equity/Debt Split

### 2️⃣ Portfolio Optimization
- Input stock tickers
- Computes allocation weights
- Displays:
  - Expected Return
  - Volatility
  - Sharpe Ratio
  - Allocation chart

### 3️⃣ Backtesting
- Historical portfolio simulation
- Benchmark comparison (SPY)
- Final return & drawdown metrics

### 4️⃣ Risk Metrics
- Expected return
- Volatility
- Sharpe ratio
- Maximum drawdown

### 5️⃣ Advisor Report
- Generates structured portfolio explanation

### 6️⃣ Monte Carlo Simulation
- Future return simulation
- Outputs percentile outcomes (p5, p50, p95)

---

## 🏗️ Tech Stack

### Frontend
- React (Vite)
- Tailwind CSS
- Recharts
- Axios

### Backend
- FastAPI
- NumPy
- Uvicorn

### Deployment
- Render (Backend)
- Vercel (Frontend)

---

## 📂 Project Structure

```
risk-portfolio-optimizer/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── Procfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🛠️ Local Development

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at:
```
http://127.0.0.1:8000
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Create a `.env` file inside `frontend/`:

```
VITE_API_URL=http://127.0.0.1:8000
```

Frontend runs at:
```
http://localhost:5173
```

---

## 🚀 Deployment

### Backend (Render)

- Root Directory: `backend`
- Build Command:
```
pip install -r requirements.txt
```
- Start Command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### Frontend (Vercel)

- Root Directory: `frontend`
- Framework: Vite
- Environment Variable:
```
VITE_API_URL=https://risk-portfolio-optimizer.onrender.com
```

After setting environment variable → Redeploy.

---

## 📡 API Endpoints

```
POST /risk-profile
POST /optimize
POST /backtest
POST /metrics
POST /report
POST /monte-carlo
```

---

## 📜 License

MIT License

---

## 👩‍💻 Author

Full-stack fintech project built to explore quantitative finance, optimization algorithms, and production deployment workflows.
