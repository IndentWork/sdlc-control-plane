from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/index", tags=["index"])


class IndexRequest(BaseModel):
    tenant_key: str       # tenant authenticates with this key (SHA256 verified against DB)
    project_name: str     # name of the project to index
    repos: list[str]      # list of repo names to index


class IndexResponse(BaseModel):
    job_id: str           # caller polls this to check indexing status
    message: str


@router.post("", response_model=IndexResponse)
async def request_index(request: IndexRequest) -> IndexResponse:
    """
    Accepts an indexing request from a tenant.

    Flow:
    1. Verify tenant_key against PostgreSQL (SHA256 lookup) — NOT YET IMPLEMENTED
    2. Get tenant endpoints (AI Search, Cosmos, Service Bus) — NOT YET IMPLEMENTED
    3. Put message on Service Bus index-request queue — NOT YET IMPLEMENTED

    For now returns a stub response so we can verify the endpoint is reachable.
    """

    # TODO: verify tenant_key against tenants table
    # TODO: look up tenant endpoints from tenant_endpoints table
    # TODO: put message on Service Bus

    return IndexResponse(
        job_id="stub-job-id",
        message=f"Index request received for project '{request.project_name}' with {len(request.repos)} repos. Processing not yet implemented.",
    )
