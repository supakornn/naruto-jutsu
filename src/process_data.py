"""
Naruto Jutsu Knowledge Graph - Data Processor
Builds graph.json with rank/chakra extraction, relationship edges,
community detection, and pre-baked golden-angle layout.
"""

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

TYPE_COLORS = {
    "Ninjutsu": "#FF6B35",
    "Taijutsu": "#2E8B57",
    "Genjutsu": "#8B008B",
    "Kekkei Genkai": "#DC143C",
    "Hiden": "#4169E1",
    "Dōjutsu": "#FF0000",
    "Kenjutsu": "#C0C0C0",
    "Fūinjutsu": "#FFD700",
    "Senjutsu": "#32CD32",
    "Kinjutsu": "#800000",
    "Bukijutsu": "#708090",
    "Shurikenjutsu": "#A9A9A9",
    "Medical Ninjutsu": "#00CED1",
    "Space–Time Ninjutsu": "#9400D3",
    "Barrier Ninjutsu": "#00BFFF",
    "Clone Techniques": "#FFA500",
    "Cooperation Ninjutsu": "#ADFF2F",
    "Collaboration Techniques": "#98FB98",
    "Chakra Flow": "#00FFFF",
    "Chakra Absorption Techniques": "#FF1493",
    "Juinjutsu": "#4B0082",
    "Fighting Style": "#DAA520",
    "Shinjutsu": "#E6E6FA",
    "Scientific Ninja Tool Techniques": "#00FA9A",
    "Kekkei Mōra": "#FFFFFF",
    "General skill": "#778899",
    "Reincarnation Ninjutsu": "#483D8B",
    "Regeneration Techniques": "#7CFC00",
    "Gelel Techniques": "#FF4500",
    "Nintaijutsu": "#3CB371",
    "Jujutsu": "#B8860B",
    "Kekkei Tōta": "#FF69B4",
    "Kyūjutsu": "#D2B48C",
    "Ninshū": "#E0E0E0",
}

# Normalize variant spellings/casing to canonical names
TYPE_ALIASES: dict[str, str] = {
    "fighting style": "Fighting Style",
    "space-time ninjutsu": "Space–Time Ninjutsu",  # hyphen → en-dash
}
DEFAULT_COLOR = "#888888"

RANK_RE = re.compile(r"\b([DCBAS])-rank\b", re.IGNORECASE)

CHAKRA_RELEASES = [
    "Fire Release",
    "Wind Release",
    "Lightning Release",
    "Earth Release",
    "Water Release",
    "Yin Release",
    "Yang Release",
    "Yin–Yang Release",
    "Wood Release",
    "Ice Release",
    "Lava Release",
    "Storm Release",
    "Boil Release",
    "Magnet Release",
    "Explosion Release",
    "Scorch Release",
    "Steel Release",
    "Mud Release",
    "Swift Release",
    "Dust Release",
    "Particle Release",
]
CHAKRA_DISPLAY = {r: r.replace(" Release", "") for r in CHAKRA_RELEASES}

