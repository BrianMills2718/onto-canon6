#!/usr/bin/env python3
"""Provenance trace report for the research_v3 → onto-canon6 → DIGIMON pipeline.

For a given entity or topic, shows the full chain:
  DIGIMON graph node → onto-canon6 candidate → source_urls (original web)

Also supports subgraph exploration: find all entities within N hops of a seed
entity, with full provenance for each.

Usage:
    python scripts/provenance_report.py --entity "Islamic Revolutionary Guard Corps"
    python scripts/provenance_report.py --entity "Iran" --hops 2
    python scripts/provenance_report.py --list-entities
    python scripts/provenance_report.py --report     # full report, all entities
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import textwrap
from pathlib import Path

import networkx as nx

# ─── Defaults ────────────────────────────────────────────────────────────────

GRAPH_PATH = Path(__file__).parent.parent / "var/iran_pipeline_run"
ENTITIES_JSONL = GRAPH_PATH / "entities.jsonl"
RELATIONSHIPS_JSONL = GRAPH_PATH / "relationships.jsonl"
SQLITE_DB = Path(__file__).parent.parent / "var/iran_demo.sqlite3"
DIGIMON_GRAPH = (
    Path(__file__).parent.parent.parent
    / "Digimon_for_KG_application/results/iran_disinformation/er_graph/nx_data.graphml"
)


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_provenance_index(
    entities_path: Path = ENTITIES_JSONL,
    relationships_path: Path = RELATIONSHIPS_JSONL,
) -> dict[str, dict]:
    """Build entity_name → provenance dict from JSONL export."""
    index: dict[str, dict] = {}
    for row in load_jsonl(entities_path):
        name = row.get("entity_name", "")
        if not name:
            continue
        raw_urls = row.get("source_urls", "[]")
        urls = json.loads(raw_urls) if isinstance(raw_urls, str) else raw_urls
        index[name] = {
            "source_candidate_id": row.get("source_candidate_id", ""),
            "source_kind": row.get("source_kind", ""),
            "source_id": row.get("source_id", ""),
            "entity_type": row.get("entity_type", ""),
            "source_urls": urls,
        }
    return index


def load_relationship_provenance(
    relationships_path: Path = RELATIONSHIPS_JSONL,
) -> dict[tuple[str, str], dict]:
    """Build (src, tgt) → provenance dict from JSONL export."""
    index: dict[tuple[str, str], dict] = {}
    for row in load_jsonl(relationships_path):
        src = row.get("src_id", "")
        tgt = row.get("tgt_id", "")
        if not src or not tgt:
            continue
        raw_urls = row.get("source_urls", "[]")
        urls = json.loads(raw_urls) if isinstance(raw_urls, str) else raw_urls
        key = (src, tgt)
        index[key] = {
            "source_candidate_id": row.get("source_candidate_id", ""),
            "source_kind": row.get("source_kind", ""),
            "relation_name": row.get("relation_name", ""),
            "description": row.get("description", ""),
            "weight": row.get("weight", 0.0),
            "source_urls": urls,
        }
    return index


def fetch_candidate_detail(db_path: Path, candidate_id: str) -> dict | None:
    """Pull full candidate record from onto-canon6 SQLite."""
    if not db_path.exists():
        return None
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT candidate_id, submitted_by, source_kind, claim_text, "
        "       source_metadata_json, validation_status, review_status, trace_id "
        "FROM candidate_assertions WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    con.close()
    if not row:
        return None
    meta = json.loads(row[4]) if row[4] else {}
    return {
        "candidate_id": row[0],
        "submitted_by": row[1],
        "source_kind": row[2],
        "claim_text": row[3],
        "source_urls": meta.get("source_urls", []),
        "confidence": meta.get("confidence"),
        "corroboration_status": meta.get("corroboration_status"),
        "validation_status": row[5],
        "review_status": row[6],
        "trace_id": row[7],
    }


def load_digimon_graph(graph_path: Path = DIGIMON_GRAPH) -> nx.Graph | None:
    """Load the DIGIMON NetworkX graph if it exists."""
    if not graph_path.exists():
        return None
    return nx.read_graphml(graph_path)


# ─── Display helpers ──────────────────────────────────────────────────────────

def fmt_urls(urls: list[str], indent: int = 6) -> str:
    pad = " " * indent
    if not urls:
        return f"{pad}(no source URLs)"
    return "\n".join(f"{pad}• {u}" for u in urls)


def fmt_wrap(text: str, width: int = 90, indent: int = 6) -> str:
    pad = " " * indent
    return textwrap.fill(text, width=width, initial_indent=pad, subsequent_indent=pad)


# ─── Report sections ──────────────────────────────────────────────────────────

def entity_provenance_block(
    name: str,
    prov: dict,
    db_path: Path,
    *,
    show_candidate: bool = True,
) -> str:
    lines = [f"  Entity: {name!r}  [{prov.get('entity_type', '')}]"]
    cid = prov.get("source_candidate_id", "")
    if cid:
        lines.append(f"    candidate_id : {cid}")
    lines.append(f"    source_kind  : {prov.get('source_kind', '')}")
    lines.append(f"    source_id    : {prov.get('source_id', '')}")
    lines.append(f"    source_urls  :")
    lines.append(fmt_urls(prov.get("source_urls", [])))

    if show_candidate and cid:
        detail = fetch_candidate_detail(db_path, cid)
        if detail:
            lines.append(f"    claim_text   :")
            lines.append(fmt_wrap(detail.get("claim_text", ""), indent=6))
            lines.append(f"    confidence   : {detail.get('confidence')}")
            lines.append(f"    corroboration: {detail.get('corroboration_status')}")
            lines.append(f"    trace_id     : {detail.get('trace_id', '')}")

    return "\n".join(lines)


def relationship_provenance_block(
    src: str,
    tgt: str,
    prov: dict,
    db_path: Path,
    *,
    show_candidate: bool = True,
) -> str:
    lines = [f"  Relationship: {src!r} → {tgt!r}"]
    lines.append(f"    relation     : {prov.get('relation_name', '')}")
    desc = prov.get("description", "")
    if desc:
        lines.append(f"    description  :")
        lines.append(fmt_wrap(desc, indent=6))
    lines.append(f"    weight       : {prov.get('weight', 0.0):.2f}")
    lines.append(f"    candidate_id : {prov.get('source_candidate_id', '')}")
    lines.append(f"    source_kind  : {prov.get('source_kind', '')}")
    lines.append(f"    source_urls  :")
    lines.append(fmt_urls(prov.get("source_urls", [])))
    return "\n".join(lines)


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_list_entities(prov_index: dict) -> None:
    print(f"\n{'─'*70}")
    print(f"  Iran Disinformation KG — {len(prov_index)} entities")
    print(f"{'─'*70}")
    for name, prov in sorted(prov_index.items()):
        url_count = len(prov.get("source_urls", []))
        etype = prov.get("entity_type", "")
        print(f"  {name:<45} {etype:<30} ({url_count} URLs)")


def cmd_entity_trace(
    entity_name: str,
    hops: int,
    prov_index: dict,
    rel_prov: dict,
    db_path: Path,
    graph: nx.Graph | None,
) -> None:
    print(f"\n{'═'*70}")
    print(f"  PROVENANCE TRACE: {entity_name!r}  (hops={hops})")
    print(f"{'═'*70}")

    if entity_name not in prov_index:
        # fuzzy match
        matches = [n for n in prov_index if entity_name.lower() in n.lower()]
        if not matches:
            print(f"  Entity not found: {entity_name!r}")
            return
        print(f"  Fuzzy matches: {matches[:5]}")
        entity_name = matches[0]
        print(f"  Using: {entity_name!r}\n")

    # Seed entity provenance
    print("\n[SEED ENTITY]")
    prov = prov_index[entity_name]
    print(entity_provenance_block(entity_name, prov, db_path))

    if graph is None or entity_name not in graph:
        print("\n  (DIGIMON graph not available or entity not in graph)")
        return

    # BFS neighborhood
    ego = nx.ego_graph(graph, entity_name, radius=hops)
    neighbors = [n for n in ego.nodes() if n != entity_name]
    print(f"\n[GRAPH NEIGHBORS — {hops}-hop, {len(neighbors)} entities]\n")

    for neighbor in sorted(neighbors):
        if neighbor in prov_index:
            print(entity_provenance_block(neighbor, prov_index[neighbor], db_path, show_candidate=False))
        else:
            print(f"  Entity: {neighbor!r}  (no provenance record)")
        print()

    # Relationships
    edges = list(ego.edges())
    print(f"\n[RELATIONSHIPS — {len(edges)} edges]\n")
    for src, tgt in edges:
        key = (src, tgt) if (src, tgt) in rel_prov else (tgt, src)
        if key in rel_prov:
            print(relationship_provenance_block(key[0], key[1], rel_prov[key], db_path))
        else:
            print(f"  {src!r} ↔ {tgt!r}  (no provenance record)")
        print()


def cmd_full_report(
    prov_index: dict,
    rel_prov: dict,
    db_path: Path,
    graph: nx.Graph | None,
) -> None:
    print(f"\n{'═'*70}")
    print(f"  FULL PROVENANCE REPORT — Iran Disinformation KG")
    print(f"  {len(prov_index)} entities · {len(rel_prov)} relationships")
    print(f"{'═'*70}\n")

    print("[ALL ENTITIES]\n")
    for name in sorted(prov_index):
        print(entity_provenance_block(name, prov_index[name], db_path, show_candidate=True))
        print()

    print(f"\n{'─'*70}")
    print("[ALL RELATIONSHIPS]\n")
    for (src, tgt), prov in sorted(rel_prov.items()):
        print(relationship_provenance_block(src, tgt, prov, db_path))
        print()

    # Graph stats
    if graph is not None:
        print(f"\n{'─'*70}")
        print(f"[DIGIMON GRAPH STATS]")
        print(f"  Nodes : {graph.number_of_nodes()}")
        print(f"  Edges : {graph.number_of_edges()}")
        # Most connected nodes
        degrees = sorted(graph.degree(), key=lambda x: x[1], reverse=True)[:10]
        print(f"  Most connected entities:")
        for node, deg in degrees:
            print(f"    {node:<45} degree={deg}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provenance trace: DIGIMON graph → onto-canon6 → source URLs"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--entity", help="Entity name to trace (fuzzy match supported)")
    group.add_argument("--list-entities", action="store_true", help="List all entities")
    group.add_argument("--report", action="store_true", help="Full provenance report")
    parser.add_argument("--hops", type=int, default=1, help="Graph neighborhood hops (default: 1)")
    parser.add_argument("--graph-dir", type=Path, default=GRAPH_PATH, help="Override pipeline run dir")
    parser.add_argument("--db", type=Path, default=SQLITE_DB, help="Override SQLite db path")
    parser.add_argument("--digimon-graph", type=Path, default=DIGIMON_GRAPH, help="Override DIGIMON graphml path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    entities_path = args.graph_dir / "entities.jsonl"
    relationships_path = args.graph_dir / "relationships.jsonl"

    prov_index = load_provenance_index(entities_path, relationships_path)
    rel_prov = load_relationship_provenance(relationships_path)
    graph = load_digimon_graph(args.digimon_graph)

    if args.list_entities:
        cmd_list_entities(prov_index)
    elif args.entity:
        cmd_entity_trace(args.entity, args.hops, prov_index, rel_prov, args.db, graph)
    elif args.report:
        cmd_full_report(prov_index, rel_prov, args.db, graph)


if __name__ == "__main__":
    main()
