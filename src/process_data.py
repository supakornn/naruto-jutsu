"""
Naruto Jutsu Knowledge Graph - Data Processor
Parses jutsus.jsonl and creates graph structure for visualization
"""

import json
import hashlib
from pathlib import Path
from collections import defaultdict

# Color palette for jutsu types (Naruto-themed)
TYPE_COLORS = {
    "Ninjutsu": "#FF6B35",  # Orange (Naruto's color)
    "Taijutsu": "#2E8B57",  # Sea green (Rock Lee)
    "Genjutsu": "#8B008B",  # Dark magenta (Itachi)
    "Kekkei Genkai": "#DC143C",  # Crimson (Sharingan)
    "Hiden": "#4169E1",  # Royal blue
    "Dōjutsu": "#FF0000",  # Red (eyes)
    "Kenjutsu": "#C0C0C0",  # Silver (swords)
    "Fūinjutsu": "#FFD700",  # Gold (seals)
    "Senjutsu": "#32CD32",  # Lime green (nature)
    "Kinjutsu": "#800000",  # Maroon (forbidden)
    "Bukijutsu": "#708090",  # Slate gray
    "Shurikenjutsu": "#A9A9A9",  # Dark gray
    "Medical Ninjutsu": "#00CED1",  # Dark turquoise (Tsunade)
    "Space–Time Ninjutsu": "#9400D3",  # Dark violet
    "Barrier Ninjutsu": "#00BFFF",  # Deep sky blue
    "Clone Techniques": "#FFA500",  # Orange
    "Cooperation Ninjutsu": "#ADFF2F",  # Green yellow
    "Collaboration Techniques": "#98FB98",  # Pale green
    "Chakra Flow": "#00FFFF",  # Cyan
    "Chakra Absorption Techniques": "#FF1493",  # Deep pink
    "Juinjutsu": "#4B0082",  # Indigo (curse marks)
    "Fighting Style": "#DAA520",  # Goldenrod
    "Shinjutsu": "#E6E6FA",  # Lavender
    "Scientific Ninja Tool Techniques": "#00FA9A",  # Medium spring green
    "Kekkei Mōra": "#FFFFFF",  # White (Kaguya)
    "General skill": "#778899",  # Light slate gray
    "Reincarnation Ninjutsu": "#483D8B",  # Dark slate blue
    "Regeneration Techniques": "#7CFC00",  # Lawn green
    "Gelel Techniques": "#FF4500",  # Orange red
}

DEFAULT_COLOR = "#888888"


def generate_id(text: str) -> str:
    """Generate a short unique ID from text"""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def parse_jutsu_types(type_string: str) -> list[str]:
    """Parse comma-separated jutsu types into list"""
    if not type_string or type_string.strip() == "":
        return ["Unknown"]

    types = [t.strip() for t in type_string.split(",")]
    return [t for t in types if t]  # Filter empty strings


def load_jutsus(filepath: str | Path) -> list[dict]:
    """Load jutsus from JSONL file"""
    jutsus = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jutsus.append(json.loads(line))
    return jutsus


