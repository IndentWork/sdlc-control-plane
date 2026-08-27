"""
Pydantic schemas for tenant API — request bodies and response models.
Kept separate from SQLAlchemy models (app/models/tenant.py) and routes (app/routers/tenants.py).
"""
from pydantic import BaseModel


class TenantCreate(BaseModel):
    """Request body for POST /tenants."""
    name: str


class TenantResponse(BaseModel):
    """Response for GET endpoints — never exposes the sha256_key."""
    id: str
    name: str


class TenantCreateResponse(BaseModel):
    """
    Response for POST /tenants only.
    Includes plaintext tenant_key — returned ONCE at creation time.
    Caller must save it — never retrievable again (only the hash is stored).
    """
    id: str
    name: str
    tenant_key: str