DERIVED_PATTERNS = [
    (re.compile(r"(?:copy|copied version|copied form) of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"based on (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"variation of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"derived from (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"similar to (?:the |a )?(.+?)(?:\.|,|$)", re.I), "similar_to"),
    (re.compile(r"stronger version of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"modified version of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"enhanced version of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"combination of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"extension of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"(?:advanced|improved|perfected) form of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"(?:technique|jutsu) (?:is )?(?:an? )?(?:alternate|alternative) (?:form|version) of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"(?:works|functions|operates) (?:similarly|in a similar (?:way|manner)) to (?:the |a )?(.+?)(?:\.|,|$)", re.I), "similar_to"),
    (re.compile(r"counterpart (?:to|of) (?:the |a )?(.+?)(?:\.|,|$)", re.I), "similar_to"),
    (re.compile(r"(?:successor|predecessor) (?:to|of) (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
    (re.compile(r"evolved? (?:form|version) of (?:the |a )?(.+?)(?:\.|,|$)", re.I), "derived_from"),
]

GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def generate_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def parse_jutsu_types(type_string: str) -> list[str]:
    if not type_string or not type_string.strip():
        return []
    result = []
    for t in type_string.split(","):
        t = t.strip()
        if t:
            result.append(TYPE_ALIASES.get(t.lower(), t))
    return result


def extract_rank(description: str) -> str | None:
    m = RANK_RE.search(description)
    return m.group(1).upper() if m else None


def extract_chakra_natures(description: str) -> list[str]:
    found = []
    for release in CHAKRA_RELEASES:
        if re.search(re.escape(release), description, re.I):
            found.append(CHAKRA_DISPLAY[release])
    return found


def load_jutsus(filepath: str | Path) -> list[dict]:
    jutsus = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jutsus.append(json.loads(line))
    return jutsus


def build_relationship_edges(jutsus: list[dict]) -> list[dict]:
    """Find derived_from / similar_to edges by pattern-matching descriptions."""
    name_to_id = {j["jutsu_name"]: f"jutsu_{generate_id(j['jutsu_name'])}" for j in jutsus}
    sorted_names = sorted(name_to_id.keys(), key=len, reverse=True)

    edges = []
    seen: set[tuple] = set()

    for jutsu in jutsus:
        src_id = name_to_id[jutsu["jutsu_name"]]
        desc = jutsu.get("jutsu_description", "")

        for pattern, rel_type in DERIVED_PATTERNS:
            for m in pattern.finditer(desc):
                match_text: str = m.group(1).strip()
                for name in sorted_names:
                    if name == jutsu["jutsu_name"]:
                        continue
                    if name.lower() in match_text.lower():
                        tgt_id = name_to_id[name]
                        key = (src_id, tgt_id, rel_type)
                        if key not in seen:
                            seen.add(key)
                            edges.append(
                                {
                                    "id": f"rel_{generate_id(src_id + tgt_id + rel_type)}",
                                    "source": src_id,
                                    "target": tgt_id,
                                    "rel": rel_type,
                                    "color": "#FFD70060",
                                }
                            )
                        break

    return edges


def assign_communities(jutsus: list[dict], rel_edges: list[dict]) -> dict[str, int]:
    """Louvain if python-louvain is available; else group by primary type."""
    node_ids = [f"jutsu_{generate_id(j['jutsu_name'])}" for j in jutsus]
    try:
        import community as community_louvain
        import networkx as nx

        G = nx.Graph()
        G.add_nodes_from(node_ids)
        for e in rel_edges:
            G.add_edge(e["source"], e["target"])
        return community_louvain.best_partition(G)
    except ImportError:
        type_list = sorted({j["jutsu_type"].split(",")[0].strip() for j in jutsus if j.get("jutsu_type")})
        return {
            f"jutsu_{generate_id(j['jutsu_name'])}": type_list.index(
                j["jutsu_type"].split(",")[0].strip()
            ) if j.get("jutsu_type") else 0
            for j in jutsus
        }


def build_graph(jutsus: list[dict]) -> dict:
    type_counts: dict[str, int] = defaultdict(int)
    for j in jutsus:
        for t in parse_jutsu_types(j.get("jutsu_type", "")):
            type_counts[t] += 1

    nodes = []
    edges = []

    type_nodes: dict[str, str] = {}
    for type_name, count in type_counts.items():
        node_id = f"type_{generate_id(type_name)}"
        type_nodes[type_name] = node_id
        nodes.append(
            {
                "id": node_id,
                "label": type_name,
                "type": "category",
                "color": TYPE_COLORS.get(type_name, DEFAULT_COLOR),
                "count": count,
                "size": min(30 + count * 0.05, 80),
                "x": 0.0,
                "y": 0.0,
            }
        )

    print("  Extracting rank / chakra from descriptions...")
    all_chakras: set[str] = set()
    all_ranks: set[str] = set()

    for j in jutsus:
        name = j.get("jutsu_name", "Unknown")
        jutsu_id = f"jutsu_{generate_id(name)}"
        types = parse_jutsu_types(j.get("jutsu_type", ""))
        primary_type = types[0] if types else None
        desc = j.get("jutsu_description", "")
        short_desc = desc[:250] + "..." if len(desc) > 250 else desc

        rank = extract_rank(desc)
        chakras = extract_chakra_natures(desc)

        if rank:
            all_ranks.add(rank)
        all_chakras.update(chakras)

        nodes.append(
            {
                "id": jutsu_id,
                "label": name,
                "type": "jutsu",
                "color": TYPE_COLORS.get(primary_type, DEFAULT_COLOR) if primary_type else DEFAULT_COLOR,
                "size": 5 + len(types) * 2,
                "jutsu_types": types,
                "rank": rank,
                "chakra_natures": chakras,
                "community": 0,
                "description": short_desc,
                "full_description": desc,
                "x": 0.0,
                "y": 0.0,
            }
        )

        for t in types:
            if t in type_nodes:
                edges.append(
                    {
                        "id": f"e_{jutsu_id}_{type_nodes[t]}",
                        "source": jutsu_id,
                        "target": type_nodes[t],
                        "rel": "type_membership",
                        "color": TYPE_COLORS.get(t, DEFAULT_COLOR) + "40",
                    }
                )

    print("  Extracting relationship edges...")
    rel_edges = build_relationship_edges(jutsus)
    print(f"  Found {len(rel_edges)} relationship edges")
    edges.extend(rel_edges)

    print("  Assigning communities...")
    communities = assign_communities(jutsus, rel_edges)
    node_by_id = {n["id"]: n for n in nodes}
    for node_id, comm in communities.items():
        if node_id in node_by_id:
            node_by_id[node_id]["community"] = comm

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_jutsus": len(jutsus),
            "total_types": len(type_counts),
            "total_rel_edges": len(rel_edges),
            "all_ranks": sorted(all_ranks),
            "all_chakras": sorted(all_chakras),
            "type_distribution": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        },
    }


def apply_layout(graph: dict) -> dict:
    """Random scatter — d3-force does the real layout at runtime."""
    import random

    rng = random.Random(42)
    for node in graph["nodes"]:
        r = 800 * math.sqrt(rng.random())
        theta = rng.random() * 2 * math.pi
        node["x"] = round(r * math.cos(theta), 3)
        node["y"] = round(r * math.sin(theta), 3)
    return graph


def main():
    input_path = Path(__file__).parent.parent / "data" / "jutsus.jsonl"
    output_path = Path(__file__).parent.parent / "frontend" / "static" / "graph_data.json"

    print(f"Loading {input_path}...")
    jutsus = load_jutsus(input_path)
    print(f"  {len(jutsus)} jutsus")

    print("Building graph...")
    graph = build_graph(jutsus)
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    print("Applying layout...")
    graph = apply_layout(graph)

    print(f"Saving to {output_path}...")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, separators=(",", ":"))

    s = graph["stats"]
    print(f"\nJutsus: {s['total_jutsus']}")
    print(f"Types: {s['total_types']}")
    print(f"Relationship edges: {s['total_rel_edges']}")
    print(f"Ranks: {s['all_ranks']}")
    print(f"Chakras: {s['all_chakras']}")


if __name__ == "__main__":
    main()
