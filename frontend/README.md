# Atlas — Country Intelligence Agent Frontend

React + Vite + TypeScript frontend for the Country AI Agent.

## Features

- **Real-time streaming** — SSE-based streaming shows tokens as they arrive
- **Agent pipeline visualization** — Live step indicators (Intent → Tool → Synthesis)
- **Multi-turn chat** — Continue asking follow-up questions across countries
- **Suggested questions** — Quick-start prompts on the empty state
- **Stop generation** — Abort in-flight streams instantly
- **Responsive** — Works on mobile and desktop

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite 5 |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v3 |
| Icons | Lucide React |
| Streaming | Native `fetch` + `ReadableStream` (SSE) |

## Getting Started

```bash
# Install dependencies
npm install

# Copy env vars
cp .env.example .env

# Start dev server (proxies /api → localhost:8000)
npm run dev
```

Make sure your backend is running on port 8000 (or update `VITE_API_URL` in `.env`).

## Backend API Contract

The frontend expects these two endpoints:

### `POST /query/stream`
**Request:**
```json
{ "question": "What is the capital of France?" }
```

**Response:** Server-Sent Events stream with `data:` lines:

```
data: {"type":"step","step":{"step":"intent","label":"Identifying intent","done":false}}
data: {"type":"step","step":{"step":"intent","label":"Identifying intent","detail":"country=France, fields=[capital]","done":true}}
data: {"type":"step","step":{"step":"tool","label":"Fetching Data","done":false}}
data: {"type":"step","step":{"step":"tool","label":"Fetching Data","detail":"GET /name/france","done":true}}
data: {"type":"step","step":{"step":"synthesis","label":"Synthesizing Answer","done":false}}
data: {"type":"token","token":"The "}
data: {"type":"token","token":"capital "}
data: {"type":"token","token":"of France is **Paris**."}
data: {"type":"step","step":{"step":"synthesis","label":"Synthesizing Answer","done":true}}
data: {"type":"done"}
data: [DONE]
```

### `POST /query` (fallback, non-streaming)
**Response:**
```json
{ "answer": "The capital of France is Paris.", "steps": [] }
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `/api` | Backend base URL (in dev, Vite proxies this) |

## Build & Deploy

```bash
# Production build
npm run build

# Preview production build locally
npm run preview
```

Deploy the `dist/` folder to any static host (Vercel, Netlify, Railway static, etc.).
Set `VITE_API_URL` to your production backend URL at build time.

### Deploy to Vercel

```bash
npx vercel --prod
# Set VITE_API_URL in Vercel dashboard → Environment Variables
```

### Deploy to Netlify

```bash
npm run build
# Drag dist/ folder to Netlify drop zone
# or connect GitHub repo and set build command: npm run build
# Set VITE_API_URL environment variable
```
