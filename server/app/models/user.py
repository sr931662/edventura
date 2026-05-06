from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import EdVenturaBase
from sqlalchemy import UniqueConstraint

class User(EdVenturaBase):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uq_user_email_tenant"),
    )
    email = Column(String(255), nullable=False, index=True)  # remove unique=True here
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)   # true only for global owners
    mfa_secret = Column(String(32), nullable=True)    # TOTP secret
    mfa_enabled = Column(Boolean, default=False)
    mfa_pending_secret = Column(String(32), nullable=True)

    # Relationships will be added later (roles via association table)