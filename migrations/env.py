import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from azure.identity import DefaultAzureCredential

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_migration_url() -> str:
    """
    Build PostgreSQL connection URL for migrations using Managed Identity token.
    Connects as id-sdlc-base-dev (Azure AD admin) — has DDL access needed
    to create roles, tables, and grant privileges.
    """
    host = os.environ["POSTGRES_HOST"]
    client_id = os.environ["AZURE_CLIENT_ID"]

    # Get a short-lived token from Azure using the Managed Identity
    credential = DefaultAzureCredential(managed_identity_client_id=client_id)
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

    return f"postgresql+psycopg2://id-sdlc-base-dev:{token.token}@{host}/sdlc"


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_migration_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
