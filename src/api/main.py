"""
PageIndex API server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.config import CORS_ORIGINS_LIST, limiter
from api.logging_config import RequestLoggingMiddleware, setup_logging
from api.routes import documents_router, jobs_router

setup_logging()

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
    allow_origins=CORS_ORIGINS_LIST if CORS_ORIGINS_LIST != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

# Routers
app.include_router(jobs_router)
app.include_router(documents_router)