def build_graph(jutsus: list[dict]) -> dict:
    """
    Build graph structure with:
    - Type nodes (large hubs)
    - Jutsu nodes (smaller)
    - Edges connecting jutsus to their types
    """
    nodes = []
    edges = []
    type_counts = defaultdict(int)

    # First pass: count types for sizing
    for jutsu in jutsus:
        types = parse_jutsu_types(jutsu.get("jutsu_type", ""))
        for t in types:
            type_counts[t] += 1

    # Create type nodes (hubs)
    type_nodes = {}
    for type_name, count in type_counts.items():
        node_id = f"type_{generate_id(type_name)}"
        type_nodes[type_name] = node_id
        nodes.append(
            {
                "id": node_id,
                "label": type_name,
                "size": min(30 + count * 0.05, 80),  # Scale size by count
                "color": TYPE_COLORS.get(type_name, DEFAULT_COLOR),
                "type": "category",
                "count": count,
                "x": 0,  # Will be positioned by layout
                "y": 0,
            }
        )

    # Create jutsu nodes and edges
    for jutsu in jutsus:
        jutsu_name = jutsu.get("jutsu_name", "Unknown")
        jutsu_id = f"jutsu_{generate_id(jutsu_name)}"
        types = parse_jutsu_types(jutsu.get("jutsu_type", ""))
        primary_type = types[0] if types else "Unknown"

        # Truncate description for display
        description = jutsu.get("jutsu_description", "")
        short_desc = (
            description[:200] + "..." if len(description) > 200 else description
        )

        nodes.append(
            {
                "id": jutsu_id,
                "label": jutsu_name,
                "size": 5 + len(types) * 2,  # Bigger if multi-type
                "color": TYPE_COLORS.get(primary_type, DEFAULT_COLOR),
                "type": "jutsu",
                "jutsu_types": types,
                "description": short_desc,
                "full_description": description,
                "x": 0,
                "y": 0,
            }
        )

        # Create edges to each type
        for t in types:
            if t in type_nodes:
                edges.append(
                    {
                        "id": f"edge_{jutsu_id}_{type_nodes[t]}",
                        "source": jutsu_id,
                        "target": type_nodes[t],
                        "size": 1,
                        "color": TYPE_COLORS.get(t, DEFAULT_COLOR)
                        + "40",  # Semi-transparent
                    }
                )

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_jutsus": len(jutsus),
            "total_types": len(type_counts),
            "type_distribution": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        },
    }


def apply_layout(graph: dict) -> dict:
    """Apply initial positions using circular layout for types"""
    import math

    # Position type nodes in a circle
    type_nodes = [n for n in graph["nodes"] if n["type"] == "category"]
    num_types = len(type_nodes)

    for i, node in enumerate(type_nodes):
        angle = (2 * math.pi * i) / num_types
        radius = 500
        node["x"] = radius * math.cos(angle)
        node["y"] = radius * math.sin(angle)

    # Position jutsu nodes near their primary type
    type_positions = {n["label"]: (n["x"], n["y"]) for n in type_nodes}

    jutsu_nodes = [n for n in graph["nodes"] if n["type"] == "jutsu"]
    type_jutsu_count = defaultdict(int)

    for node in jutsu_nodes:
        primary_type = node["jutsu_types"][0] if node["jutsu_types"] else "Unknown"
        if primary_type in type_positions:
            base_x, base_y = type_positions[primary_type]
            count = type_jutsu_count[primary_type]

            # Spiral outward from type center
            angle = count * 0.3
            distance = 50 + count * 0.5
            node["x"] = base_x + distance * math.cos(angle)
            node["y"] = base_y + distance * math.sin(angle)

            type_jutsu_count[primary_type] += 1
        else:
            node["x"] = 0
            node["y"] = 0

    return graph


def main():
    """Main processing function"""
    # Paths
    input_path = Path(__file__).parent.parent / "jutsus.jsonl"
    output_path = Path(__file__).parent.parent / "data" / "graph_data.json"

    print(f"📖 Loading jutsus from {input_path}...")
    jutsus = load_jutsus(input_path)
    print(f"   Found {len(jutsus)} jutsus")

    print("🔨 Building graph structure...")
    graph = build_graph(jutsus)
    print(f"   Created {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")

    print("📐 Applying initial layout...")
    graph = apply_layout(graph)

    print(f"💾 Saving to {output_path}...")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False)

    print("\n📊 Stats:")
    print(f"   Total jutsus: {graph['stats']['total_jutsus']}")
    print(f"   Total types: {graph['stats']['total_types']}")
    print("\n   Top 10 types:")
    for type_name, count in list(graph["stats"]["type_distribution"].items())[:10]:
        print(f"   - {type_name}: {count}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
