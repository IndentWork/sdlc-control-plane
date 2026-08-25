import os
from alembic.config import Config
from alembic import command
from azure.identity import DefaultAzureCredential


def get_db_url() -> str:
    """
    Build PostgreSQL connection URL using Managed Identity token.
    FastAPI connects as id-sdlc-base-dev which has app_role (DML only).
    Token is short-lived and auto-rotated by Azure — no password needed.
    """
    host = os.environ["POSTGRES_HOST"]
    client_id = os.environ["AZURE_CLIENT_ID"]

    # Request a token for PostgreSQL from Azure using the Managed Identity
    credential = DefaultAzureCredential(managed_identity_client_id=client_id)
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

    # asyncpg connection string — token used as password
    return f"postgresql+asyncpg://id-sdlc-base-dev:{token.token}@{host}/sdlc"


async def run_migrations():
    """
    Run all pending Alembic migrations on startup.
    Uses the migration_user (DDL access) — not the app Managed Identity.
    Migration connection string is separate from the app connection.
    """
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
