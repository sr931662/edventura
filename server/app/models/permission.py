from sqlalchemy import Column, String
from app.models.base import EdVenturaBase

class Permission(EdVenturaBase):
    __tablename__ = "permissions"

    codename = Column(String(150), unique=True, nullable=False)   # e.g., "student:read"
    description = Column(String(500))