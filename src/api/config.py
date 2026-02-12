"""
API configuration from environment variables.
"""
import os
from pathlib import Path

from slowapi import Limiter
from slowapi.util import get_remote_address

# Data
DATA_DIR = Path(os.getenv("PAGEINDEX_DATA_DIR", "data"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS_LIST = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

# Upload
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "104857600"))  # 100MB

# Rate limit
limiter = Limiter(key_func=get_remote_address)
RATE_LIMIT_UPLOAD = "10/minute"
