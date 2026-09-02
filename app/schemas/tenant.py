"""
Pydantic schemas for tenant API — request bodies and response models.
Kept separate from SQLAlchemy models (app/models/tenant.py) and routes (app/routers/tenants.py).
"""
from typing import Literal
from pydantic import BaseModel


class TenantCreate(BaseModel):
    """Request body for POST /tenants. resource_code is generated server-side — not provided by caller."""
    name:       str
    github_org: str                            # GitHub organisation slug, e.g. "acme-corp"
    tier:       Literal["shared", "dedicated"] # infrastructure tier chosen at onboarding


class TenantResponse(BaseModel):
    """Response for GET and POST /tenants — never exposes any secrets."""
    id:            str
    name:          str
    github_org:    str
    tier:          str
    resource_code: str  # SHA256(github_org)[:8] — used to name Azure resources, e.g. vnet-sdlc-a3f1c2b4-dev
