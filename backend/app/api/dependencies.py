from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.models import Tenant


def get_tenant(
    db: Session = Depends(get_db),
    x_tenant_slug: Optional[str] = Header(default=None),
) -> Tenant:
    slug = x_tenant_slug or get_settings().default_tenant_slug
    tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{slug}' was not found",
        )
    return tenant
