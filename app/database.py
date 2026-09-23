from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL") 
Base = declarative_base()
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def add_missing_columns():
    """Add columns introduced after the initial database creation."""
    try:
        inspector = inspect(engine)
    except Exception:
        return

    tables = set(inspector.get_table_names())

    if "objects" in tables:
        object_columns = {column["name"] for column in inspector.get_columns("objects")}
        if "homework_url" not in object_columns:
            try:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE objects ADD COLUMN homework_url VARCHAR(2048)"))
            except Exception:
                pass

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "student_code" not in user_columns:
            try:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE users ADD COLUMN student_code VARCHAR(50)"))
                    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_student_code ON users (student_code)"))
            except Exception:
                pass

    if "groups" in tables:
        group_columns = {column["name"] for column in inspector.get_columns("groups")}
        if "teacher_id" not in group_columns:
            try:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE groups ADD COLUMN teacher_id INTEGER REFERENCES users(id)"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_groups_teacher_id ON groups (teacher_id)"))
            except Exception:
                pass

    if "notifications" in tables:
        notification_columns = {column["name"] for column in inspector.get_columns("notifications")}
        if "created_by_id" not in notification_columns:
            try:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE notifications ADD COLUMN created_by_id INTEGER"))
                    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_created_by_id ON notifications (created_by_id)"))
            except Exception:
                pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

