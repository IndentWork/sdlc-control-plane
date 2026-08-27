# sdlc-control-plane

FastAPI management API for the SDLC platform. Serves the public HTTP endpoints that tenants call to onboard, index their code, and check status.

Runs as a Container App inside the base VNet. Connects to Azure PostgreSQL passwordlessly via Managed Identity.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/tenants` | Create a tenant, returns plaintext `tenant_key` once |
| GET | `/tenants` | List all tenants (no keys exposed) |
| GET | `/tenants/{id}` | Get a specific tenant |
| DELETE | `/tenants/{id}` | Delete a tenant (idempotent) |
| POST | `/index` | Request an indexing job — requires valid `tenant_key` |
| GET | `/docs` | Swagger UI |

## Architecture

```
app/
├── main.py            FastAPI wiring, runs migrations on startup
├── db.py              PostgreSQL connection (Managed Identity in Azure, password locally)
├── security.py        hash_key helper (SHA256)
├── models/            SQLAlchemy DB models
├── schemas/           Pydantic request/response schemas
└── routers/           API endpoints (thin — just routes)

migrations/            Alembic migrations
├── env.py             DB URL builder (token vs password based on LOCAL_DEV env)
└── versions/
    ├── 001_init.py           Roles + tenants table
    └── 002_add_tenant_key.py sha256_key column + index
```

## Authentication

- **FastAPI → PostgreSQL** — Managed Identity, no password (Azure) or password (local dev)
- **Tenant → API** — sends plaintext `tenant_key`, server compares `SHA256(key)` against `tenants.sha256_key`
- Plaintext keys are never stored — hashes cannot be reversed if DB leaks

## Running locally

Use the [`sdlc-local-dev`](https://github.com/IndentWork/sdlc-local-dev) repo:

```bash
cd sdlc-local-dev
make service-start
curl http://localhost:8000/health
```

## Deploying to Azure

Via GitHub Actions: **Actions → Deploy Control Plane → Run workflow → select DEV or PROD**

The pipeline:
1. Derives image tag from git SHA (`{branch}-{short_sha}`)
2. Skips build if image already exists in ACR
3. Otherwise builds and pushes to `crsdlc{env}.azurecr.io/control-plane:{tag}`
4. Updates the Container App with the new image

## Environment variables

Set by the Container App (Azure) or docker-compose (local):

| Var | Purpose |
|---|---|
| `POSTGRES_HOST` | PostgreSQL hostname |
| `POSTGRES_DB` | Database name (default `sdlc`) |
| `POSTGRES_USER` | Local dev only |
| `POSTGRES_PASSWORD` | Local dev only |
| `AZURE_CLIENT_ID` | Managed Identity client ID (Azure only) |
| `LOCAL_DEV` | Set to `true` in local dev — switches to password auth |

## Adding a new migration

```bash
uv run alembic revision -m "description"
# Edit migrations/versions/00N_description.py
# Restart the container — migrations run automatically on startup
```

## Adding a new endpoint

1. Add schemas to `app/schemas/<resource>.py`
2. Add routes to `app/routers/<resource>.py`
3. Register the router in `app/main.py`
4. Add e2e tests in `sdlc-e2e/tests/`
