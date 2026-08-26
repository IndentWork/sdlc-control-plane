import uuid
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from app.db import get_db_session

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: str
    name: str


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(body: TenantCreate) -> TenantResponse:
    """Create a new tenant."""
    tenant_id = str(uuid.uuid4())

    async with get_db_session() as conn:
        await conn.execute(
            "INSERT INTO tenants (id, name) VALUES ($1, $2)",
            tenant_id, body.name
        )

    return TenantResponse(id=tenant_id, name=body.name)


@router.get("", response_model=list[TenantResponse])
async def list_tenants() -> list[TenantResponse]:
    """List all tenants."""
    async with get_db_session() as conn:
        rows = await conn.fetch("SELECT id, name FROM tenants ORDER BY name")

    return [TenantResponse(id=row["id"], name=row["name"]) for row in rows]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str) -> TenantResponse:
    """Get a specific tenant by id."""
    async with get_db_session() as conn:
        row = await conn.fetchrow(
            "SELECT id, name FROM tenants WHERE id = $1",
            tenant_id
        )

    if row is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(id=row["id"], name=row["name"])


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: str) -> Response:
    """Delete a tenant by id. Idempotent — returns 204 whether or not it existed."""
    async with get_db_session() as conn:
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)

    return Response(status_code=204)
