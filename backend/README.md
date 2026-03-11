# Vishwa — Country Information AI Agent

A production-grade LangGraph agent that answers natural-language questions
about countries using live data from the REST Countries API.

## Architecture

```
app/
├── main.py                  # FastAPI app — POST /query
├── schemas.py               # Pydantic request/response models
├── agent/
│   ├── graph.py             # LangGraph StateGraph
│   ├── nodes.py             # Node 1: intent, Node 2: tool, Node 3: synthesis
│   ├── state.py             # AgentState TypedDict
│   └── tools.py             # REST Countries API client (httpx)
└── providers/
    ├── __init__.py          # exposes get_llm()
    └── factory.py           # reads LLM_PROVIDER, returns LangChain BaseChatModel
```

### Agent pipeline
```
identify_intent → invoke_tool → synthesise_answer → END
     (LLM)           (HTTP)          (LLM)
```

## LLM Providers

Set `LLM_PROVIDER` in `.env`:

| Value        | LangChain class | Required env vars                                          |
|--------------|-----------------|------------------------------------------------------------|
| `groq`       | `ChatGroq`      | `GROQ_API_KEY`                                             |
| `bedrock`    | `ChatBedrock`   | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `openrouter` | `ChatOpenAI`    | `OPENROUTER_API_KEY`                                       |

All providers use standard LangChain `.ainvoke()` — swapping requires only a `.env` change.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env    # set LLM_PROVIDER + API key
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the interactive Swagger UI.

## API

### `POST /query`
```json
// Request
{ "question": "What is the capital of Japan?" }

// Response
{ "answer": "The capital of Japan is Tokyo.", "country": "Japan", "fields": ["capital"] }
```

### `GET /health` → `{ "status": "ok" }`
### `GET /info`   → `{ "app": "Vishwa", "provider": "groq", ... }`

## Tests

```bash
pytest tests/ -v
# No API keys needed — all LLM and HTTP calls are mocked
```

## Deployment

```bash
# Railway
railway up

# Docker
docker build -t vishwa .
docker run -p 8000:8000 --env-file .env vishwa
```
