"""create tenant_github_repos table

Stores the list of GitHub repos a tenant is allowed to call the API from.
If no rows exist for a tenant, any repo in their org is allowed (wildcard).
Repos are populated by the tenant's sdlc-project pipeline reading project.yml.

Revision ID: 004
Revises: 003
Create Date: 2026-08-30
"""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE tenant_github_repos (
            id         VARCHAR PRIMARY KEY,
            tenant_id  VARCHAR NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            repo_name  VARCHAR NOT NULL,
            UNIQUE (tenant_id, repo_name)
        )
    """)

    # Index for fast lookup — every /index request checks allowed repos.
    op.execute("CREATE INDEX ix_tenant_github_repos_tenant_id ON tenant_github_repos (tenant_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenant_github_repos_tenant_id")
    op.execute("DROP TABLE IF EXISTS tenant_github_repos")
