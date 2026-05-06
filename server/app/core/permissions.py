from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import user_roles
from app.models.role_permission import role_permissions
from app.core.config import settings
from sqlalchemy import select
import json
from redis.asyncio import Redis   # change import

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_user_permissions(user_id: str, tenant_id: str, db: AsyncSession) -> set[str]:
    cache_key = f"perms:{user_id}:{tenant_id}"
    cached = await redis_client.get(cache_key)
    if cached is not None:
        # `cached` is str because decode_responses=True
        return set(json.loads(cached))

    # Super admin has all permissions
    user = await db.get(User, user_id)
    if user and user.is_super_admin:  # type: ignore[reportGeneralTypeIssues]
        all_perms = (await db.execute(select(Permission.codename))).scalars().all()
        perms = set(str(p) for p in all_perms)  # convert to str
    else:
        stmt = (
            select(Permission.codename)
            .select_from(user_roles)
            .join(role_permissions, user_roles.c.role_id == role_permissions.c.role_id)
            .join(Permission, role_permissions.c.permission_id == Permission.id)
            .where(
                user_roles.c.user_id == user_id,
                user_roles.c.tenant_id == tenant_id
            )
        )
        result = await db.execute(stmt)
        perms = set(str(p) for p in result.scalars().all())

    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(list(perms)))
    return perms

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # First try middleware
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            # Next, extract from token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                try:
                    from app.core.security import decode_and_validate_token
                    payload = decode_and_validate_token(auth_header.split(" ")[1], expected_type="access")
                    tenant_id = payload.get("tenant_id")
                except Exception:
                    pass
        if not tenant_id:
            # Final fallback: use the user's own tenant_id from DB
            # This is safe for non-superadmins; superadmins might have a "default" tenant
            if current_user.tenant_id is not None:
                tenant_id = str(current_user.tenant_id)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not resolved"
            )

        permissions = await get_user_permissions(str(current_user.id), tenant_id, db)
        if self.required_permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return current_user

# Usage example: 
# @router.get("/students", dependencies=[Depends(PermissionChecker("student:read"))])