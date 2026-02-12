"""
PageIndex API server.
"""
import json
import logging
import os
import shutil

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.logging_config import RequestLoggingMiddleware, setup_logging
from api.store import (
    DATA_DIR,
    create_job,
    delete_document,
    get_document,
    get_job,
    list_documents,
)
from api.tasks import run_indexing_task
from pageindex import load_unified_toc, query as pageindex_query

setup_logging()
log = logging.getLogger("api")

_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
limiter = Limiter(key_func=get_remote_address)
_CORS_ORIGINS_LIST = [o.strip() for o in _CORS_ORIGINS.split(",") if o.strip()]

app = FastAPI(
    title="PageIndex API",
    description="API for document indexing and retrieval with PageIndex",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS_LIST if _CORS_ORIGINS_LIST != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/documents")
@limiter.limit("10/minute")
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

    max_bytes = int(os.getenv("MAX_UPLOAD_BYTES", "104857600"))  # 100MB default
    for f in pdfs:
        content = await f.read()
        if len(content) > max_bytes:
            raise HTTPException(400, f"File {f.filename} exceeds max size ({max_bytes} bytes)")
        path = upload_dir / (f.filename or "unnamed.pdf")
        path.write_bytes(content)

    background_tasks.add_task(run_indexing_task, job_id, upload_dir)
    return JSONResponse(content={"job_id": job_id}, status_code=202)


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get job status. Returns processing, completed, or failed."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job["id"],
        "status": job["status"],
        "document_id": job.get("document_id"),
        "error": job.get("error"),
        "progress": job.get("progress", 0),
        "message": job.get("message"),
    }


@app.get("/documents")
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


@app.get("/documents/{document_id}/toc")
def get_document_toc(document_id: str):
    """Get unified table of contents for a document."""
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    toc = load_unified_toc(doc["toc_path"])
    return toc


class QueryRequest(BaseModel):
    query: str


@app.post("/documents/{document_id}/query")
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


@app.delete("/documents/{document_id}")
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
