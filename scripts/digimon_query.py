#!/usr/bin/env python3
"""Query the Iran disinformation DIGIMON graph with provenance.

Demonstrates end-to-end: research_v3 → onto-canon6 → DIGIMON graph retrieval.
For a natural-language research question, finds relevant entities, expands the
subgraph, and traces every fact back to its source URL.

This uses DIGIMON's imported graph (NetworkX) with graph operators (PPR-style
traversal, ego networks) without requiring the full DIGIMON LLM agent setup.

Usage:
    python scripts/digimon_query.py --query "Iran influence operations on social media"
    python scripts/digimon_query.py --query "APT42 phishing campaigns"
    python scripts/digimon_query.py --query "Soleimani assassination reaction"
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import networkx as nx

# ─── Paths ────────────────────────────────────────────────────────────────────

DIGIMON_GRAPH = (
    Path(__file__).parent.parent.parent
    / "Digimon_for_KG_application/results/iran_disinformation/er_graph/nx_data.graphml"
)
ENTITIES_JSONL = Path(__file__).parent.parent / "var/iran_pipeline_run/entities.jsonl"
RELATIONSHIPS_JSONL = Path(__file__).parent.parent / "var/iran_pipeline_run/relationships.jsonl"
SQLITE_DB = Path(__file__).parent.parent / "var/iran_demo.sqlite3"


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_provenance_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(ENTITIES_JSONL):
        name = row.get("entity_name", "")
        if not name:
            continue
        raw_urls = row.get("source_urls", "[]")
        urls = json.loads(raw_urls) if isinstance(raw_urls, str) else raw_urls
        index[name] = {
            "candidate_id": row.get("source_candidate_id", ""),
            "source_kind": row.get("source_kind", ""),
            "entity_type": row.get("entity_type", ""),
            "source_urls": urls,
        }
    return index


def build_relationship_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(RELATIONSHIPS_JSONL):
        src, tgt = row.get("src_id", ""), row.get("tgt_id", "")
        if not src or not tgt:
            continue
        raw_urls = row.get("source_urls", "[]")
        urls = json.loads(raw_urls) if isinstance(raw_urls, str) else raw_urls
        index[(src, tgt)] = {
            "candidate_id": row.get("source_candidate_id", ""),
            "description": row.get("description", ""),
            "weight": float(row.get("weight", 0.0) or 0),
            "source_urls": urls,
        }
    return index


def fetch_claim_text(candidate_id: str) -> str:
    if not SQLITE_DB.exists() or not candidate_id:
        return ""
    con = sqlite3.connect(SQLITE_DB)
    row = con.execute(
        "SELECT claim_text FROM candidate_assertions WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    con.close()
    return (row[0] or "") if row else ""


# ─── Graph retrieval ──────────────────────────────────────────────────────────

def keyword_entity_match(graph: nx.Graph, query: str) -> list[tuple[str, float]]:
    """Score each graph node by keyword overlap with the query."""
    keywords = set(query.lower().split())
    scores = []
    for node in graph.nodes():
        node_lower = node.lower()
        # Count how many query words appear in the entity name
        overlap = sum(1 for kw in keywords if kw in node_lower)
        if overlap > 0:
            scores.append((node, overlap))
    return sorted(scores, key=lambda x: x[1], reverse=True)


def ppr_expansion(
    graph: nx.Graph,
    seed_nodes: list[str],
    top_k: int = 15,
) -> list[tuple[str, float]]:
    """Personalized PageRank from seed nodes — DIGIMON's PPR operator."""
    personalization = {n: 1.0 / len(seed_nodes) for n in seed_nodes if n in graph}
    if not personalization:
        return []
    try:
        scores = nx.pagerank(graph, personalization=personalization, alpha=0.85)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
    except Exception:
        return []


