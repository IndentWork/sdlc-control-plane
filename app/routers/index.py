from fastapi import APIRouter, Depends

from app.db import get_db_session
from app.schemas.index import IndexRequest, IndexResponse
from app.security import verified_tenant

router = APIRouter(prefix="/index", tags=["index"])


@router.post("", response_model=IndexResponse)
async def request_index(
    request: IndexRequest,
    tenant: dict = Depends(verified_tenant),
) -> IndexResponse:
    """
    Accept an indexing request from a tenant pipeline.
    Auth: GitHub OIDC Bearer token — validated and resolved to a tenant by verified_tenant.
    TODO: put message on Service Bus index-request queue.
    """
    # TODO: put message on Service Bus index-request queue
    return IndexResponse(
        job_id=f"stub-job-{tenant['id']}",
        message=f"Index request accepted for tenant '{tenant['name']}' — project '{request.project_name}' with {len(request.repos)} repos. Processing not yet implemented.",
    )
