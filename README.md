# 🚀 FinAnalysis — AI-Powered Financial Analysis Tool for Indian Markets

> **Team Code Conquerors** | Sardar Patel Institute of Technology, Mumbai  
> Aarushi Ghosh • Aryan Shewale • Vivek Yadav • Vidhi Gond

---

## 📌 Project Overview

An AI-powered financial analysis platform for Indian retail investors using a **multi-agent architecture**.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, React, Tailwind CSS, Chart.js |
| **Backend API** | Node.js 20, Express.js, MongoDB (Mongoose) |
| **AI Service** | Python 3.11, FastAPI |
| **Agent Framework** | **AutoGen v0.7** (Microsoft) |
| **LLM** | **Gemini 1.5 Pro** (macro) / **Gemini 1.5 Flash** (micro) |
| **Embeddings** | **Gemini text-embedding-004** |
| **OCR** | **Mistral OCR** |
| **Vector DB** | **ChromaDB** (persistent, local) |
| **Database** | **MongoDB** (user data + JSON chunks) |
| **Stock Data** | **yfinance** (NSE/BSE) |
| **Deployment** | Docker, Docker Compose |

---

## 🏗️ Architecture

```
INPUT DOCUMENTS (PDF)
  Annual Reports, Concall Transcripts, Fund Reports
          │
          ▼
    ┌─────────────┐      ┌─────────────────────┐
    │ Mistral OCR  │────▶ │ JSON Chunks         │
    └─────────────┘      │ MongoDB              │
                         └──────────┬──────────┘
    ┌─────────────┐                 │
    │  yfinance   │                 ▼
    │ NSE/BSE data│       ┌─────────────────────┐
    └──────┬──────┘       │ Gemini Embeddings    │
           │              │ → ChromaDB Vectors   │
           │              └──────────┬──────────┘
           └──────────┬──────────────┘
                      ▼
      ┌─────────────────────────────────────────┐
      │         AUTOGEN v0.7 AGENTS             │
      │  ┌─────────────────────────────────┐   │
      │  │  Tools: Y Finance | Vector RAG  │   │
      │  │         Arithmetic | Reasoning  │   │
      │  └──────────────┬──────────────────┘   │
      │  MACRO (Gemini 1.5 Pro):                │
      │    Business | Financial | Market | Risk │
      │  MICRO (Gemini 1.5 Flash):              │
      │    Valuation | Profitability | Liquidity│
      │    Leverage | Efficiency | News         │
      │    Historical | Guidance | Sentiment    │
      │    Financial Metrics                    │
      └─────────────────────────────────────────┘
                      │
                      ▼
           Dashboard | PDF Report | Excel
```

---

## � Project Structure

