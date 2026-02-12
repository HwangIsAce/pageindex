"""
Structured logging configuration for PageIndex API.
"""
import json
import logging
import os
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False) + "\n"


def setup_logging():
    """Configure root logger. Set LOG_FORMAT=json for JSON output."""
    level = os.getenv("LOG_LEVEL", "INFO")
    fmt = os.getenv("LOG_FORMAT", "text").lower()
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    root = logging.getLogger()
    if root.handlers:
        h = root.handlers[0]
        h.setFormatter(JsonFormatter() if fmt == "json" else logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with method, path, status, duration."""

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logging.getLogger("api").info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
