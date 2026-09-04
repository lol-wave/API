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
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "objects" in tables:
        object_columns = {column["name"] for column in inspector.get_columns("objects")}
        if "homework_url" not in object_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE objects ADD COLUMN homework_url VARCHAR(2048)"))

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "student_code" not in user_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN student_code VARCHAR(50)"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_student_code ON users (student_code)"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

