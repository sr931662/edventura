from sqlalchemy import Column, String, Boolean
from app.models.base import EdVenturaBase

class Tenant(EdVenturaBase):
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False, unique=True)
    domain = Column(String(255), unique=True)  # optional domain for easy identification
    is_active = Column(Boolean, default=True)
    # subscription tier, etc. will be added later