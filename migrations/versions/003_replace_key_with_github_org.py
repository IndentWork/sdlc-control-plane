"""drop sha256_key, add github_org to tenants

SHA256 key auth is replaced by GitHub OIDC — no stored secret needed.
Tenants are now identified by their GitHub organisation name, which is
extracted from the OIDC token sub claim at request time.

Revision ID: 003
Revises: 002
Create Date: 2026-08-30
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove SHA256 key auth entirely.
    op.execute("DROP INDEX IF EXISTS ix_tenants_sha256_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS sha256_key")

    # github_org: the tenant's GitHub organisation name (e.g. "acme-corp").
    # Added with a temporary default so existing rows are not rejected.
    # Default is dropped immediately after — the app layer enforces NOT NULL.
    op.execute("ALTER TABLE tenants ADD COLUMN github_org VARCHAR NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE tenants ALTER COLUMN github_org DROP DEFAULT")

    # Unique — one tenant per GitHub org.
    # We do not index empty strings from legacy rows; they will be cleaned up.
    op.execute("CREATE UNIQUE INDEX ix_tenants_github_org ON tenants (github_org) WHERE github_org != ''")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenants_github_org")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS github_org")
    op.execute("ALTER TABLE tenants ADD COLUMN sha256_key VARCHAR")
    op.execute("CREATE INDEX ix_tenants_sha256_key ON tenants (sha256_key)")
