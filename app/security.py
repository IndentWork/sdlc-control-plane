"""
GitHub OIDC token validation — FastAPI dependency for authenticated endpoints.

How it works:
  1. Tenant pipeline requests a short-lived OIDC token from GitHub
     (permissions: id-token: write in the workflow)
  2. Token is sent as "Authorization: Bearer <token>" to our API
  3. We validate the token signature against GitHub's public keys (JWKS)
  4. We extract the GitHub org and repo from the token claims
  5. We look up the tenant in our DB by github_org
  6. We check if the repo is registered (or allow all if no rows exist)
  7. We return the tenant — route handlers receive it via Depends(verified_tenant)
"""
import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException

from app.db import get_db_session

# GitHub's OIDC issuer — all GitHub Actions tokens are signed by this authority.
_GITHUB_ISSUER = "https://token.actions.githubusercontent.com"

# Audience must match what the tenant requests when fetching their OIDC token.
# The tenant workflow uses: &audience=sdlc-control-plane
_EXPECTED_AUDIENCE = "sdlc-control-plane"

# PyJWKClient fetches GitHub's public keys once and caches them.
# It automatically refreshes when it encounters a key ID it hasn't seen before.
_jwks_client = PyJWKClient(f"{_GITHUB_ISSUER}/.well-known/jwks")


def _extract_bearer_token(authorization: str) -> str:
    """Pull the raw token string out of 'Bearer <token>'."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must use 'Bearer <token>' scheme",
        )
    return authorization[len("Bearer "):]


def _decode_and_validate(token: str) -> dict:
    """
    Validate the JWT signature using GitHub's JWKS and verify standard claims.
    Raises 401 for any validation failure — expired, wrong issuer, wrong audience, bad signature.
    """
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_EXPECTED_AUDIENCE,
            issuer=_GITHUB_ISSUER,
        )
    except jwt.exceptions.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


def _extract_org_and_repo(claims: dict) -> tuple[str, str]:
    """
    Pull github_org and repo_name out of the token claims.
    claims["repository_owner"] = "acme-corp"
    claims["repository"]       = "acme-corp/payments-service"
    """
    github_org = claims.get("repository_owner", "")
    repository = claims.get("repository", "/")
    # repository is always "org/repo" — we only need the repo part
    repo_name = repository.split("/", 1)[-1]

    if not github_org or not repo_name:
        raise HTTPException(status_code=401, detail="Token is missing repository claims")

    return github_org, repo_name


async def _lookup_tenant(github_org: str, repo_name: str) -> dict:
    """
    Find the tenant by github_org and verify the repo is allowed to call the API.

    Allowed-repo logic:
      - If tenant_github_repos has NO rows for this tenant → all repos in the org are allowed.
      - If rows exist → only listed repos are allowed.

    This lets a tenant start with unrestricted access and lock it down later by
    populating project.yml in their sdlc-config repo.
    """
    async with get_db_session() as conn:
        tenant = await conn.fetchrow(
            "SELECT id, name, github_org, tier, resource_code FROM tenants WHERE github_org = $1",
            github_org,
        )

        if tenant is None:
            raise HTTPException(status_code=401, detail="GitHub org is not registered")

        allowed_repos = await conn.fetch(
            "SELECT repo_name FROM tenant_github_repos WHERE tenant_id = $1",
            tenant["id"],
        )

        # No rows → allow all repos in the org (wildcard)
        if allowed_repos:
            allowed_names = {row["repo_name"] for row in allowed_repos}
            if repo_name not in allowed_names:
                raise HTTPException(
                    status_code=401,
                    detail=f"Repo '{repo_name}' is not registered for this tenant",
                )

    return dict(tenant)


async def verified_tenant(authorization: str = Header(...)) -> dict:
    """
    FastAPI dependency — validates a GitHub OIDC token and returns the tenant.

    Usage in a route:
        @router.post("")
        async def my_endpoint(tenant: dict = Depends(verified_tenant)):
            ...

    Raises 401 for: missing header, bad token, expired token,
                    unknown org, unregistered repo.
    """
    token = _extract_bearer_token(authorization)
    claims = _decode_and_validate(token)
    github_org, repo_name = _extract_org_and_repo(claims)
    return await _lookup_tenant(github_org, repo_name)
