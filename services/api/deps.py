from fastapi import Header, HTTPException


def require_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    """Stands in for a real auth layer: every tenant-scoped request in this
    demo carries the caller's tenant as a header instead of a session."""
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="missing X-Tenant-Id")
    return x_tenant_id
