# 🧠 ZeptoBrain — Dark Store Inventory Intelligence System

> **Built to solve Zepto's ₹3,367 crore loss problem.**  
> AI-powered system that predicts demand, flags spoilage risk, and optimizes inter-store transfers — all in real time.

---

## 🎯 Problem Statement

Zepto operates 300+ dark stores across India, each managing 2,500+ SKUs.

| Problem | Impact |
|---|---|
| Perishables over-ordered | ₹crores in daily wastage |
| Demand not predicted per store | Wrong stock = stockouts + wastage |
| No inter-store coordination | Store A wastes while Store B runs out |
| No spoilage early warning | Staff react *after* items expire |

**ZeptoBrain solves all four — simultaneously.**

---

## 🚀 What It Does

### 1. 🔮 Demand Forecasting (XGBoost)
- Per-SKU, per-store, 7-day ahead predictions
- Accounts for: day of week, festivals, weather signals, rolling demand
- **MAPE: 12.9%** on held-out Nov-Dec 2024 test set
- Features: lag-7 sales, rolling means, festival flags, weekend multipliers

### 2. ⚠️ Spoilage Risk Scoring
- Real-time 0–100 risk score per perishable item
- Inputs: current stock, shelf life remaining, predicted demand
- Actions: "Discount 30%" / "Transfer NOW" / "Monitor"
- Detects expired items before manual check

### 3. 🔄 Inter-Store Transfer Optimizer
- Finds Store A (excess) + Store B (low stock) pairs for same SKU
- Distance-constrained (< 10 km transfers only)
- Calculates exact transfer quantity + financial impact
- Prevents dual loss: wastage at A AND stockout at B

### 4. 📊 Live Dashboard
- 5-tab React dashboard
- Real-time spoilage alerts, forecast charts, transfer map
- ROI calculator showing exact savings
- Filter by store, category, risk level

---

## 📊 Results on Simulated Data

| Metric | Value |
|---|---|
| Records analyzed | 149,650 |
| Stores | 5 (Mumbai dark stores) |
| SKUs tracked | 82 |
| Annual waste simulated | ₹1.11 Crore |
| Annual savings (30% reduction) | ₹33.3 Lakhs |
| Model MAPE | 12.9% |
| Tests passing | 59/59 ✅ |

---

## 🛠️ Tech Stack

| Layer | Tech | Why |
|---|---|---|
| ML | Python + XGBoost | Industry standard for tabular demand forecasting |
| Backend | FastAPI | Fast async API, auto docs at /docs |
| Database | SQLite (dev) / PostgreSQL (prod) | Zepto uses PostgreSQL |
| Frontend | React + Recharts | Clean, interactive charts |
| Data | Zepto-style simulated dataset | Real SKUs, real price points |
| Testing | pytest + FastAPI TestClient | 59 tests, 100% pass |

---

## 📁 Project Structure

```
zeptobrain/
├── data/
│   ├── generate_data.py        ← Realistic Zepto-style data generator
│   ├── inventory_history.csv   ← 149,650 records (365 days × 5 stores × 82 SKUs)
│   └── stores.json             ← Mumbai dark store coordinates
├── ml/
│   ├── demand_forecast.py      ← XGBoost model (train + predict)
│   ├── spoilage_scorer.py      ← Risk scoring engine
│   ├── transfer_optimizer.py   ← Inter-store optimization
│   ├── demand_model.pkl        ← Trained model
│   └── encoders.pkl            ← Label encoders
├── backend/
│   └── main.py                 ← FastAPI (8 endpoints)
├── frontend/
│   └── src/App.jsx             ← React dashboard (5 tabs)
├── tests/
│   └── test_all.py             ← 59 tests
└── README.md
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install fastapi uvicorn pandas numpy scikit-learn xgboost sqlalchemy python-dotenv pytest httpx faker --break-system-packages
```

### 2. Generate data + train model
```bash
python3 data/generate_data.py
python3 ml/demand_forecast.py
```

### 3. Run backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. API docs
Open: http://localhost:8000/docs

### 5. Run tests
```bash
python3 tests/test_all.py
```

### 6. Frontend
```bash
cd frontend && npm install && npm start
```

### 7. GitHub Pages (optional)
```bash
git add .
git commit -m "Redesign the page" && git push```

---

## 🌐 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/summary` | Dashboard overview metrics |
| `GET /api/stores` | All dark stores with stats |
| `GET /api/forecast?store_id=&sku_id=&days=7` | 7-day demand forecast |
| `GET /api/spoilage-alerts` | Ranked spoilage risk alerts |
| `GET /api/transfers` | Inter-store transfer recommendations |
| `GET /api/roi` | ROI calculator |
| `GET /api/waste-trend` | Historical waste trend |
| `GET /api/skus` | All SKUs with waste stats |

Full docs: **http://localhost:8000/docs** (auto-generated Swagger UI)

---

## 🧠 ML Model Details

**Algorithm:** XGBoost Regressor  
**Train/Test Split:** Time-based (Jan–Oct 2024 train, Nov–Dec 2024 test)

**Top Features by Importance:**
1. `lag_7` — Last week's sales (48.3%)
2. `rolling_7_mean` — 7-day rolling average (18.7%)
3. `day_of_week` — Day pattern (7.3%)
4. `demand_multiplier` — Festival/weekend boost (7.1%)
5. `base_demand` — Product baseline (5.8%)

---

## 💡 Why This Matters for Zepto

- Zepto lost **₹3,367 crore** in FY25 (177% YoY increase)
- Inventory wastage is a direct margin killer at their 18-22% gross margins
- They are actively hiring for **inventory forecasting + ML engineering roles**
- This project demonstrates: ML + backend + system design + **business domain understanding**

---

## 👨‍💻 Built By

**Sumit Kumar** — MCA Student, KIIT University  
Full Stack + ML Engineer  
📧 sumitranjanhisu@gmail.com  
🐙 GitHub | 💼 LinkedIn

---

*Built in 11 days. Real data. Real problem. Real solution.*
