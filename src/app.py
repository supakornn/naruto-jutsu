"""
Naruto Jutsu Knowledge Graph - FastAPI Server
Serves the graph data and static web files
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json

app = FastAPI(
    title="Naruto Jutsu Graph", description="Knowledge graph of Naruto jutsus"
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"

# Cache graph data
_graph_cache = None


def get_graph_data():
    """Load and cache graph data"""
    global _graph_cache
    if _graph_cache is None:
        graph_path = DATA_DIR / "graph_data.json"
        if graph_path.exists():
            with open(graph_path, "r", encoding="utf-8") as f:
                _graph_cache = json.load(f)
        else:
            _graph_cache = {"nodes": [], "edges": [], "stats": {}}
    return _graph_cache


@app.get("/")
async def index():
    """Serve the main page"""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/graph")
async def get_graph():
    """Get full graph data"""
    return JSONResponse(get_graph_data())


@app.get("/api/stats")
async def get_stats():
    """Get graph statistics"""
    data = get_graph_data()
    return JSONResponse(data.get("stats", {}))


@app.get("/api/search/{query}")
async def search_jutsu(query: str):
    """Search jutsus by name"""
    data = get_graph_data()
    query_lower = query.lower()

    results = [
        node
        for node in data["nodes"]
        if node["type"] == "jutsu" and query_lower in node["label"].lower()
    ]

    return JSONResponse({"results": results[:50]})  # Limit results


@app.get("/api/type/{type_name}")
async def get_by_type(type_name: str):
    """Get all jutsus of a specific type"""
    data = get_graph_data()

    results = [
        node
        for node in data["nodes"]
        if node["type"] == "jutsu" and type_name in node.get("jutsu_types", [])
    ]

    return JSONResponse({"type": type_name, "count": len(results), "jutsus": results})


# Mount static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
