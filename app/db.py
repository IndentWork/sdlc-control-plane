import os
from contextlib import asynccontextmanager

import asyncpg
from alembic.config import Config
from alembic import command


def _is_local() -> bool:
    """Returns True when running in local dev (Docker Compose). False in Azure."""
    return os.environ.get("LOCAL_DEV", "false").lower() == "true"


def _get_token() -> str:
    """Get a short-lived Azure AD token for PostgreSQL using the Managed Identity."""
    from azure.identity import DefaultAzureCredential
    client_id = os.environ["AZURE_CLIENT_ID"]
    credential = DefaultAzureCredential(managed_identity_client_id=client_id)
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    return token.token


def _get_password() -> str:
    """
    Returns DB password — either a regular password (local dev) or
    a short-lived Azure AD token (production with Managed Identity).
    """
    if _is_local():
        return os.environ["POSTGRES_PASSWORD"]
    return _get_token()


def _get_db_user() -> str:
    """Returns DB username — local user or Managed Identity name."""
    if _is_local():
        return os.environ["POSTGRES_USER"]
    return "id-sdlc-base-dev"


@asynccontextmanager
async def get_db_session():
    """
    Async context manager providing a raw asyncpg connection.
    Local dev: connects with username + password.
    Azure: connects with Managed Identity token as password.
    """
    host = os.environ["POSTGRES_HOST"]
    db = os.environ.get("POSTGRES_DB", "sdlc")

    conn = await asyncpg.connect(
        host=host,
        database=db,
        user=_get_db_user(),
        password=_get_password(),
    )
    try:
        yield conn
    finally:
        await conn.close()


async def run_migrations():
    """
    Run all pending Alembic migrations on startup.
    Alembic uses the same connection logic — password locally, token in Azure.
    """
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
