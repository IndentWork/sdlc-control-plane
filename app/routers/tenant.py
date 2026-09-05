"""
Tenant router — endpoints called by GitHub Actions workflows in tenant repos.
All endpoints authenticated via GitHub OIDC token (see security.verified_tenant).

GET  /tenant/test_storage   — puts test message, worker writes hello.txt (connectivity smoke test)
POST /tenant/upload_sdlc    — receives raw sdlc.yml, worker saves to Storage
POST /tenant/index          — triggers indexing worker to index repos from sdlc.yml
POST /tenant/orchestrate    — triggers orchestrator worker to process a labeled issue

All payloads include github_org so workers can build the correct storage path:
  sdlc/{resource_code}/{github_org}/...
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.security import verified_tenant
from app.services.servicebus import send_message

router = APIRouter(prefix="/tenant", tags=["tenant"])


class OrchestrateRequest(BaseModel):
    """Payload sent by trigger-sdlc action when an issue is labeled 'sdlc'."""
    github_org:   str
    issue_repo:   str
    issue_number: int


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


@router.post("/orchestrate")
async def trigger_orchestrator(
    req: OrchestrateRequest,
    tenant: dict = Depends(verified_tenant),
) -> dict:
    """
    Trigger the orchestrator worker to process a labeled issue.

    Called by IndentWork/sdlc-actions/trigger-sdlc when an issue is labeled 'sdlc'.
    Body carries the issue coordinates; the tenant is identified via OIDC token.

    Security check: request payload github_org must match the OIDC-verified tenant.
    """
    # verify the org in the payload matches the tenant identified by OIDC token
    # prevents a tenant from triggering orchestration for another tenant's repo
    if req.github_org != tenant["github_org"]:
        raise HTTPException(
            status_code=403,
            detail=f"github_org mismatch: payload={req.github_org}, oidc={tenant['github_org']}",
        )

    payload = {
        "action":        "orchestrate",
        "resource_code": tenant["resource_code"],
        "github_org":    tenant["github_org"],
        "tier":          tenant["tier"],
        "issue_repo":    req.issue_repo,
        "issue_number":  req.issue_number,
    }

    try:
        await send_message(tenant["tier"], tenant["resource_code"], payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return {
        "status":       "queued",
        "action":       "orchestrate",
        "org":          tenant["github_org"],
        "issue_repo":   req.issue_repo,
        "issue_number": req.issue_number,
    }
