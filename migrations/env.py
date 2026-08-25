import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _is_local() -> bool:
    return os.environ.get("LOCAL_DEV", "false").lower() == "true"


def get_migration_url() -> str:
    """
    Build PostgreSQL connection URL for migrations.
    Local dev: uses regular password.
    Azure: uses Managed Identity token — connects as Azure AD admin with DDL access.
    """
    host = os.environ["POSTGRES_HOST"]
    db = os.environ.get("POSTGRES_DB", "sdlc")

    if _is_local():
        user = os.environ["POSTGRES_USER"]
        password = os.environ["POSTGRES_PASSWORD"]
    else:
        from azure.identity import DefaultAzureCredential
        client_id = os.environ["AZURE_CLIENT_ID"]
        credential = DefaultAzureCredential(managed_identity_client_id=client_id)
        token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        user = "id-sdlc-base-dev"
        password = token.token

    return f"postgresql+psycopg2://{user}:{password}@{host}/{db}"


def run_migrations_online() -> None:
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
