# 🚀 FinAnalysis AI — Financial Intelligence for Indian Markets

> **Team Code Conquerors** | Sardar Patel Institute of Technology, Mumbai
> Aarushi Ghosh • Aryan Shewale • Vivek Yadav • Vidhi Gond

---

## 📌 Overview

An AI-powered financial analysis platform for Indian retail investors built on a **multi-agent AutoGen architecture** using Gemini 2.0, ChromaDB, Mistral OCR, and live NSE/BSE market data.

Upload annual reports → AI extracts, embeds, and analyzes → Get institutional-grade equity research in seconds.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js, Vite, Vanilla CSS (Dark Glassmorphism), Chart.js |
| **Backend API** | Node.js 20, Express.js, MongoDB (Mongoose) |
| **AI Service** | Python 3.11, FastAPI |
| **Agent Framework** | AutoGen v0.7 (Microsoft) |
| **LLM** | Gemini 2.0 Flash (macro + micro agents) |
| **Embeddings** | Gemini `text-embedding-004` |
| **OCR** | Mistral OCR (`mistral-ocr-latest`) |
| **Vector DB** | ChromaDB (persistent, local) |
| **Database** | MongoDB Atlas (user data + document chunks) |
| **Stock Data** | yfinance (NSE/BSE live + historical) |
| **Deployment** | Docker, Docker Compose |

---

## 🏗️ Architecture

```
PDF Documents (Annual Reports, Concall Transcripts, Fund Reports)
        │
        ▼
  ┌─────────────┐      ┌─────────────────────┐
  │ Mistral OCR  │────▶ │  JSON Chunks         │
  └─────────────┘      │  MongoDB Atlas        │
                       └──────────┬──────────┘
  ┌─────────────┐                 │
  │  yfinance   │                 ▼
  │ NSE/BSE data│       ┌─────────────────────┐
  └──────┬──────┘       │  Gemini Embeddings   │
         │              │  → ChromaDB Vectors  │
         │              └──────────┬──────────┘
         └──────────┬──────────────┘
                    ▼
    ┌─────────────────────────────────────────┐
    │         AUTOGEN v0.7 AGENTS             │
    │  Tools: YFinance | Vector RAG           │
    │         Arithmetic | Reasoning (Gemini) │
    │  ─────────────────────────────────────  │
    │  MACRO Agents (Gemini 2.0 Flash):       │
    │    Business | Financial | Market | Risk │
    │  ─────────────────────────────────────  │
    │  MICRO Agents (Gemini 2.0 Flash Lite):  │
    │    Valuation | Profitability | Liquidity│
    │    Leverage | Efficiency | News         │
    │    Historical | Guidance | Sentiment    │
    │    Financial Metrics                    │
    └─────────────────────────────────────────┘
                    │
                    ▼
         React Dashboard | PDF Report
```

---

## 📁 Project Structure

```
ET_phase2/
├── backend/                    # Node.js + Express (Port 5000)
│   ├── src/
│   │   ├── controllers/        # auth, watchlist, stock proxy
│   │   ├── middleware/auth.js  # JWT verification
│   │   ├── models/User.js      # MongoDB user + watchlist
│   │   ├── routes/             # auth, watchlist, stocks
│   │   ├── utils/              # jwt.js, logger.js
│   │   ├── app.js
│   │   └── server.js
│   ├── .env
│   └── package.json
│
├── ai-service/                 # FastAPI + AutoGen (Port 8000)
│   ├── app/
│   │   ├── agents/
│   │   │   ├── macro/          # Business, Financial, Market, Risk agents
│   │   │   └── micro/          # 10 specialized micro-agents
│   │   ├── tools/              # yfinance_tool, vector_rag_tool, arithmetic_tool, reasoning_tool
│   │   ├── services/
│   │   │   ├── ocr/            # Mistral OCR pipeline
│   │   │   ├── vector_store/   # ChromaDB + Gemini embeddings
│   │   │   └── mongo/          # Motor async MongoDB
│   │   ├── api/                # stocks, analysis, documents, reasoning routers
│   │   ├── config/settings.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/                   # React + Vite (Port 3000)
│   ├── src/
│   │   ├── context/            # AuthContext, StockContext
│   │   ├── components/layout/  # Sidebar, Navbar, Layout
│   │   ├── pages/
│   │   │   ├── Auth/           # Login, Register
│   │   │   ├── Dashboard/      # Market overview + watchlist table
│   │   │   ├── Stock/          # Detail: Charts + Metrics + AI analysis
│   │   │   ├── Watchlist/      # Personal tracked stocks
│   │   │   ├── Documents/      # PDF upload + pipeline status
│   │   │   └── Ask/            # AI chat interface
│   │   ├── services/api.js     # Axios client + JWT interceptors
│   │   └── index.css           # Design system (dark glassmorphism)
│   └── package.json
│
├── docker/mongo-init.js
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- MongoDB Atlas URI (free tier at [cloud.mongodb.com](https://cloud.mongodb.com))
- API Keys: [Google Gemini](https://aistudio.google.com/apikey) (free) + [Mistral](https://console.mistral.ai) (free tier)

---

### 1. AI Service (FastAPI + AutoGen)

```bash
cd ai-service
setup.bat              # Creates venv + installs dependencies
```

Set your keys in `ai-service/.env`:
```env
GOOGLE_API_KEY=AIza...
MISTRAL_API_KEY=...
MONGODB_URI=mongodb+srv://...
```

```bash
venv\Scripts\activate
python main.py
# ✅ AI Service → http://localhost:8000
# ✅ Swagger UI → http://localhost:8000/docs
```

---

### 2. Backend (Node.js + Express)

```bash
cd backend
npm install
```

Set your keys in `backend/.env`:
```env
MONGODB_URI=mongodb+srv://...
JWT_SECRET=your_secure_secret
AI_SERVICE_URL=http://localhost:8000
```

```bash
npm run dev
# ✅ Backend → http://localhost:5000
```

---

### 3. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# ✅ Frontend → http://localhost:3000
```

