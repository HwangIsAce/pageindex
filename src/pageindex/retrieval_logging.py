"""
Retrieval logging and highlighting: log retrieved sections, aggregate counts.
Phase 5 of PageIndex extension.
"""
import json
from datetime import datetime
from pathlib import Path
from .utils import structure_to_list


def log_retrieval(log_path, nodes, query_id=None, query_text=None):
    """
    Log a retrieval event (which nodes were retrieved for a query).

    Args:
        log_path: Path to log file (JSONL format, append-only)
        nodes: List of {"doc_id": str, "node_id": str}
        query_id: Optional query identifier (auto-generated if None)
        query_text: Optional query text for analysis
    """
    if not nodes:
        return

    import uuid
    query_id = query_id or uuid.uuid4().hex
    timestamp = datetime.utcnow().isoformat() + "Z"

    entry = {
        "query_id": query_id,
        "timestamp": timestamp,
        "nodes": nodes,
        "query": query_text,
    }

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def aggregate_retrieval_counts(log_path):
    """
    Aggregate retrieval counts from log file.
    Counts how often each (doc_id, node_id) was retrieved.

    Args:
        log_path: Path to JSONL retrieval log

    Returns:
        dict: {(doc_id, node_id): count}
    """
    counts = {}
    path = Path(log_path)
    if not path.exists():
        return counts

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                for n in entry.get("nodes", []):
                    doc_id = n.get("doc_id")
                    node_id = n.get("node_id")
                    if doc_id and node_id:
                        key = (str(doc_id), str(node_id))
                        counts[key] = counts.get(key, 0) + 1
            except json.JSONDecodeError:
                continue

    return counts


def merge_retrieval_counts(unified_toc, retrieval_counts):
    """
    Add retrieval_count to each node in unified_toc (in-place).

    Args:
        unified_toc: From build_unified_toc() or load_unified_toc()
        retrieval_counts: From aggregate_retrieval_counts(), or dict {(doc_id, node_id): count}
    """
    def add_count_to_node(node):
        doc_id = node.get("doc_id")
        node_id = node.get("node_id")
        if doc_id and node_id:
            key = (str(doc_id), str(node_id))
            node["retrieval_count"] = retrieval_counts.get(key, 0)
        if "nodes" in node and node["nodes"]:
            for child in node["nodes"]:
                add_count_to_node(child)

    for doc in unified_toc.get("doc_structures", []):
        for root in doc.get("structure", []):
            add_count_to_node(root)

    return unified_toc


def load_unified_toc_with_retrieval_counts(unified_toc_path, retrieval_log_path):
    """
    Load unified TOC and merge retrieval counts from log.

    Args:
        unified_toc_path: Path to unified TOC JSON
        retrieval_log_path: Path to retrieval log (JSONL)

    Returns:
        unified_toc with retrieval_count on each node
    """
    from .unified_toc import load_unified_toc
    unified = load_unified_toc(unified_toc_path)
    counts = aggregate_retrieval_counts(retrieval_log_path)
    return merge_retrieval_counts(unified, counts)
