import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import index, tenants, tenant
from app.db import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup before serving any requests.
    # This ensures the schema is always up to date when the container starts.
    await run_migrations()
    yield


app = FastAPI(
    title="SDLC Control Plane",
    description="Management API — tenant registry and indexing requests",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(index.router)
app.include_router(tenants.router)
app.include_router(tenant.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
