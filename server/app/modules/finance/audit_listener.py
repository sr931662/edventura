from sqlalchemy import event, inspect
from app.models.finance_models import Invoice, Transaction, StudentFeeAccount, FinanceAuditLog

@event.listens_for(Invoice, 'after_insert')
@event.listens_for(Invoice, 'after_update')
@event.listens_for(Transaction, 'after_insert')
@event.listens_for(Transaction, 'after_update')
@event.listens_for(StudentFeeAccount, 'after_update')
def after_change(mapper, connection, target):
    entity_type = type(target).__name__
    action = 'UPDATE' if inspect(target).modified else 'INSERT'
    changes = {}
    if action == 'UPDATE':
        for attr in inspect(target).attrs:
            if attr.history.has_changes():
                changes[attr.key] = {
                    'old': str(attr.history.deleted[0]) if attr.history.deleted else None,
                    'new': str(attr.history.added[0]) if attr.history.added else None
                }
    log = FinanceAuditLog(
        tenant_id=target.tenant_id,
        entity_type=entity_type,
        entity_id=target.id,
        action=action,
        changed_by=getattr(target, 'marked_by', None) or getattr(target, 'updated_at', None),
        changes=changes
    )
    from sqlalchemy.orm import Session
    sync_session = Session(bind=connection)
    sync_session.add(log)
    sync_session.commit()