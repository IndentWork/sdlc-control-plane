"""Pydantic schemas for /index API."""
from pydantic import BaseModel


class IndexRequest(BaseModel):
    """
    Request body for POST /index.
    Auth is via GitHub OIDC Bearer token in the Authorization header —
    no tenant_key in the body. Token validation is handled by middleware.
    """
    project_name: str
    repos:        list[str]


class IndexResponse(BaseModel):
    """Response for POST /index — job_id to poll, message with human-readable status."""
    job_id:  str
    message: str
