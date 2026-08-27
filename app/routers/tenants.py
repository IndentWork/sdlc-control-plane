import secrets
import uuid

from fastapi import APIRouter, HTTPException, Response

from app.db import get_db_session
from app.schemas.tenant import TenantCreate, TenantResponse, TenantCreateResponse
from app.security import hash_key

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantCreateResponse, status_code=201)
async def create_tenant(body: TenantCreate) -> TenantCreateResponse:
    """
    Create a new tenant.
    Generates a random 32-byte URL-safe key, hashes it, and stores the hash.
    Returns the plaintext key in the response — the caller MUST save it now.
    """
    tenant_id = str(uuid.uuid4())
    plaintext_key = secrets.token_urlsafe(32)

    async with get_db_session() as conn:
        await conn.execute(
            "INSERT INTO tenants (id, name, sha256_key) VALUES ($1, $2, $3)",
            tenant_id, body.name, hash_key(plaintext_key)
        )

    return TenantCreateResponse(id=tenant_id, name=body.name, tenant_key=plaintext_key)


@router.get("", response_model=list[TenantResponse])
async def list_tenants() -> list[TenantResponse]:
    """List all tenants — never exposes the sha256_key."""
    async with get_db_session() as conn:
        rows = await conn.fetch("SELECT id, name FROM tenants ORDER BY name")

    return [TenantResponse(id=row["id"], name=row["name"]) for row in rows]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str) -> TenantResponse:
    """Get a specific tenant by id — never exposes the sha256_key."""
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