```
ET_phase2/
├── backend/                    # Node.js + Express (Port 5000)
│   ├── src/
│   │   ├── agents/
│   │   ├── config/database.js
│   │   ├── controllers/
│   │   ├── middleware/auth.js
│   │   ├── models/User.js
│   │   ├── routes/
│   │   ├── utils/ (jwt.js, logger.js)
│   │   ├── app.js
│   │   └── server.js
│   ├── .env
│   └── package.json
│
├── ai-service/                 # FastAPI + AutoGen (Port 8000)
│   ├── app/
│   │   ├── agents/
│   │   │   ├── macro/          # Business, Financial, Market, Risk
│   │   │   └── micro/          # 10 micro-agents
│   │   ├── tools/              # yfinance, RAG, arithmetic
│   │   ├── services/
│   │   │   ├── ocr/            # Mistral OCR
│   │   │   ├── vector_store/   # ChromaDB + Gemini embeddings
│   │   │   └── mongo/          # Motor async MongoDB
│   │   ├── api/                # FastAPI routers
│   │   ├── config/settings.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/                   # Next.js 14 (Port 3000 — Part 5)
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- MongoDB running locally OR MongoDB Atlas URI
- API Keys: Google Gemini (free) + Mistral (free tier)

---

### Step 1 — Get API Keys
1. **Google Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — FREE
2. **Mistral**: [console.mistral.ai](https://console.mistral.ai) — Free tier available

---

### Step 2 — Backend Setup

```bash
cd backend
setup.bat          # OR: npm install && mkdir logs
```

Add your config to `backend/.env` (already created with defaults).

```bash
npm run dev
# ✅ Backend running at http://localhost:5000
# ✅ Health: http://localhost:5000/health
```

---

### Step 3 — AI Service Setup

```bash
cd ai-service
setup.bat           # Creates venv + installs all deps
```

Add your **Gemini** and **Mistral** API keys to `ai-service/.env`:
```
GOOGLE_API_KEY=AIza...
MISTRAL_API_KEY=...
```

```bash
venv\Scripts\activate
python main.py
# ✅ AI Service at http://localhost:8000
# ✅ Swagger docs: http://localhost:8000/docs
```

---

### (Optional) Docker Compose

```bash
# Set your API keys in docker-compose.yml or a .env file
docker-compose up -d mongodb backend ai-service
```

---

## 📡 API Reference

### Backend — Node.js (Port 5000)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register user |
| POST | `/api/auth/login` | ❌ | Login + get JWT |
| POST | `/api/auth/refresh` | ❌ | Refresh token |
| GET | `/api/auth/me` | ✅ | Get current user |
| GET | `/api/watchlist` | ✅ | User's watchlist |
| POST | `/api/watchlist` | ✅ | Add stock |
| DELETE | `/api/watchlist/:symbol` | ✅ | Remove stock |

### AI Service — FastAPI (Port 8000)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stocks/{symbol}` | Live stock data |
| GET | `/api/v1/stocks/{symbol}/history` | OHLCV history |
| GET | `/api/v1/stocks/{symbol}/financials` | P&L, BS, CF |
| GET | `/api/v1/stocks/compare/peers?symbols=...` | Peer comparison |
| POST | `/api/v1/documents/upload` | Upload PDF (OCR pipeline) |
| GET | `/api/v1/documents/{id}/status` | Pipeline status |
| POST | `/api/v1/analysis/rag-query` | Document Q&A |
| POST | `/api/v1/analysis/micro/{agent_type}` | Single micro-agent |
| POST | `/api/v1/analysis/micro/all/{symbol}` | All 10 micro-agents |
| POST | `/api/v1/analysis/macro/{symbol}` | All 4 macro-agents |
| POST | `/api/v1/analysis/full/{symbol}` | Complete analysis |

> **Swagger UI**: http://localhost:8000/docs

---

## 🤖 AutoGen Agents

### Macro Agents (Gemini 1.5 Pro)
| Agent | Role |
|---|---|
| Business Agent | Business model, moat, strategy |
| Financial Agent | P&L, ratios, balance sheet |
| Market Agent | Price action, technicals, sector |
| Risk Agent | All risk factors |

### Micro Agents (Gemini 1.5 Flash)
| Agent | Metrics |
|---|---|
| Valuation | P/E, P/B, EV/EBITDA |
| Profitability | ROE, ROCE, margins |
| Liquidity | Current Ratio, Quick Ratio |
| Leverage | D/E, Interest Coverage |
| Efficiency | Asset Turnover, Inventory Days |
| News | Recent corporate news |
| Historical | Price returns and CAGR |
| Guidance | Concall management guidance |
| Sentiment | Aggregated sentiment score |
| Financial Metrics | Complete metrics table |

---

## 🏗️ Build Status

| Phase | Status | Description |
|---|---|---|
| **Part 1** | ✅ Done | Node.js Auth, MongoDB, Docker |
| **Part 1b** | ✅ Done | AutoGen + Gemini + ChromaDB + Mistral OCR |
| **Part 2** | 🔲 Next | Node.js stock proxy routes + caching |
| **Part 3** | 🔲 | Agent testing + output refinement |
| **Part 4** | 🔲 | Frontend Dashboard (Next.js) |
| **Part 5** | 🔲 | AI Chatbot + PDF/Excel export |
| **Part 6** | 🔲 | Docker production + deployment |
