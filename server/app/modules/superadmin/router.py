from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.class_ import Class
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import user_roles
from app.core.security import get_password_hash
import uuid
from app.models.role_permission import role_permissions   # add this import


router = APIRouter(prefix="/admin", tags=["Admin/Seed"])

# A helper to ensure only super admins can access
async def super_admin_only(current_user: User = Depends(get_current_user)):
    if not current_user.is_super_admin: # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(status_code=403, detail="Super admin only")
    return current_user



@router.post("/roles", status_code=201)
async def create_role(
    name: str,
    description: str = "",
    is_system: bool = True,
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    role = Role(name=name, description=description, is_system=is_system, tenant_id=user.tenant_id)   # global roles
    db.add(role)
    await db.commit()
    return {"id": str(role.id), "name": name}

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_name: str
    tenant_id: Optional[str] = None
    phone: str = ""

@router.post("/users", status_code=201)
async def create_user(
    payload: UserCreate,
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    # Ensure tenant exists
    tid = payload.tenant_id or user.tenant_id
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    # Find role
    role = (await db.execute(select(Role).where(Role.name == payload.role_name))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    # Check duplicate email
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=True,
        tenant_id=tid,
    )
    db.add(new_user)
    await db.flush()  # get user id

    # Assign role
    ins = user_roles.insert().values(user_id=new_user.id, role_id=role.id, tenant_id=tid)
    await db.execute(ins)
    await db.commit()

    return {"id": str(new_user.id), "email": payload.email, "role": payload.role_name}


class ClassCreate(BaseModel):
    name: str

@router.post("/classes", status_code=201)
async def create_class(
    payload: ClassCreate,
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    cls = Class(name=payload.name, tenant_id=user.tenant_id)
    db.add(cls)
    await db.commit()
    return {"id": str(cls.id), "name": cls.name}

@router.post("/permissions", status_code=201)
async def create_permission(
    codename: str,
    description: str = "",
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    # Ensure codename is unique
    existing = (await db.execute(select(Permission).where(Permission.codename == codename))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")
    perm = Permission(codename=codename, description=description, tenant_id=user.tenant_id)
    db.add(perm)
    await db.commit()
    return {"id": str(perm.id), "codename": codename}

@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: str,
    permission_codenames: List[str],
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    perms_result = await db.execute(
        select(Permission).where(Permission.codename.in_(permission_codenames))
    )
    perms = perms_result.scalars().all()

    # convert codename Column to str for set operation
    found = {str(p.codename) for p in perms}
    missing = set(permission_codenames) - found
    if missing:
        raise HTTPException(status_code=400, detail=f"Permissions not found: {missing}")

    for p in perms:
        # Insert ignoring duplicates
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        ins = pg_insert(role_permissions).values(role_id=role.id, permission_id=p.id).on_conflict_do_nothing()
        await db.execute(ins)
    await db.commit()
    return {"detail": f"Assigned {len(perms)} permissions"}

@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(404, detail="Role not found")
    # Join through role_permissions
    stmt = select(Permission.codename).select_from(role_permissions).join(
        Permission, role_permissions.c.permission_id == Permission.id
    ).where(role_permissions.c.role_id == role.id)
    result = await db.execute(stmt)
    codenames = result.scalars().all()
    return {"codenames": codenames}