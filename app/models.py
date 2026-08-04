from .database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(
        String(50),
        unique=False,
        nullable=False
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False
    )
    password_hash = Column(
        String(255),
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )