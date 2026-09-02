import uuid

from fastapi import APIRouter, HTTPException, Response

from app.db import get_db_session
from app.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(body: TenantCreate) -> TenantResponse:
    """
    Register a new tenant.
    Stores their GitHub org name and infrastructure tier — no secret is generated or returned.
    Auth is GitHub OIDC: tokens are validated at request time using the org name.
    """
    tenant_id = str(uuid.uuid4())

    async with get_db_session() as conn:
        await conn.execute(
            "INSERT INTO tenants (id, name, github_org, tier) VALUES ($1, $2, $3, $4)",
            tenant_id, body.name, body.github_org, body.tier,
        )

    return TenantResponse(id=tenant_id, name=body.name, github_org=body.github_org, tier=body.tier)


@router.get("", response_model=list[TenantResponse])
async def list_tenants() -> list[TenantResponse]:
    """List all tenants."""
    async with get_db_session() as conn:
        rows = await conn.fetch("SELECT id, name, github_org, tier FROM tenants ORDER BY name")

    return [TenantResponse(id=r["id"], name=r["name"], github_org=r["github_org"], tier=r["tier"]) for r in rows]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str) -> TenantResponse:
    """Get a specific tenant by id."""
    async with get_db_session() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, github_org, tier FROM tenants WHERE id = $1",
            tenant_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(id=row["id"], name=row["name"], github_org=row["github_org"], tier=row["tier"])


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: str) -> Response:
    """Delete a tenant by id. Idempotent — returns 204 whether or not it existed."""
    async with get_db_session() as conn:
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)

    return Response(status_code=204)
