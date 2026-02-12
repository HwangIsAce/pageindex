"""
PageIndex API server.
"""
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.store import DATA_DIR, create_job, get_document, get_job, list_documents
from api.tasks import run_indexing_task
from pageindex import load_unified_toc

app = FastAPI(
    title="PageIndex API",
    description="API for document indexing and retrieval with PageIndex",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/documents")
async def upload_documents(
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
        path = upload_dir / (f.filename or "unnamed.pdf")
        content = await f.read()
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
