# PageIndex API Reference

Self-hosted API for document indexing and RAG retrieval.

## Running the API

```bash
# Development
python run_api.py

# With Docker
docker compose up --build
```

API runs at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/documents` | Upload PDFs, returns `job_id` (202) |
| GET | `/jobs/{job_id}` | Poll job status |
| GET | `/documents` | List indexed documents |
| GET | `/documents/{id}/toc` | Get unified TOC |
| POST | `/documents/{id}/query` | RAG query |
| DELETE | `/documents/{id}` | Delete document |

## Environment Variables

See `env.example`. Key variables:

- `CHATGPT_API_KEY` – Required for indexing and query
- `PAGEINDEX_DATA_DIR` – Data directory (default: `./data`)
- `CORS_ORIGINS` – Allowed origins (comma-separated, default: `*`)
- `MAX_UPLOAD_BYTES` – Max file size (default: 100MB)
- `LOG_FORMAT` – `text` or `json`
- `LOG_LEVEL` – `DEBUG`, `INFO`, etc.

## Example: Upload and Query

```bash
# Upload
curl -X POST http://localhost:8000/documents -F "files=@doc.pdf"

# Poll status (use job_id from response)
curl http://localhost:8000/jobs/{job_id}

# Query (use document_id when completed)
curl -X POST http://localhost:8000/documents/{document_id}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the summary?"}'
```
