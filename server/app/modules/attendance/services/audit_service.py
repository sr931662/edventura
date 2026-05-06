from sqlalchemy import event, inspect
from app.models.attendance_models import AttendanceRecord, AttendanceAuditLog
from app.core.database import async_session_factory
import asyncio

# @event.listens_for(AttendanceRecord, 'after_insert')
def after_insert(mapper, connection, target):
    _log_attendance_change(target, 'INSERT', connection)

# @event.listens_for(AttendanceRecord, 'after_update')
def after_update(mapper, connection, target):
    _log_attendance_change(target, 'UPDATE', connection)

def _log_attendance_change(target, action, connection):
    try:
        changed_fields = inspect(target).attrs
        # For simplicity, we log the whole record status change.
        # In a production listener, you'd loop over changed columns.
        # Here we just log the status change.
        log = AttendanceAuditLog(
            tenant_id=target.tenant_id,
            record_id=target.id,
            changed_by=getattr(target, 'marked_by', None),
            field_name='status',
            old_value='' if action == 'INSERT' else target.status,
            new_value=target.status,
            action=action
        )
        # Use synchronous session attached to the raw connection
        from sqlalchemy.orm import Session
        sync_session = Session(bind=connection)
        sync_session.add(log)
        sync_session.commit()
    except Exception:
        pass
    
async def log_attendance_change(db, tenant_id, record_id, changed_by, field_name, old_value, new_value, action):
    from app.models.attendance_models import AttendanceAuditLog
    log = AttendanceAuditLog(
        tenant_id=tenant_id,
        record_id=record_id,
        changed_by=changed_by,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        action=action
    )
    db.add(log)
    await db.flush()
