#!/usr/bin/env python3
"""
Query PageIndex unified TOC: tree search and answer generation.
Phase 6 CLI for retrieval.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pageindex import load_unified_toc, query


def main():
    parser = argparse.ArgumentParser(
        description='Query documents using PageIndex unified TOC'
    )
    parser.add_argument(
        '--unified_toc',
        type=str,
        required=True,
        help='Path to unified TOC JSON file',
    )
    parser.add_argument(
        '--doc_store',
        type=str,
        required=True,
        help='Path to doc_store JSON: {"doc_id": "path/to/doc.pdf"}',
    )
    parser.add_argument(
        '--query', '-q',
        type=str,
        required=True,
        help='Question to ask',
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-2024-11-20',
        help='OpenAI model to use',
    )
    parser.add_argument(
        '--retrieval_log',
        type=str,
        default=None,
        help='Path to append retrieval events (for highlighting)',
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Save full result (retrieved_nodes, context, answer) to JSON file',
    )
    args = parser.parse_args()

    if not os.path.isfile(args.unified_toc):
        raise FileNotFoundError(f"Unified TOC not found: {args.unified_toc}")
    if not os.path.isfile(args.doc_store):
        raise FileNotFoundError(f"Doc store not found: {args.doc_store}")

    with open(args.doc_store, 'r', encoding='utf-8') as f:
        doc_store = json.load(f)

    unified = load_unified_toc(args.unified_toc)

    result = query(
        args.query,
        unified,
        doc_store,
        model=args.model,
        retrieval_log_path=args.retrieval_log,
    )

    print(result['answer'])

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nFull result saved to: {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
