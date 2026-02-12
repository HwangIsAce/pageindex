import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pageindex import (
    md_to_tree,
    page_index_main,
    page_index_batch,
    build_unified_toc,
    save_unified_toc,
)
from pageindex.utils import config

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process PDF or Markdown document and generate structure')
    parser.add_argument('--pdf_path', type=str, help='Path to a single PDF file')
    parser.add_argument('--md_path', type=str, help='Path to a single Markdown file')
    parser.add_argument('--pdf_paths', type=str, help='Comma-separated paths to multiple PDF files (generates unified TOC)')
    parser.add_argument('--input_dir', type=str, help='Directory containing PDF files (generates unified TOC from all .pdf)')

    parser.add_argument('--model', type=str, default='gpt-4o-2024-11-20', help='Model to use')

    parser.add_argument('--toc-check-pages', type=int, default=20, 
                      help='Number of pages to check for table of contents (PDF only)')
    parser.add_argument('--max-pages-per-node', type=int, default=10,
                      help='Maximum number of pages per node (PDF only)')
    parser.add_argument('--max-tokens-per-node', type=int, default=20000,
                      help='Maximum number of tokens per node (PDF only)')

    parser.add_argument('--if-add-node-id', type=str, default='yes',
                      help='Whether to add node id to the node')
    parser.add_argument('--if-add-node-summary', type=str, default='yes',
                      help='Whether to add summary to the node')
    parser.add_argument('--if-add-doc-description', type=str, default='no',
                      help='Whether to add doc description to the doc')
    parser.add_argument('--if-add-node-text', type=str, default='no',
                      help='Whether to add text to the node')
    parser.add_argument('--if-add-node-entities', type=str, default='no',
                      help='Whether to add entities (key terms) to each node')

    parser.add_argument('--doc-id', type=str, default=None,
                      help='Document ID (auto-generated UUID if not specified)')
    parser.add_argument('--doc-name', type=str, default=None,
                      help='Display name for the document (overrides filename)')
                      
    # Markdown specific arguments
    parser.add_argument('--if-thinning', type=str, default='no',
                      help='Whether to apply tree thinning for markdown (markdown only)')
    parser.add_argument('--thinning-threshold', type=int, default=5000,
                      help='Minimum token threshold for thinning (markdown only)')
    parser.add_argument('--summary-token-threshold', type=int, default=200,
                      help='Token threshold for generating summaries (markdown only)')

    parser.add_argument('--unified_toc_output', type=str, default='./results/unified_toc.json',
                      help='Output path for unified TOC (when using --pdf_paths or --input_dir)')
    parser.add_argument('--doc_store_output', type=str, default=None,
                      help='Output path for doc_store JSON (default: same dir as unified_toc with _doc_store.json)')
    args = parser.parse_args()

    # Count active modes
    modes = sum([bool(args.pdf_path), bool(args.md_path), bool(args.pdf_paths), bool(args.input_dir)])
    if modes == 0:
        raise ValueError("Specify one of: --pdf_path, --md_path, --pdf_paths, or --input_dir")
    if modes > 1:
        raise ValueError("Specify only one of: --pdf_path, --md_path, --pdf_paths, or --input_dir")
    
    if args.pdf_path:
        # Validate PDF file
        if not args.pdf_path.lower().endswith('.pdf'):
            raise ValueError("PDF file must have .pdf extension")
        if not os.path.isfile(args.pdf_path):
            raise ValueError(f"PDF file not found: {args.pdf_path}")
            
        # Process PDF file
        # Configure options
        opt_kwargs = {
            'model': args.model,
            'toc_check_page_num': args.toc_check_pages,
            'max_page_num_each_node': args.max_pages_per_node,
            'max_token_num_each_node': args.max_tokens_per_node,
            'if_add_node_id': args.if_add_node_id,
            'if_add_node_summary': args.if_add_node_summary,
            'if_add_doc_description': args.if_add_doc_description,
            'if_add_node_text': args.if_add_node_text,
            'if_add_node_entities': args.if_add_node_entities
        }
        if args.doc_id is not None:
            opt_kwargs['doc_id'] = args.doc_id
        if args.doc_name is not None:
            opt_kwargs['doc_display_name'] = args.doc_name
        opt = config(**opt_kwargs)

        # Process the PDF
        toc_with_page_number = page_index_main(args.pdf_path, opt)
        print('Parsing done, saving to file...')
        
        # Save results
        pdf_name = os.path.splitext(os.path.basename(args.pdf_path))[0]    
        output_dir = './results'
        output_file = f'{output_dir}/{pdf_name}_structure.json'
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(toc_with_page_number, f, indent=2)
        
        print(f'Tree structure saved to: {output_file}')
            
    elif args.md_path:
        # Validate Markdown file
        if not args.md_path.lower().endswith(('.md', '.markdown')):
            raise ValueError("Markdown file must have .md or .markdown extension")
        if not os.path.isfile(args.md_path):
            raise ValueError(f"Markdown file not found: {args.md_path}")
            
        # Process markdown file
        print('Processing markdown file...')
        
        # Process the markdown
        import asyncio
        
        # Use ConfigLoader to get consistent defaults (matching PDF behavior)
        from pageindex.utils import ConfigLoader
        config_loader = ConfigLoader()
        
        # Create options dict with user args
        user_opt = {
            'model': args.model,
            'if_add_node_summary': args.if_add_node_summary,
            'if_add_doc_description': args.if_add_doc_description,
            'if_add_node_text': args.if_add_node_text,
            'if_add_node_id': args.if_add_node_id,
            'if_add_node_entities': args.if_add_node_entities
        }
        if args.doc_id is not None:
            user_opt['doc_id'] = args.doc_id
        if args.doc_name is not None:
            user_opt['doc_display_name'] = args.doc_name

        # Load config with defaults from config.yaml
        opt = config_loader.load(user_opt)

        md_kwargs = {
            'md_path': args.md_path,
            'if_thinning': args.if_thinning.lower() == 'yes',
            'min_token_threshold': args.thinning_threshold,
            'if_add_node_summary': opt.if_add_node_summary,
            'summary_token_threshold': args.summary_token_threshold,
            'model': opt.model,
            'if_add_doc_description': opt.if_add_doc_description,
            'if_add_node_text': opt.if_add_node_text,
            'if_add_node_id': opt.if_add_node_id,
            'if_add_node_entities': getattr(opt, 'if_add_node_entities', 'no')
        }
        if hasattr(opt, 'doc_id') and opt.doc_id is not None:
            md_kwargs['doc_id'] = opt.doc_id
        if hasattr(opt, 'doc_display_name') and opt.doc_display_name is not None:
            md_kwargs['doc_display_name'] = opt.doc_display_name

        toc_with_page_number = asyncio.run(md_to_tree(**md_kwargs))
        
        print('Parsing done, saving to file...')
        
        # Save results
        md_name = os.path.splitext(os.path.basename(args.md_path))[0]    
        output_dir = './results'
        output_file = f'{output_dir}/{md_name}_structure.json'
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(toc_with_page_number, f, indent=2, ensure_ascii=False)
        
        print(f'Tree structure saved to: {output_file}')

    elif args.pdf_paths:
        # Multi-document: process PDFs and build unified TOC
        paths = [p.strip() for p in args.pdf_paths.split(',') if p.strip()]
        if not paths:
            raise ValueError("--pdf_paths must contain at least one path")
        for p in paths:
            if not p.lower().endswith('.pdf'):
                raise ValueError(f"PDF path must end with .pdf: {p}")
            if not os.path.isfile(p):
                raise ValueError(f"PDF file not found: {p}")

        opt_kwargs = {
            'model': args.model,
            'toc_check_page_num': args.toc_check_pages,
            'max_page_num_each_node': args.max_pages_per_node,
            'max_token_num_each_node': args.max_tokens_per_node,
            'if_add_node_id': args.if_add_node_id,
            'if_add_node_summary': args.if_add_node_summary,
            'if_add_doc_description': args.if_add_doc_description,
            'if_add_node_text': args.if_add_node_text,
            'if_add_node_entities': args.if_add_node_entities
        }
        opt = config(**opt_kwargs)

        docs = [(path,) for path in paths]
        print(f'Processing {len(docs)} documents...')
        results = page_index_batch(docs, opt)
        unified = build_unified_toc(results)
        save_unified_toc(unified, args.unified_toc_output)
        print(f'Unified TOC saved to: {args.unified_toc_output}')

        doc_store_output = args.doc_store_output
        if doc_store_output is None:
            base = os.path.splitext(args.unified_toc_output)[0]
            doc_store_output = f"{base}_doc_store.json"
        doc_store = {r['doc_id']: os.path.abspath(p) for r, p in zip(results, paths)}
        os.makedirs(os.path.dirname(doc_store_output) or '.', exist_ok=True)
        with open(doc_store_output, 'w', encoding='utf-8') as f:
            json.dump(doc_store, f, indent=2)
        print(f'Doc store saved to: {doc_store_output}')

    elif args.input_dir:
        # Multi-document: process all PDFs in directory
        if not os.path.isdir(args.input_dir):
            raise ValueError(f"Directory not found: {args.input_dir}")

        paths = sorted(glob.glob(os.path.join(args.input_dir, '*.pdf')))
        if not paths:
            raise ValueError(f"No PDF files found in {args.input_dir}")

        opt_kwargs = {
            'model': args.model,
            'toc_check_page_num': args.toc_check_pages,
            'max_page_num_each_node': args.max_pages_per_node,
            'max_token_num_each_node': args.max_tokens_per_node,
            'if_add_node_id': args.if_add_node_id,
            'if_add_node_summary': args.if_add_node_summary,
            'if_add_doc_description': args.if_add_doc_description,
            'if_add_node_text': args.if_add_node_text,
            'if_add_node_entities': args.if_add_node_entities
        }
        opt = config(**opt_kwargs)

        docs = [(path,) for path in paths]
        print(f'Processing {len(docs)} PDFs from {args.input_dir}...')
        results = page_index_batch(docs, opt)
        unified = build_unified_toc(results)
        save_unified_toc(unified, args.unified_toc_output)
        print(f'Unified TOC saved to: {args.unified_toc_output}')

        doc_store_output = args.doc_store_output
        if doc_store_output is None:
            base = os.path.splitext(args.unified_toc_output)[0]
            doc_store_output = f"{base}_doc_store.json"
        doc_store = {r['doc_id']: os.path.abspath(p) for r, p in zip(results, paths)}
        os.makedirs(os.path.dirname(doc_store_output) or '.', exist_ok=True)
        with open(doc_store_output, 'w', encoding='utf-8') as f:
            json.dump(doc_store, f, indent=2)
        print(f'Doc store saved to: {doc_store_output}')