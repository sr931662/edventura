from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.base import EdVenturaBase
from app.models.role import Role
from app.modules.auth import schemas, service
from app.core.deps import get_current_user, oauth2_scheme
from app.core.security import blacklist_token, decode_and_validate_token, invalidate_refresh_token
from app.core.config import settings
import uuid
from app.models.user import User
from app.models.user_role import user_roles

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request



limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

router = APIRouter(prefix="/auth", tags=["Authentication"])

from app.modules.auth.service import MFARequiredError

@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    try:
        access, refresh, user = await svc.authenticate(
            req.email, req.password, req.tenant_domain, req.mfa_code, req.keep_logged_in
        )
    except MFARequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={"mfa_required": True, "user_id": e.user_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return schemas.TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    req: schemas.RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    svc = service.AuthService(db)
    try:
        access, new_refresh = await svc.refresh_tokens(req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return schemas.TokenResponse(access_token=access, refresh_token=new_refresh)

from pydantic import BaseModel

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.post("/logout")
async def logout(
    req: LogoutRequest,
    token: str = Depends(oauth2_scheme),
):
    payload = decode_and_validate_token(token, expected_type="access")
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    await blacklist_token(jti, ttl=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    if req.refresh_token:
        await invalidate_refresh_token(req.refresh_token)
    return {"detail": "Logged out successfully"}

@router.post("/mfa/setup", response_model=schemas.MFASetupResponse)
async def setup_mfa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = service.AuthService(db)
    uri = await svc.enable_mfa(uuid.UUID(str(user.id)))
    # Refresh user from DB to get the pending secret just set
    await db.refresh(user)
    return {"secret": str(user.mfa_pending_secret), "qr_code_uri": uri}

@router.post("/mfa/verify")
async def verify_mfa(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = service.AuthService(db)
    if not await svc.verify_mfa(uuid.UUID(str(user.id)), code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    return {"detail": "MFA verified"}

    
from pydantic import BaseModel

class DebugTokenRequest(BaseModel):
    token: str


@router.get("/me")
async def read_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch actual roles from the DB for the current user + tenant
    stmt = (
        select(Role.name)
        .select_from(user_roles)
        .join(Role, user_roles.c.role_id == Role.id)
        .where(
            user_roles.c.user_id == current_user.id,
            user_roles.c.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(stmt)
    role_names = [row[0] for row in result.fetchall()]

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "tenant_id": str(current_user.tenant_id),
        "is_active": current_user.is_active,
        "is_super_admin": current_user.is_super_admin,
        "roles": role_names
    }