"""
Pydantic models for API request/response.
"""
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
