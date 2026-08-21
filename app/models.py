from .database import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

user_notifications = Table(
    "user_notifications",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("notification_id", ForeignKey("notifications.id"), primary_key=True),
    Column("is_read", Boolean, default=False, nullable=False),
    Column("read_at", DateTime, nullable=True)
)


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
    
    group_id = Column(
        Integer,
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True
    )
    
    is_group_admin = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    group = relationship("Groups", back_populates="members", foreign_keys=[group_id])
    
    notifications = relationship(
        "Notification",
        secondary=user_notifications,
        back_populates="users"
    )

    homework_submissions = relationship(
        "HomeworkSubmission",
        back_populates="student",
        cascade="all, delete-orphan"
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

    submitted = Column(
        Boolean, default=False
    )

    homework_url = Column(
        String(2048), nullable=True
    )

    group_id = Column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False
    )

    group = relationship("Groups", back_populates="objects")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    submissions = relationship(
        "HomeworkSubmission",
        back_populates="object",
        cascade="all, delete-orphan"
    )


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"
    __table_args__ = (
        UniqueConstraint("object_id", "student_id", name="uq_homework_submission_student_object"),
    )

    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    grade = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    graded_at = Column(DateTime, nullable=True)

    object = relationship("Objects", back_populates="submissions")
    student = relationship("User", back_populates="homework_submissions")


class Groups(Base):
    __tablename__ = "groups"

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
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    objects = relationship("Objects", back_populates="group", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="group", cascade="all, delete-orphan")
    members = relationship("User", back_populates="group", cascade="all")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    group = relationship("Groups", back_populates="lessons")
    teacher = relationship("User", foreign_keys=[teacher_id])
    items = relationship("LessonItem", back_populates="lesson", cascade="all, delete-orphan")


class LessonItem(Base):
    __tablename__ = "lesson_items"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(30), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(2048), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lesson = relationship("Lesson", back_populates="items")


class StudentRating(Base):
    __tablename__ = "student_ratings"
    __table_args__ = (UniqueConstraint("teacher_id", "student_id", name="uq_student_rating_teacher_student"),)

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    teacher = relationship("User", foreign_keys=[teacher_id])
    student = relationship("User", foreign_keys=[student_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    notification_type = Column(String(50), nullable=False, default="info")  # info, warning, error, success
    icon_url = Column(String, nullable=True)
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    users = relationship(
        "User",
        secondary=user_notifications,
        back_populates="notifications"
    )
