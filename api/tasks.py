"""
Background indexing task.
"""
import json
import shutil
import uuid
from pathlib import Path

from api.store import (
    DATA_DIR,
    create_document,
    update_job,
)
from pageindex import page_index_batch, build_unified_toc, save_unified_toc
from pageindex.utils import ConfigLoader


def run_indexing_task(job_id: str, upload_dir: Path):
    """
    Run indexing on uploaded PDFs. Called from background.
    """
    try:
        update_job(job_id, message="Loading documents...", progress=10)

        paths = sorted(upload_dir.glob("*.pdf"))
        if not paths:
            update_job(job_id, status="failed", error="No PDF files found")
            return

        opt = ConfigLoader().load({
            "if_add_node_summary": "no",
            "if_add_node_entities": "no",
        })
        docs = [(str(p),) for p in paths]

        update_job(job_id, message=f"Indexing {len(docs)} documents...", progress=30)
        results = page_index_batch(docs, opt)

        update_job(job_id, message="Building unified TOC...", progress=70)
        unified = build_unified_toc(results)

        doc_id = uuid.uuid4().hex
        doc_dir = DATA_DIR / "documents" / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        toc_path = doc_dir / "unified_toc.json"
        doc_store_path = doc_dir / "doc_store.json"
        save_unified_toc(unified, toc_path)

        pdfs_dir = doc_dir / "pdfs"
        pdfs_dir.mkdir(exist_ok=True)
        doc_store = {}
        for r, src in zip(results, paths):
            dst = pdfs_dir / src.name
            shutil.copy2(src, dst)
            doc_store[r["doc_id"]] = str(dst)
        with open(doc_store_path, "w", encoding="utf-8") as f:
            json.dump(doc_store, f, indent=2)

        create_document(
            doc_id=doc_id,
            name=f"Document set ({len(docs)} files)",
            doc_count=len(docs),
            toc_path=str(toc_path),
            doc_store_path=str(doc_store_path),
        )

        update_job(
            job_id,
            status="completed",
            document_id=doc_id,
            progress=100,
            message="Indexing complete",
        )
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
    finally:
        if upload_dir.exists():
            shutil.rmtree(upload_dir, ignore_errors=True)
