"""
Test router — validates end-to-end connectivity: FastAPI → Service Bus → Indexing Worker → Storage.

GET /tenant/{tenant_id}/test_storage
  1. Looks up tenant (tier + resource_code)
  2. Puts a test message on the repo-index queue
  3. The Indexing Worker picks it up and creates hello.txt in the configs container

Remove this router once the real sync endpoint is working.
"""
from fastapi import APIRouter, HTTPException

from app.db import get_db_session
from app.services.servicebus import send_message

router = APIRouter(prefix="/tenant", tags=["test"])


@router.get("/{tenant_id}/test_storage")
async def test_storage(tenant_id: str) -> dict:
    """
    Trigger a test message on Service Bus for the given tenant.
    The Indexing Worker creates hello.txt in the tenant's Storage configs container.
    """
    async with get_db_session() as conn:
        tenant = await conn.fetchrow(
            "SELECT id, tier, resource_code FROM tenants WHERE id = $1",
            tenant_id,
        )

    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    payload = {
        "action": "test_storage",
        "tenant_id": tenant["id"],
        "tier": tenant["tier"],
        "resource_code": tenant["resource_code"],
    }

    await send_message(tenant["tier"], tenant["resource_code"], payload)

    return {"status": "queued", "tenant_id": tenant_id, "queue": "repo-index"}
