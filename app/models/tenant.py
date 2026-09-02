import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    """
    Tenant registry — one row per onboarded tenant.
    Auth is GitHub OIDC: we store github_org and validate incoming JWT sub claims.
    No secrets are stored — the OIDC token is verified against GitHub's public keys.
    """
    __tablename__ = "tenants"

    id:         Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name:       Mapped[str] = mapped_column(String, nullable=False)
    github_org: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class TenantGithubRepo(Base):
    """
    Allowed repos for a tenant. If no rows exist, any repo in the org is permitted.
    Populated by the tenant's sdlc-project pipeline via PUT /tenants/repos.
    """
    __tablename__ = "tenant_github_repos"

    id:        Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    repo_name: Mapped[str] = mapped_column(String, nullable=False)
