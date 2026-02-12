"""
Retrieval layer for unified TOC: tree search and answer generation.
Phase 4 of PageIndex extension.
"""
import json
from .utils import (
    ChatGPT_API,
    extract_json,
    get_page_tokens,
    get_text_of_pdf_pages,
    structure_to_list,
)


def _find_node_by_id(structure, doc_id, node_id):
    """Find a node by (doc_id, node_id) in a structure."""
    nodes = structure_to_list(structure)
    for node in nodes:
        if node.get('doc_id') == doc_id and node.get('node_id') == node_id:
            return node
    return None


def _get_page_list_for_doc(doc_id, doc_store, model=None):
    """Resolve page_list from doc_store. doc_store[doc_id] can be page_list or doc path/BytesIO."""
    val = doc_store.get(doc_id)
    if val is None:
        raise KeyError(f"doc_id '{doc_id}' not found in doc_store")
    if isinstance(val, list):
        return val
    return get_page_tokens(val, model=model or "gpt-4o-2024-11-20")


def _simplify_for_search(structure):
    """Create a compact structure for LLM tree search (drop text, keep metadata)."""
    def simplify_node(node):
        out = {}
        for k in ['doc_id', 'node_id', 'title', 'summary', 'prefix_summary', 'entities']:
            if k in node and node[k] is not None:
                out[k] = node[k]
        if 'nodes' in node and node['nodes']:
            out['nodes'] = [simplify_node(n) for n in node['nodes']]
        return out

    if isinstance(structure, list):
        return [simplify_node(n) for n in structure]
    return [simplify_node(structure)]


def unified_tree_search(query, unified_toc, model=None):
    """
    Run LLM tree search over the unified TOC to find relevant (doc_id, node_id) pairs.

    Args:
        query: User question
        unified_toc: From build_unified_toc(), with doc_structures
        model: OpenAI model name

    Returns:
        List of {"doc_id": str, "node_id": str}
    """
    doc_structures = unified_toc.get('doc_structures', [])
    toc_for_prompt = []
    for doc in doc_structures:
        toc_for_prompt.append({
            'doc_id': doc['doc_id'],
            'doc_name': doc['doc_name'],
            'structure': _simplify_for_search(doc['structure']),
        })

    prompt = f"""You are given a query and a unified table of contents from multiple documents.
Each document has doc_id, doc_name, and a tree structure. Each node has doc_id, node_id, title, and optionally summary and entities.
Your task is to find all nodes that are likely to contain information relevant to answering the query.

Query: {query}

Unified document structures:
{json.dumps(toc_for_prompt, indent=2, ensure_ascii=False)}

Reply in the following JSON format:
{{
  "thinking": "<your reasoning about which nodes are relevant>",
  "node_list": [
    {{"doc_id": "<doc_id>", "node_id": "<node_id>"}},
    ...
  ]
}}
Return only the JSON structure. Do not output anything else."""

    response = ChatGPT_API(model, prompt)
    parsed = extract_json(response)
    node_list = parsed.get('node_list', [])
    if not isinstance(node_list, list):
        return []
    return [
        {'doc_id': str(n.get('doc_id', '')), 'node_id': str(n.get('node_id', ''))}
        for n in node_list
        if n.get('doc_id') and n.get('node_id')
    ]


def get_node_text(doc_id, node_id, unified_toc, doc_store, model=None):
    """
    Get the full text content for a node.

    Args:
        doc_id: Document ID
        node_id: Node ID
        unified_toc: From build_unified_toc()
        doc_store: { doc_id: page_list or doc_path/BytesIO }
        model: For get_page_tokens when doc_store has path

    Returns:
        str: Text content of the node, or empty string if not found
    """
    node = None
    for doc in unified_toc.get('doc_structures', []):
        if doc.get('doc_id') == doc_id:
            node = _find_node_by_id(doc['structure'], doc_id, node_id)
            break
    if node is None:
        return ''

    start_page = node.get('start_index')
    end_page = node.get('end_index')
    if start_page is None or end_page is None:
        return ''

    page_list = _get_page_list_for_doc(doc_id, doc_store, model)
    return get_text_of_pdf_pages(page_list, start_page, end_page + 1)


def query(query_text, unified_toc, doc_store, model=None):
    """
    Full pipeline: tree search → fetch node texts → generate answer.

    Args:
        query_text: User question
        unified_toc: From build_unified_toc()
        doc_store: { doc_id: page_list or doc_path }
        model: OpenAI model name

    Returns:
        dict with 'retrieved_nodes', 'context', 'answer'
    """
    model = model or "gpt-4o-2024-11-20"

    # Tree search
    nodes = unified_tree_search(query_text, unified_toc, model)
    if not nodes:
        return {
            'retrieved_nodes': [],
            'context': '',
            'answer': 'No relevant sections found for this query.',
        }

    # Fetch text for each node
    context_parts = []
    for n in nodes:
        text = get_node_text(n['doc_id'], n['node_id'], unified_toc, doc_store, model)
        if text:
            context_parts.append(
                f"[Document: {n['doc_id']}, Section: {n['node_id']}]\n{text}"
            )

    context = '\n\n---\n\n'.join(context_parts)

    # Generate answer
    answer_prompt = f"""Answer the following question based ONLY on the provided context from the documents.
If the context does not contain enough information, say so.

Question: {query_text}

Context:
{context}

Provide a clear, concise answer based on the context. Do not make up information."""

    answer = ChatGPT_API(model, answer_prompt)

    return {
        'retrieved_nodes': nodes,
        'context': context,
        'answer': answer,
    }
