"""init: create roles and tenants table

Revision ID: 001
Revises:
Create Date: 2026-08-25
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Roles ---
    # migration_role: DDL access — CREATE, ALTER, DROP TABLE
    # Only migration_user is a member. FastAPI never uses this role.
    op.execute("CREATE ROLE migration_role")

    # app_role: DML only — SELECT, INSERT, UPDATE, DELETE
    # id-sdlc-base-dev (Managed Identity) is a member.
    # FastAPI runs as this role — cannot drop or alter tables.
    op.execute("CREATE ROLE app_role")

    # --- Users ---
    # migration_user gets DDL via migration_role
    op.execute("CREATE USER migration_user")
    op.execute("GRANT migration_role TO migration_user")

    # Managed Identity gets DML only via app_role
    # The identity name in PostgreSQL matches the Azure Managed Identity display name
    op.execute('GRANT app_role TO "id-sdlc-base-dev"')

    # --- Schema privileges ---
    # migration_role can create and manage objects in public schema
    op.execute("GRANT CREATE ON SCHEMA public TO migration_role")
    op.execute("GRANT USAGE ON SCHEMA public TO migration_role")

    # app_role can query objects but not create or drop them
    op.execute("GRANT USAGE ON SCHEMA public TO app_role")

    # --- Tenants table ---
    # Minimal for now: id + name only.
    # More columns added in future migrations (tier, org_code, endpoints, etc.)
    op.execute("""
        CREATE TABLE tenants (
            id   VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL
        )
    """)

    # Grant DML on tenants table to app_role
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE tenants TO app_role")

    # Default privileges: any future table created by migration_role
    # automatically grants DML to app_role — no need to grant per table
    op.execute("ALTER DEFAULT PRIVILEGES FOR ROLE migration_role GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_role")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP USER IF EXISTS migration_user")
    op.execute("DROP ROLE IF EXISTS migration_role")
    op.execute("DROP ROLE IF EXISTS app_role")
