"""
Test router — validates end-to-end connectivity: FastAPI → Service Bus → Worker → Storage.

GET /tenant/test_storage
  - Caller authenticates with a GitHub OIDC token (Authorization: Bearer {token})
  - verified_tenant dependency validates the token and resolves the tenant from DB
  - Puts a test message on the tenant's Service Bus repo-index queue
  - The worker picks it up and creates hello.txt in the configs container

Remove this router once the real sync endpoint is working.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.security import verified_tenant
from app.services.servicebus import send_message

router = APIRouter(prefix="/tenant", tags=["test"])


@router.get("/test_storage")
async def test_storage(tenant: dict = Depends(verified_tenant)) -> dict:
    """
    Trigger a test message on Service Bus for the authenticated tenant.
    Tenant is resolved from the GitHub OIDC token — no tenant_id needed in the URL.
    """
    payload = {
        "action":        "test_storage",
        "tenant_id":     tenant["id"],
        "tier":          tenant["tier"],
        "resource_code": tenant["resource_code"],
    }

    try:
        await send_message(tenant["tier"], tenant["resource_code"], payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return {
        "status":    "queued",
        "tenant_id": tenant["id"],
        "org":       tenant["github_org"],
        "queue":     "repo-index",
    }
