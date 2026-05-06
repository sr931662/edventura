from sqlalchemy import Column, String
from app.models.base import EdVenturaBase

class Class(EdVenturaBase):
    __tablename__ = "classes"

    name = Column(String(100), nullable=False)
    section = Column(String(20))