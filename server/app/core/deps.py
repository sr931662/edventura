from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_and_validate_token, is_token_blacklisted
from app.models.user import User
from app.models.role import Role
from app.models.user_role import user_roles
from sqlalchemy import select
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract user from JWT, validate tenant, return User ORM object."""
    try:
        payload = decode_and_validate_token(token, expected_type="access")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if await is_token_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    # Fetch user with tenant scope
    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user

async def get_current_active_tenant(request: Request, user: User = Depends(get_current_user)) -> str:
    if user.is_super_admin and (tid := request.headers.get("X-Tenant-ID")):
        return tid
    return str(user.tenant_id)  # it's already on the user object
