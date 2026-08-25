import os
from contextlib import asynccontextmanager

import asyncpg
from alembic.config import Config
from alembic import command
from azure.identity import DefaultAzureCredential


def _get_token() -> str:
    """Get a short-lived Azure AD token for PostgreSQL using the Managed Identity."""
    client_id = os.environ["AZURE_CLIENT_ID"]
    credential = DefaultAzureCredential(managed_identity_client_id=client_id)
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    return token.token


def get_db_url() -> str:
    """
    Build PostgreSQL connection URL using Managed Identity token.
    FastAPI connects as id-sdlc-base-dev which has app_role (DML only).
    Token is short-lived and auto-rotated by Azure — no password needed.
    """
    host = os.environ["POSTGRES_HOST"]
    return f"postgresql+asyncpg://id-sdlc-base-dev:{_get_token()}@{host}/sdlc"


@asynccontextmanager
async def get_db_session():
    """
    Async context manager that provides a raw asyncpg connection.
    Token is fetched fresh per request — tokens expire in ~1 hour.
    Usage:
        async with get_db_session() as conn:
            rows = await conn.fetch("SELECT ...")
    """
    host = os.environ["POSTGRES_HOST"]
    conn = await asyncpg.connect(
        host=host,
        database="sdlc",
        user="id-sdlc-base-dev",
        password=_get_token(),
    )
    try:
        yield conn
    finally:
        await conn.close()


async def run_migrations():
    """
    Run all pending Alembic migrations on startup.
    Alembic connects as the Managed Identity (Azure AD admin) — has DDL access.
    """
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
