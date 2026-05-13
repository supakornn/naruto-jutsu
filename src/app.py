import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Naruto Jutsu Graph")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "frontend" / "build"

_graph_cache = None


def get_graph_data():
    global _graph_cache
    if _graph_cache is None:
        p = DATA_DIR / "graph_data.json"
        _graph_cache = (
            json.loads(p.read_text(encoding="utf-8"))
            if p.exists()
            else {"nodes": [], "edges": [], "stats": {}}
        )
    return _graph_cache


@app.get("/api/graph")
async def get_graph():
    return JSONResponse(get_graph_data())


@app.get("/api/stats")
async def get_stats():
    return JSONResponse(get_graph_data().get("stats", {}))


@app.get("/api/search/{query}")
async def search_jutsu(query: str):
    data = get_graph_data()
    ql = query.lower()
    results = [n for n in data["nodes"] if n["type"] == "jutsu" and ql in n["label"].lower()]
    return JSONResponse({"results": results[:50]})


# Serve SvelteKit build (web/ directory) — must come last
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
