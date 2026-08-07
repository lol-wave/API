from .database import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime
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
    profile_pic = Column(String, unique=True, index=True)

    teacher = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Objects(Base):
    __tablename__ = "objects"

    id = Column(Integer, primary_key=True)
    name = Column(
        String(100),
        unique=True,
        nullable=False
    )
    description = Column(
        String(255),
        nullable=True
    )

    deadline = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )