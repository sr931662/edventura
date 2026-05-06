import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.tenant import Tenant
from app.core.config import settings
from app.core.security import (
    decode_and_validate_token,
    verify_password,
    create_jwt_token,
    store_refresh_token,
    invalidate_refresh_token,
    get_refresh_token_data,
    generate_mfa_secret,
    get_totp_uri,
    verify_totp
)
from app.models.role import Role
from app.models.user_role import user_roles as user_roles_table


class MFARequiredError(Exception):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"MFA required for user {user_id}")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _fetch_roles(self, user_id, tenant_id) -> list[str]:
        stmt = (
            select(Role.name)
            .select_from(user_roles_table)
            .join(Role, user_roles_table.c.role_id == Role.id)
            .where(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def authenticate(
        self,
        email: str,
        password: str,
        tenant_domain: Optional[str] = None,
        mfa_code: Optional[str] = None,
        keep_logged_in: bool = False,
    ) -> tuple:
        # 1. Find user by email
        stmt = select(User).where(
            User.email == email,
            User.is_active == True,
            User.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, str(user.hashed_password)):
            raise ValueError("Invalid credentials")

        # 2. Enforce MFA if enabled
        if user.mfa_enabled:  # type: ignore[reportGeneralTypeIssues]
            if mfa_code is None:
                raise MFARequiredError(user_id=str(user.id))
            if user.mfa_secret is None or not verify_totp(str(user.mfa_secret), mfa_code):
                raise ValueError("Invalid MFA code")

        # 3. Determine tenant
        if user.is_super_admin:  # type: ignore[reportGeneralTypeIssues]
            if tenant_domain:
                tenant_res = await self.db.execute(
                    select(Tenant).where(Tenant.domain == tenant_domain)
                )
                tenant = tenant_res.scalar_one_or_none()
                if not tenant:
                    raise ValueError("Tenant not found")
                tenant_id = tenant.id
            else:
                tenant_res = await self.db.execute(select(Tenant).limit(1))
                tenant = tenant_res.scalar_one_or_none()
                if not tenant:
                    raise ValueError("No tenants exist")
                tenant_id = tenant.id
        else:
            tenant_id = user.tenant_id  # type: ignore[reportGeneralTypeIssues]

        # 4. Fetch real roles from DB
        roles = await self._fetch_roles(user.id, tenant_id)

        # 5. Create tokens
        refresh_days = 30 if keep_logged_in else None
        access_token = create_jwt_token(
            subject=str(user.id),
            tenant_id=str(tenant_id),
            roles=roles,
            token_type="access",
        )
        refresh_token = create_jwt_token(
            subject=str(user.id),
            tenant_id=str(tenant_id),
            token_type="refresh",
            refresh_expire_days=refresh_days,
        )
        redis_ttl = (refresh_days or settings.REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 3600
        await store_refresh_token(str(user.id), str(tenant_id), refresh_token, ttl=redis_ttl)

        return access_token, refresh_token, user

    async def refresh_tokens(self, old_refresh_token: str) -> tuple:
        try:
            payload = decode_and_validate_token(old_refresh_token, expected_type="refresh")
        except ValueError:
            raise ValueError("Invalid refresh token signature")

        # Extract identity from JWT payload directly — Redis is used for revocation only
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise ValueError("Invalid refresh token")

        # Rotation: invalidate old token before issuing new one
        await invalidate_refresh_token(old_refresh_token)

        user = await self.db.get(User, user_id)
        if not user or not user.is_active:  # type: ignore[reportGeneralTypeIssues]
            raise ValueError("User inactive")

        # Re-fetch roles so the new access token is never empty
        roles = await self._fetch_roles(user.id, tenant_id)

        access_token = create_jwt_token(
            subject=str(user.id),
            tenant_id=tenant_id,
            roles=roles,
            token_type="access",
        )
        new_refresh_token = create_jwt_token(
            subject=str(user.id),
            tenant_id=tenant_id,
            token_type="refresh",
        )
        await store_refresh_token(str(user.id), tenant_id, new_refresh_token)

        return access_token, new_refresh_token

    async def enable_mfa(self, user_id: uuid.UUID) -> str:
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        secret = generate_mfa_secret()
        user.mfa_pending_secret = secret  # type: ignore[reportAttributeAccessIssue]
        user.mfa_enabled = False  # type: ignore[reportAttributeAccessIssue]
        await self.db.commit()
        return get_totp_uri(secret, str(user.email))

    async def verify_mfa(self, user_id: uuid.UUID, code: str) -> bool:
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        pending = user.mfa_pending_secret  # type: ignore[reportGeneralTypeIssues]
        active = user.mfa_secret  # type: ignore[reportGeneralTypeIssues]
        secret_to_check = pending if pending is not None else active
        if secret_to_check is None:
            return False

        valid = verify_totp(str(secret_to_check), code)
        if valid and user.mfa_pending_secret is not None:  # type: ignore[reportGeneralTypeIssues]
            user.mfa_secret = user.mfa_pending_secret  # type: ignore[reportAttributeAccessIssue]
            user.mfa_pending_secret = None  # type: ignore[reportAttributeAccessIssue]
            user.mfa_enabled = True  # type: ignore[reportAttributeAccessIssue]
            await self.db.commit()
        return valid
