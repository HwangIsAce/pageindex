"""
Document routes: upload, list, toc, query, delete.
"""
import json
import shutil

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from api.config import DATA_DIR, MAX_UPLOAD_BYTES, limiter, RATE_LIMIT_UPLOAD
from api.schemas import QueryRequest
from api.store import (
    create_job,
    delete_document,
    get_document,
    list_documents,
)
from api.tasks import run_indexing_task
from pageindex import load_unified_toc, query as pageindex_query

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def upload_documents(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """
    Upload PDFs for indexing. Returns 202 with job_id for status polling.
    """
    pdfs = [f for f in files if f.filename and f.filename.lower().endswith(".pdf")]
    if not pdfs:
        raise HTTPException(400, "At least one PDF file is required")

    job_id = create_job()
    upload_dir = DATA_DIR / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    for f in pdfs:
        content = await f.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                400,
                f"File {f.filename} exceeds max size ({MAX_UPLOAD_BYTES} bytes)",
            )
        path = upload_dir / (f.filename or "unnamed.pdf")
        path.write_bytes(content)

    background_tasks.add_task(run_indexing_task, job_id, upload_dir)
    return JSONResponse(content={"job_id": job_id}, status_code=202)


@router.get("")
def list_documents_route():
    """List all indexed documents."""
    docs = list_documents()
    return {
        "documents": [
            {
                "id": d["id"],
                "name": d["name"],
                "doc_count": d["doc_count"],
                "created_at": d["created_at"],
            }
            for d in docs
        ],
    }


@router.get("/{document_id}/toc")
def get_document_toc(document_id: str):
    """Get unified table of contents for a document."""
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    toc = load_unified_toc(doc["toc_path"])
    return toc


@router.post("/{document_id}/query")
def query_document(document_id: str, body: QueryRequest):
    """
    Query a document using RAG. Returns answer and retrieved node references.
    """
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    unified_toc = load_unified_toc(doc["toc_path"])
    with open(doc["doc_store_path"], encoding="utf-8") as f:
        doc_store = json.load(f)
    result = pageindex_query(
        body.query,
        unified_toc,
        doc_store,
    )
    return {
        "answer": result["answer"],
        "retrieved_nodes": result["retrieved_nodes"],
    }


@router.delete("/{document_id}")
def delete_document_route(document_id: str):
    """Delete an indexed document and its stored files."""
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    doc_dir = DATA_DIR / "documents" / document_id
    if doc_dir.exists():
        shutil.rmtree(doc_dir, ignore_errors=True)
    delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}
