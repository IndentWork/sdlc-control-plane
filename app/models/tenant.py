import uuid
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    """
    Tenant registry — one row per onboarded tenant.
    Keeping it minimal for now: just id and name.
    More columns (tier, org_code, endpoints) added in future migrations.
    """
    __tablename__ = "tenants"

    id:   Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
