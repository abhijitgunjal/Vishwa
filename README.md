# Vishwa — Country Intelligence Agent

Vishwa is a full-stack AI agent that answers natural-language questions about countries. Ask it anything — population, capital, currency, languages, area — and it returns a grounded, factual answer powered by live data.

```
"What is the population of Germany?"       →  Germany has a population of ~84 million.
"What currency does Japan use?"            →  Japan uses the Japanese Yen (¥).
"Tell me about Brazil — capital and area"  →  The capital is Brasília. Brazil covers 8,515,767 km².
```

---

## How it works

Every question passes through a three-step LangGraph pipeline:

```
User question
      │
      ▼
┌─────────────────┐
│  identify_intent │  LLM extracts country name + requested fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   invoke_tool   │  Fetches live data from restcountries.com
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│synthesise_answer│  LLM composes a clear, factual answer
└────────┬────────┘
         │
         ▼
      Answer
```

---

## Project structure

```
vishwa/
├── backend/                   # FastAPI + LangGraph agent
│   ├── app/
│   │   ├── main.py            # API entry point (POST /query)
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── agent/
│   │   │   ├── graph.py       # LangGraph StateGraph
│   │   │   ├── nodes.py       # The three pipeline nodes
│   │   │   ├── state.py       # AgentState TypedDict
│   │   │   └── tools.py       # REST Countries API client
│   │   └── providers/
│   │       ├── __init__.py
│   │       └── factory.py     # Pluggable LLM backend (Groq / Bedrock / OpenRouter)
│   ├── tests/
│   │   └── test_agent.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
└── frontend/                  # React + Vite + TypeScript chat UI
    ├── src/
    │   ├── App.tsx
    │   ├── components/        # Header, MessageBubble, ChatInput, EmptyState…
    │   ├── hooks/
    │   │   └── useChat.ts     # All chat state management
    │   ├── lib/
    │   │   └── api.ts         # Backend fetch client
    │   └── types/index.ts
    ├── package.json
    └── .env.example
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend framework | React 18 + Vite 5 + TypeScript |
| Styling | Tailwind CSS |
| Backend framework | FastAPI + Uvicorn |
| Agent framework | LangGraph |
| LLM abstraction | LangChain (`BaseChatModel`) |
| Country data | REST Countries API (public, no auth) |
| LLM providers | Groq · AWS Bedrock · OpenRouter |

---

## LLM providers

Vishwa supports three LLM backends. Switch between them by changing a single env var — no code changes required.

| `LLM_PROVIDER` | LangChain class | Requires |
|---|---|---|
| `groq` | `ChatGroq` | `GROQ_API_KEY` |
| `bedrock` | `ChatBedrock` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `openrouter` | `ChatOpenAI` | `OPENROUTER_API_KEY` |

---

## Getting started

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # set LLM_PROVIDER and your API key
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**. Visit `/docs` for the interactive Swagger UI.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL defaults to /api (proxied to localhost:8000)
npm run dev
```

Frontend runs at **http://localhost:5173**.

---

## API

### `POST /query`

```jsonc
// Request
{ "question": "What languages are spoken in Switzerland?" }

// Response
{
  "answer": "Switzerland has four official languages: German, French, Italian, and Romansh.",
  "country": "Switzerland",
  "fields": ["languages"]
}
```

### `GET /health` — liveness probe
### `GET /info` — active provider and model info

---

## Running tests

```bash
cd backend
pytest tests/ -v
```

All LLM and HTTP calls are mocked — no API keys needed to run the test suite.

---
