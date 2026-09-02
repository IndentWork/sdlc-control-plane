# Database Schema

**Database:** `sdlc` (PostgreSQL 16)
**Host:** `psql-sdlc-base-{env}.postgres.database.azure.com`

---

## Tables

### `tenants`

One row per onboarded tenant. This is the central registry.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | UUID generated at creation time |
| `name` | VARCHAR | NOT NULL | Human-readable org name, e.g. "Acme Corp" |
| `github_org` | VARCHAR | NOT NULL, UNIQUE | GitHub organisation slug, e.g. "acme-corp". Used to match incoming OIDC tokens |

**Indexes:**
- `ix_tenants_github_org` — unique partial index on `github_org WHERE github_org != ''`

**How a tenant is identified at request time:**
The GitHub OIDC token contains `repository_owner = "acme-corp"`. FastAPI looks up the tenant by matching `github_org = "acme-corp"`. No password or secret is stored.

---

### `tenant_github_repos`

The list of repos in a tenant's org that are allowed to call the API.
Populated by the tenant's `sdlc-config` pipeline when they push `project.yml`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | UUID generated at creation time |
| `tenant_id` | VARCHAR | NOT NULL, FK → `tenants.id` ON DELETE CASCADE | Which tenant owns this repo |
| `repo_name` | VARCHAR | NOT NULL | Repo name only, e.g. "payments-service" (no org prefix) |

**Constraints:**
- `UNIQUE (tenant_id, repo_name)` — a repo can only be registered once per tenant

**Indexes:**
- `ix_tenant_github_repos_tenant_id` — for fast lookup on every `/index` request

**Allowed-repo logic (enforced in `app/security.py`):**

| State | Behaviour |
|---|---|
| No rows for this tenant | All repos in the org are allowed (wildcard — used at onboarding before `project.yml` is pushed) |
| Rows exist | Only listed repos can call the API |

---

## Roles and Users

Defined in migration 001. FastAPI never touches roles or DDL.

| Name | Type | Permissions | Used by |
|---|---|---|---|
| `migration_role` | Role | CREATE, ALTER, DROP on public schema | Alembic migrations |
| `app_role` | Role | SELECT, INSERT, UPDATE, DELETE on all tables | FastAPI at runtime |
| `migration_user` | User | Member of `migration_role` | Alembic (local dev only) |
| `id-sdlc-base-dev` | Azure Managed Identity | Member of `app_role` | FastAPI Container App on Azure |

**Why two roles?**
FastAPI runs as `app_role` which has DML only — it cannot drop or alter tables.
Even if FastAPI is compromised, an attacker cannot destroy the schema.

---

## Migration History

| # | File | What it does |
|---|---|---|
| 001 | `001_init.py` | Creates roles, users, and the initial `tenants` table (`id`, `name`) |
| 002 | `002_add_tenant_key.py` | Added `sha256_key` column — **superseded by 003** |
| 003 | `003_replace_key_with_github_org.py` | Drops `sha256_key`, adds `github_org`. SHA256 auth replaced by GitHub OIDC |
| 004 | `004_create_tenant_github_repos.py` | Creates `tenant_github_repos` table for per-repo access control |

---

## Entity Relationship

```
tenants
├── id           (PK)
├── name
└── github_org   (UNIQUE)
        │
        │ 1 ──── N
        ▼
tenant_github_repos
├── id
├── tenant_id    (FK → tenants.id, CASCADE DELETE)
└── repo_name
```
