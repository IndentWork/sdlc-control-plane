from fastapi import APIRouter, HTTPException

from app.db import get_db_session
from app.schemas.index import IndexRequest, IndexResponse
from app.security import hash_key

router = APIRouter(prefix="/index", tags=["index"])


@router.post("", response_model=IndexResponse)
async def request_index(request: IndexRequest) -> IndexResponse:
    """
    Accept an indexing request from a tenant.
    Verifies the tenant_key by comparing SHA256(key) against tenants.sha256_key.

    Returns 401 if the key does not match any tenant.
    Actual indexing (Service Bus queue push) is a later task.
    """
    async with get_db_session() as conn:
        tenant = await conn.fetchrow(
            "SELECT id, name FROM tenants WHERE sha256_key = $1",
            hash_key(request.tenant_key)
        )

    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid tenant_key")

    # TODO: put message on Service Bus index-request queue
    return IndexResponse(
        job_id=f"stub-job-{tenant['id']}",
        message=f"Index request accepted for tenant '{tenant['name']}' — project '{request.project_name}' with {len(request.repos)} repos. Processing not yet implemented.",
    )
