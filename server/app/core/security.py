import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from jose.exceptions import JOSEError
from redis.asyncio import Redis
import pyotp
import bcrypt
import hashlib
from app.core.config import settings

from app.core.redis import redis_client

# Redis client for token blacklisting & refresh storage
# redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# --------------- Password Utilities ---------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# --------------- JWT Utilities ---------------
def create_jwt_token(
    subject: str | uuid.UUID,
    tenant_id: str | uuid.UUID,
    roles: Optional[list[str]] = None,
    permissions: Optional[list[str]] = None,
    token_type: str = "access",
    refresh_expire_days: int | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        days = refresh_expire_days if refresh_expire_days is not None else settings.REFRESH_TOKEN_EXPIRE_DAYS
        expire = now + timedelta(days=days)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "iat": now,
        "exp": expire,
        "type": token_type,
        "jti": str(uuid.uuid4()),
    }
    if roles:
        to_encode["roles"] = roles
    if permissions:
        to_encode["permissions"] = permissions

    
    return jwt.encode(to_encode, settings.JWT_PRIVATE_KEY or "", algorithm=settings.JWT_ALGORITHM)

def decode_and_validate_token(token: str, expected_type: str | None) -> dict:
    """Decodes a JWT and verifies signature, expiry. Does NOT check blacklist."""
    try:
        if not settings.JWT_PUBLIC_KEY:
            raise ValueError("JWT_PUBLIC_KEY is not configured")

        # payload = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=[settings.JWT_ALGORITHM], options={"verify_exp": True})
        payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM], options={"verify_exp": True})
        if expected_type and payload.get("type") != expected_type:
            raise ValueError(f"Expected {expected_type} token")
        return payload
    except (JWTError, JOSEError) as e:
        raise ValueError(f"Invalid token: {str(e)}") from e

async def is_token_blacklisted(jti: str) -> bool:
    try:
        return await redis_client.exists(f"blacklist:{jti}") > 0
    except Exception:
        return False

async def blacklist_token(jti: str, ttl: int | None = None):
    """Add a token to blacklist set. ttl should match token expiry."""
    try:
        await redis_client.setex(f"blacklist:{jti}", ttl or 3600, "1")
    except Exception:
        pass

# --------------- Refresh Token Management ---------------
async def store_refresh_token(user_id: str, tenant_id: str, refresh_token: str, ttl: int | None = None):
    """Store refresh token hash in Redis for rotation."""
    if ttl is None:
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    try:
        await redis_client.setex(f"refresh:{_hash_token(refresh_token)}", ttl, f"{user_id}:{tenant_id}")
    except Exception:
        pass  # Redis unavailable — token rotation disabled, acceptable in dev

async def invalidate_refresh_token(refresh_token: str):
    try:
        await redis_client.delete(f"refresh:{_hash_token(refresh_token)}")
    except Exception:
        pass

async def get_refresh_token_data(refresh_token: str) -> Optional[tuple[str, str]]:
    try:
        data = await redis_client.get(f"refresh:{_hash_token(refresh_token)}")
        if data:
            user_id, tenant_id = data.split(":", 1)
            return user_id, tenant_id
    except Exception:
        pass
    return None

# --------------- MFA Utilities ---------------
def generate_mfa_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.MFA_ISSUER
    )

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)