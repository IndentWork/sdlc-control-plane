"""add resource_code to tenants

resource_code is a short deterministic identifier derived from SHA256(github_org)[:8].
Used to name Azure resources for dedicated tenants (VNet, PostgreSQL, Key Vault).
Example: github_org="sdlc-tenant" → resource_code="a3f1c2b4"
         → vnet-sdlc-a3f1c2b4-dev, psql-sdlc-a3f1c2b4-dev, kv-sdlc-a3f1c2b4-dev

Stored in the DB so resource names are always reproducible without re-computing.
UNIQUE constraint catches the rare SHA256 prefix collision at onboarding time.

Revision ID: 006
Revises: 005
Create Date: 2026-09-02
"""
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN resource_code VARCHAR(8) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE tenants ALTER COLUMN resource_code DROP DEFAULT")
    op.execute("CREATE UNIQUE INDEX ix_tenants_resource_code ON tenants (resource_code) WHERE resource_code != ''")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenants_resource_code")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS resource_code")
