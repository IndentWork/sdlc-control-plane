"""add sha256_key column to tenants

Revision ID: 002
Revises: 001
Create Date: 2026-08-27
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sha256_key: SHA256 hash of the tenant's plaintext secret key.
    # Plaintext key is never stored — only the hash for verification.
    # If DB is compromised, hashes cannot be reversed to the original keys.
    op.execute("ALTER TABLE tenants ADD COLUMN sha256_key VARCHAR")

    # Index for fast lookup — every API call from a tenant does this lookup.
    op.execute("CREATE INDEX ix_tenants_sha256_key ON tenants (sha256_key)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenants_sha256_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS sha256_key")
