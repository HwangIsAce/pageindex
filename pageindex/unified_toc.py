"""
Multi-document support and unified table-of-contents builder.
Phase 3 of PageIndex extension.
"""
import json
import copy
from pathlib import Path
from io import BytesIO
from .page_index import page_index_main
from .utils import ConfigLoader, config


def _add_doc_id_to_node(node, doc_id):
    """Recursively add doc_id to a node and all its descendants."""
    node = copy.deepcopy(node)
    node['doc_id'] = doc_id
    if 'nodes' in node and node['nodes']:
        node['nodes'] = [_add_doc_id_to_node(n, doc_id) for n in node['nodes']]
    return node


def _add_doc_id_to_structure(structure, doc_id):
    """Add doc_id to every node in a structure (list of root nodes)."""
    if isinstance(structure, list):
        return [_add_doc_id_to_node(n, doc_id) for n in structure]
    return [_add_doc_id_to_node(structure, doc_id)]


def page_index_batch(docs, opt=None):
    """
    Process multiple documents and return a list of indexed structures.

    Args:
        docs: List of:
            - str (file path) or BytesIO
            - or (doc, doc_id, doc_display_name) tuple
            - or dict with 'doc', optional 'doc_id', 'doc_display_name'
        opt: Config options (uses ConfigLoader defaults if None)

    Returns:
        List of {doc_id, doc_name, structure, ...} per document
    """
    if opt is None:
        opt = ConfigLoader().load({})

    results = []
    for i, item in enumerate(docs):
        doc = None
        doc_id = None
        doc_display_name = None

        if isinstance(item, (str, BytesIO)):
            doc = item
        elif isinstance(item, (tuple, list)) and len(item) >= 1:
            doc = item[0]
            doc_id = item[1] if len(item) > 1 else None
            doc_display_name = item[2] if len(item) > 2 else None
        elif isinstance(item, dict):
            doc = item.get('doc')
            doc_id = item.get('doc_id')
            doc_display_name = item.get('doc_display_name')

        if doc is None:
            raise ValueError(f"Invalid doc item at index {i}: {item}")

        opt_vars = dict(vars(opt))
        if doc_id is not None:
            opt_vars['doc_id'] = doc_id
        if doc_display_name is not None:
            opt_vars['doc_display_name'] = doc_display_name
        opt_copy = config(**opt_vars)
        result = page_index_main(doc, opt_copy)
        results.append(result)

    return results


def build_unified_toc(doc_structures):
    """
    Build a unified TOC from multiple document structures.
    Adds doc_id to every node for unambiguous (doc_id, node_id) identification.

    Args:
        doc_structures: List of {doc_id, doc_name, structure, ...} from page_index_main or page_index_batch

    Returns:
        dict with 'doc_structures': list of {doc_id, doc_name, structure} where each node has doc_id
    """
    unified = []
    for doc in doc_structures:
        doc_id = doc.get('doc_id')
        doc_name = doc.get('doc_name', '')
        structure = doc.get('structure', [])

        if doc_id is None:
            raise ValueError("doc_id is required in each doc structure")

        structure_with_doc_id = _add_doc_id_to_structure(structure, doc_id)
        unified.append({
            'doc_id': doc_id,
            'doc_name': doc_name,
            'structure': structure_with_doc_id,
            **{k: v for k, v in doc.items() if k not in ('doc_id', 'doc_name', 'structure')}
        })

    return {'doc_structures': unified}


def save_unified_toc(unified_toc, path):
    """Save unified TOC to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(unified_toc, f, indent=2, ensure_ascii=False)


def load_unified_toc(path):
    """Load unified TOC from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
