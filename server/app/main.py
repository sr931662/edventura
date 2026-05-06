from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
import uuid

from app.core.config import settings
from app.core.database import engine, Base
from app.core.permissions import PermissionChecker
from app.core.deps import get_current_user
from app.core.middleware import tenant_middleware
from app.core.security import decode_and_validate_token
from app.models.user import User
from app.models.tenant import Tenant
from app.models.class_ import Class
from app.models.student import Student, Guardian
from app.modules.finance.router import router as finance_router

# Import all modules so their models are registered
import app.models
import app.models.attendance_models
import app.models.gamification_models

from app.modules.auth.router import router as auth_router
from app.modules.superadmin.router import router as admin_router
from app.modules.student.router import router as student_router
from app.modules.attendance.router import router as attendance_router
from app.modules.gamification.router import router as gamification_router

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.staticfiles import StaticFiles
import os
from app.modules.communication.router import router as communication_router

from app.modules.assistant.router import router as assistant_router

os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "reports"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "certificates"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "transcripts"), exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://app.ed-ventura.in",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

app.middleware("http")(tenant_middleware)

from app.core.database import engine
from app.core.redis import redis_client
from sqlalchemy import text

@app.get("/health", tags=["system"])
async def health_check():
    checks = {"api": "ok", "database": "unknown", "redis": "unknown"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    status_code = 200 if all(v == "ok" for v in checks.values()) else 503
    return JSONResponse(content=checks, status_code=status_code)

app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")

# Mount routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(student_router, prefix=settings.API_V1_PREFIX)
app.include_router(attendance_router, prefix=settings.API_V1_PREFIX)
app.include_router(gamification_router, prefix=settings.API_V1_PREFIX)
app.include_router(finance_router, prefix=settings.API_V1_PREFIX)
app.include_router(communication_router, prefix=settings.API_V1_PREFIX)
app.include_router(assistant_router,
                    prefix=f"{settings.API_V1_PREFIX}/assistant",
                    tags=["🌼 Daisy Assistant"])
# Temporary test endpoint
@app.get("/test/students", dependencies=[Depends(PermissionChecker("student:read"))])



async def test_student_access(current_user: User = Depends(get_current_user)):
    return {"msg": "You have student:read permission"}

# Auto-create tables (dev only)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.core.database import async_session_factory
    from app.core.security import get_password_hash
    import asyncio
    from app.modules.communication.services.event_consumer import consume_events
    asyncio.create_task(consume_events())

    async with async_session_factory() as session:
        result = await session.execute(select(Tenant).limit(1))
        if not result.scalar_one_or_none():
            tenant = Tenant(
                id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                name="EdVentura Inc.",
                domain="edventura",
            )
            session.add(tenant)
            await session.flush()

            admin = User(
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                full_name="Super Admin",
                is_super_admin=True,
                is_active=True,
                tenant_id=tenant.id,
            )
            session.add(admin)
            await session.commit()