def get_relevant_relationships(
    graph: nx.Graph,
    relevant_nodes: set[str],
    rel_index: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract edges between relevant nodes with provenance."""
    results = []
    for src, tgt in graph.edges():
        if src in relevant_nodes or tgt in relevant_nodes:
            key = (src, tgt) if (src, tgt) in rel_index else (tgt, src)
            prov = rel_index.get(key, {})
            results.append({
                "src": src,
                "tgt": tgt,
                "description": prov.get("description", ""),
                "weight": prov.get("weight", 0.0),
                "candidate_id": prov.get("candidate_id", ""),
                "source_urls": prov.get("source_urls", []),
            })
    return sorted(results, key=lambda x: x["weight"], reverse=True)


# ─── Output ───────────────────────────────────────────────────────────────────

def render_report(
    query: str,
    seed_matches: list[tuple[str, float]],
    ppr_results: list[tuple[str, float]],
    relationships: list[dict[str, Any]],
    prov_index: dict[str, dict[str, Any]],
) -> None:
    print(f"\n{'═'*72}")
    print(f"  DIGIMON QUERY: {query!r}")
    print(f"{'═'*72}\n")

    # Seed entity matches
    if seed_matches:
        print(f"[MATCHED ENTITIES — keyword overlap]\n")
        for node, score in seed_matches[:8]:
            prov = prov_index.get(node, {})
            etype = prov.get("entity_type", "")
            urls = prov.get("source_urls", [])
            cid = prov.get("candidate_id", "")
            claim = fetch_claim_text(cid)
            print(f"  ▶ {node}  [{etype}]")
            if claim:
                # Wrap claim text
                import textwrap
                wrapped = textwrap.fill(claim, width=80, initial_indent="    ", subsequent_indent="    ")
                print(f"    claim: {wrapped.strip()}")
            if urls:
                for url in urls[:2]:
                    print(f"    src: {url}")
            print()
    else:
        print("  (No direct entity matches — showing PPR expansion only)\n")

    # PPR expansion results
    if ppr_results:
        non_seed = [(n, s) for n, s in ppr_results if n not in {x[0] for x in seed_matches}]
        if non_seed:
            print(f"[PPR-EXPANDED ENTITIES — graph neighborhood]\n")
            for node, score in non_seed[:8]:
                prov = prov_index.get(node, {})
                etype = prov.get("entity_type", "")
                urls = prov.get("source_urls", [])
                print(f"  ◆ {node}  [{etype}]  ppr={score:.4f}")
                if urls:
                    for url in urls[:1]:
                        print(f"    src: {url}")
            print()

    # Relationships with evidence
    if relationships:
        print(f"[RELATIONSHIPS — {len(relationships)} edges with provenance]\n")
        for rel in relationships[:12]:
            src, tgt = rel["src"], rel["tgt"]
            desc = rel.get("description", "")
            urls = rel.get("source_urls", [])
            weight = rel.get("weight", 0.0)
            print(f"  {src}  →  {tgt}  (weight={weight:.2f})")
            if desc:
                import textwrap
                print(textwrap.fill(
                    desc, width=80,
                    initial_indent="    ",
                    subsequent_indent="    ",
                ))
            for url in urls[:2]:
                print(f"    src: {url}")
            print()

    # Summary
    print(f"{'─'*72}")
    print(f"  Summary: {len(seed_matches)} keyword matches, "
          f"{len(ppr_results)} PPR-expanded nodes, "
          f"{len(relationships)} traced relationships")
    sourced = sum(1 for r in relationships if r.get("source_urls"))
    print(f"  Provenance: {sourced}/{len(relationships)} relationships have source URLs")
    print(f"{'─'*72}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_query(query: str) -> None:
    graph = nx.read_graphml(DIGIMON_GRAPH)
    prov_index = build_provenance_index()
    rel_index = build_relationship_index()

    # Step 1: keyword match → seed entities
    seed_matches = keyword_entity_match(graph, query)

    # Step 2: PPR from seeds → expand neighborhood
    seed_nodes = [n for n, _ in seed_matches[:5]]
    if not seed_nodes:
        # Fall back to centrality-ranked nodes
        deg = dict(graph.degree())
        seed_nodes = [n for n, _ in sorted(deg.items(), key=lambda x: x[1], reverse=True)[:3]]

    ppr_results = ppr_expansion(graph, seed_nodes)
    relevant_nodes = {n for n, _ in seed_matches[:5]} | {n for n, _ in ppr_results[:10]}

    # Step 3: extract relationships with provenance
    relationships = get_relevant_relationships(graph, relevant_nodes, rel_index)

    render_report(query, seed_matches, ppr_results, relationships, prov_index)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query Iran disinformation DIGIMON graph with provenance"
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Research question or keyword string",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_query(args.query)
