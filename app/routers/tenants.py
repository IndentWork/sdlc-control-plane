import uuid
from fastapi import APIRouter, HTTPException
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
