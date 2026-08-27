"""Pydantic schemas for /index API."""
from pydantic import BaseModel


class IndexRequest(BaseModel):
    """
    Request body for POST /index.
    tenant_key is the plaintext key — server hashes it and looks up by hash.
    """
    tenant_key: str
    project_name: str
    repos: list[str]


class IndexResponse(BaseModel):
    """Response for POST /index — job_id to poll, message with human-readable status."""
    job_id: str
    message: str
