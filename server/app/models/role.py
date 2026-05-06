from sqlalchemy import Column, String, Boolean
from app.models.base import EdVenturaBase

class Role(EdVenturaBase):
    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    is_system = Column(Boolean, default=False)   # predefined roles like "Institution Owner"