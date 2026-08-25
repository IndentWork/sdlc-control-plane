FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first — Docker layer cache: only reinstalls if these change
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Run migrations first, then start FastAPI.
# Migrations run as Managed Identity (AD admin) — creates roles and tables if needed.
# FastAPI then starts as app_role (DML only) — cannot drop or alter tables.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
