# Naruto Jutsu Graph

Interactive knowledge graph of Naruto jutsu — built with SvelteKit + Canvas2D + d3-force.

## Stack

- **Frontend** — SvelteKit, Tailwind CSS v4, Canvas 2D renderer, d3-force simulation
- **Backend** — FastAPI (local only, for serving during development)
- **Data pipeline** — Python + uv, extracts rank/chakra/relationships from raw JSONL

## Setup

```bash
# Python (data pipeline + local server)
uv sync

# Frontend
cd frontend && npm install
```

## Data pipeline

```bash
uv run python src/process_data.py
```

Reads `data/jutsus.jsonl`, outputs `frontend/static/graph_data.json`.

## Dev

```bash
# Run frontend dev server (proxies /api to FastAPI)
cd frontend && npm run dev

# Run FastAPI backend (optional, only needed if using /api/* routes)
uv run uvicorn src.app:app --reload
```

## Deploy

Deployed on Vercel. Set **Root Directory = `frontend`** in Vercel project settings.

Every push to `main` triggers a redeploy. To update graph data, run the pipeline, commit `frontend/static/graph_data.json`, and push.
