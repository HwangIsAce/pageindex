"""
Job status routes.
"""
from fastapi import APIRouter, HTTPException

from api.store import get_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
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