---

### Optional: Docker Compose

```bash
docker-compose up -d
```

---

## 📡 API Reference

### Backend — Node.js (Port 5000)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register user |
| POST | `/api/auth/login` | ❌ | Login → JWT token |
| GET | `/api/auth/me` | ✅ | Get current user |
| GET | `/api/watchlist` | ✅ | User's watchlist |
| POST | `/api/watchlist` | ✅ | Add stock |
| DELETE | `/api/watchlist/:symbol` | ✅ | Remove stock |
| GET | `/api/stocks/:symbol` | ❌ | Live stock data (proxied) |
| GET | `/api/stocks/:symbol/history` | ❌ | OHLCV chart data |
| GET | `/api/stocks/:symbol/thesis` | ✅ | AI investment thesis |
| GET | `/api/stocks/:symbol/risk` | ✅ | AI risk assessment |
| POST | `/api/stocks/ask` | ✅ | Free-form AI Q&A |

### AI Service — FastAPI (Port 8000)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stocks/{symbol}` | Live stock info |
| GET | `/api/v1/stocks/{symbol}/history` | OHLCV history |
| GET | `/api/v1/stocks/{symbol}/financials` | P&L, BS, CF |
| POST | `/api/v1/documents/upload` | PDF → OCR → MongoDB → ChromaDB |
| POST | `/api/v1/analysis/micro/{agent_type}` | Single micro-agent run |
| POST | `/api/v1/analysis/full/{symbol}` | All 14 agents (full report) |
| POST | `/api/v1/reasoning/investment-thesis/{symbol}` | Investment thesis |
| POST | `/api/v1/reasoning/compare` | Compare multiple stocks |
| POST | `/api/v1/reasoning/risk/{symbol}` | Risk score 1–10 |
| POST | `/api/v1/reasoning/ask` | Custom financial Q&A |

> 📘 **Swagger UI**: http://localhost:8000/docs

---

## 🤖 AutoGen Agents

### Macro Agents (Gemini 2.0 Flash)
| Agent | Focus |
|---|---|
| Business Agent | Business model, moat, strategy analysis |
| Financial Agent | P&L deep-dive, ratio analysis |
| Market Agent | Price action, technicals, sector positioning |
| Risk Agent | Business, financial, regulatory risks |

### Micro Agents (Gemini 2.0 Flash Lite)
| Agent | Key Metrics |
|---|---|
| Valuation | P/E, P/B, EV/EBITDA, DCF |
| Profitability | ROE, ROCE, gross/net margins |
| Liquidity | Current Ratio, Quick Ratio, Cash Flow |
| Leverage | D/E, Interest Coverage, Net Debt/EBITDA |
| Efficiency | Asset Turnover, Inventory Days, CCC |
| News | Recent corporate announcements & sentiment |
| Historical | 1M–5Y returns, CAGR vs Nifty 50 |
| Guidance | Concall transcript management commentary |
| Sentiment | Bull/bear sentiment aggregation |
| Financial Metrics | Full metrics table with industry benchmarks |

---

## ✅ Build Status

| Phase | Status | Description |
|---|---|---|
| **Part 1** | ✅ Done | Node.js Auth, MongoDB, Docker |
| **Part 1b** | ✅ Done | AutoGen v0.7 + Gemini + ChromaDB + Mistral OCR |
| **Part 2** | ✅ Done | AutoGen Tools + Reasoning Engine + Node.js Stock Proxy |
| **Part 3** | ✅ Done | React Frontend — Dashboard, Charts, AI Analysis, Chat |
| **Part 4** | 🔲 Next | PDF/Excel report export |
| **Part 5** | 🔲 | Docker production build + deployment |
