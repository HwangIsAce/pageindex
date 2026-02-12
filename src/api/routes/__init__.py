"""
API route modules.
"""
from api.routes.documents import router as documents_router
from api.routes.jobs import router as jobs_router

__all__ = ["documents_router", "jobs_router"]
