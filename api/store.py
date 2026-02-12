"""
Job and document storage (SQLite).
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.getenv("PAGEINDEX_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "pageindex.db"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_conn():
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            document_id TEXT,
            error TEXT,
            progress INTEGER DEFAULT 0,
            message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT,
            doc_count INTEGER,
            toc_path TEXT NOT NULL,
            doc_store_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create_job():
    """Create a new job, return job_id."""
    _init_db()
    job_id = uuid.uuid4().hex
    now = datetime.utcnow().isoformat() + "Z"
    conn = _get_conn()
    conn.execute(
        "INSERT INTO jobs (id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (job_id, "processing", now, now),
    )
    conn.commit()
    conn.close()
    return job_id


def update_job(job_id, status=None, document_id=None, error=None, progress=None, message=None):
    """Update job status."""
    now = datetime.utcnow().isoformat() + "Z"
    conn = _get_conn()
    updates = ["updated_at = ?"]
    params = [now]
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if document_id is not None:
        updates.append("document_id = ?")
        params.append(document_id)
    if error is not None:
        updates.append("error = ?")
        params.append(error)
    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)
    if message is not None:
        updates.append("message = ?")
        params.append(message)
    params.append(job_id)
    conn.execute(
        f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    conn.close()


def get_job(job_id):
    """Get job by id. Returns dict or None."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def create_document(doc_id, name, doc_count, toc_path, doc_store_path):
    """Create document record."""
    now = datetime.utcnow().isoformat() + "Z"
    conn = _get_conn()
    conn.execute(
        "INSERT INTO documents (id, name, doc_count, toc_path, doc_store_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, name, doc_count, toc_path, doc_store_path, now),
    )
    conn.commit()
    conn.close()


def get_document(doc_id):
    """Get document by id. Returns dict or None."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def list_documents():
    """List all documents."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
