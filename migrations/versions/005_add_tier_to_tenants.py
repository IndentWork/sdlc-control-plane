"""add tier to tenants

Tracks whether the tenant is on shared or dedicated infrastructure.
Shared: cost-effective, shared Azure resources with metadata isolation.
Dedicated: own VNet, own resources, full isolation (higher cost).

Revision ID: 005
Revises: 004
Create Date: 2026-09-02
"""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tier is set at onboarding time and rarely changes.
    # Constraint ensures only valid values are stored.
    op.execute("ALTER TABLE tenants ADD COLUMN tier VARCHAR NOT NULL DEFAULT 'shared'")
    op.execute("ALTER TABLE tenants ALTER COLUMN tier DROP DEFAULT")
    op.execute("ALTER TABLE tenants ADD CONSTRAINT tenants_tier_check CHECK (tier IN ('shared', 'dedicated'))")


def downgrade() -> None:
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_tier_check")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS tier")
