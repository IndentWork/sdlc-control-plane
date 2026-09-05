"""
Test router — validates end-to-end connectivity: FastAPI → Service Bus → Worker → Storage.

GET  /tenant/test_storage   — puts test message, worker writes hello.txt
POST /tenant/upload_sdlc    — receives raw YAML, worker saves as sdlc.yml in Storage
POST /tenant/index          — triggers indexing worker to index repos from sdlc.yml

All payloads include github_org so workers can build the correct storage path:
  sdlc/{resource_code}/{github_org}/...

Remove this router once the real sync endpoint is working.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

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
        "resource_code": tenant["resource_code"],
        "github_org":    tenant["github_org"],
        "tier":          tenant["tier"],
    }

    try:
        await send_message(tenant["tier"], tenant["resource_code"], payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return {
        "status": "queued",
        "org":    tenant["github_org"],
        "queue":  "repo-index",
    }


@router.post("/upload_sdlc")
async def upload_sdlc(request: Request, tenant: dict = Depends(verified_tenant)) -> dict:
    """
    Receive raw sdlc.yml content and queue it for the worker to save to Storage.
    Body: raw YAML text (Content-Type: text/plain or application/x-yaml).
    Worker saves it to: sdlc/{resource_code}/{github_org}/sdlc.yml
    """
    try:
        yaml_content = (await request.body()).decode("utf-8")

        if not yaml_content.strip():
            raise HTTPException(status_code=400, detail="Request body is empty")

        payload = {
            "action":        "upload_sdlc",
            "resource_code": tenant["resource_code"],
            "github_org":    tenant["github_org"],
            "tier":          tenant["tier"],
            "content":       yaml_content,
        }

        await send_message(tenant["tier"], tenant["resource_code"], payload)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return {
        "status": "queued",
        "org":    tenant["github_org"],
        "queue":  "repo-index",
    }


@router.post("/index")
async def trigger_indexing(tenant: dict = Depends(verified_tenant)) -> dict:
    """
    Trigger the indexing worker to index all repos defined in sdlc.yml.
    sdlc.yml must already be uploaded to Storage via POST /tenant/upload_sdlc.
    Indexing worker reads from: sdlc/{resource_code}/{github_org}/sdlc.yml
    """
    try:
        payload = {
            "action":        "index_repos",
            "resource_code": tenant["resource_code"],
            "github_org":    tenant["github_org"],
            "tier":          tenant["tier"],
        }

        await send_message(tenant["tier"], tenant["resource_code"], payload)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return {
        "status": "queued",
        "org":    tenant["github_org"],
        "action": "index_repos",
    }
