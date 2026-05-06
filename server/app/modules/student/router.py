from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_active_tenant
from app.core.permissions import PermissionChecker
from app.modules.superadmin.router import super_admin_only
from app.modules.student import schemas, service
from app.models.user import User

router = APIRouter(prefix="/students", tags=["Student Management"])
from app.models.class_ import Class   # add at top

@router.post("/classes", status_code=201)
async def create_class(
    name: str,
    user: User = Depends(super_admin_only),
    db: AsyncSession = Depends(get_db)
):
    # tenant_id from the super admin's own tenant (default)
    cls = Class(name=name, tenant_id=user.tenant_id)
    db.add(cls)
    await db.commit()
    return {"id": str(cls.id), "name": name}

@router.post("/", response_model=schemas.StudentOut, status_code=201,
             dependencies=[Depends(PermissionChecker("student:create"))])
async def create_student(
    data: schemas.StudentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant),
    current_user: User = Depends(get_current_user)
):
    svc = service.StudentService(db, UUID(tenant_id))
    return await svc.create_student(data)

@router.get("/{student_id}", response_model=schemas.StudentOut,
            dependencies=[Depends(PermissionChecker("student:read"))])
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    svc = service.StudentService(db, UUID(tenant_id))
    student = await svc.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/", response_model=List[schemas.StudentOut],
            dependencies=[Depends(PermissionChecker("student:read"))])
async def list_students(
    class_id: Optional[UUID] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    svc = service.StudentService(db, UUID(tenant_id))
    return await svc.list_students(class_id, is_active, skip, limit)

@router.patch("/{student_id}", response_model=schemas.StudentOut,
              dependencies=[Depends(PermissionChecker("student:update"))])
async def update_student(
    student_id: UUID,
    data: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    svc = service.StudentService(db, UUID(tenant_id))
    student = await svc.update_student(student_id, data)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.delete("/{student_id}", status_code=204,
               dependencies=[Depends(PermissionChecker("student:delete"))])
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    svc = service.StudentService(db, UUID(tenant_id))
    # Soft delete by deactivating
    await svc.exit_student(student_id, reason="Deleted by admin")
    return

@router.post("/{student_id}/exit", response_model=schemas.StudentOut,
             dependencies=[Depends(PermissionChecker("student:update"))])
async def exit_student(
    student_id: UUID,
    reason: str = Query(..., description="Reason for exit"),
    exit_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    from datetime import date, datetime
    svc = service.StudentService(db, UUID(tenant_id))
    edate = datetime.strptime(exit_date, "%Y-%m-%d").date() if exit_date else date.today()
    student = await svc.exit_student(student_id, reason, edate)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/bulk/promote", status_code=200,
             dependencies=[Depends(PermissionChecker("student:bulk"))])
async def bulk_promote(
    req: schemas.BulkPromoteRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_active_tenant)
):
    svc = service.StudentService(db, UUID(tenant_id))
    count = await svc.bulk_promote(req.from_class_id, req.to_class_id, req.section)
    return {"promoted_count": count}