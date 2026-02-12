"""API E2E tests. Run: pytest tests/test_api.py -v"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_documents_empty(client):
    r = client.get("/documents")
    assert r.status_code == 200
    assert "documents" in r.json()
    assert r.json()["documents"] == []


def test_get_job_not_found(client):
    r = client.get("/jobs/nonexistent")
    assert r.status_code == 404


def test_get_document_toc_not_found(client):
    r = client.get("/documents/nonexistent/toc")
    assert r.status_code == 404


def test_query_document_not_found(client):
    r = client.post("/documents/nonexistent/query", json={"query": "test"})
    assert r.status_code == 404


def test_delete_document_not_found(client):
    r = client.delete("/documents/nonexistent")
    assert r.status_code == 404


def test_upload_no_pdf(client):
    r = client.post("/documents", files=[])
    assert r.status_code == 422  # validation error for empty files
