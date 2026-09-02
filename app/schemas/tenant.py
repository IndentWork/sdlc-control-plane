"""
Pydantic schemas for tenant API — request bodies and response models.
Kept separate from SQLAlchemy models (app/models/tenant.py) and routes (app/routers/tenants.py).
"""
from pydantic import BaseModel


class TenantCreate(BaseModel):
    """Request body for POST /tenants."""
    name:       str
    github_org: str  # GitHub organisation name, e.g. "acme-corp"


class TenantResponse(BaseModel):
    """Response for GET and POST /tenants — never exposes any secrets."""
    id:         str
    name:       str
    github_org: str
