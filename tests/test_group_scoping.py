import os

os.environ["DATABASE_URL"] = "sqlite:///./test_group_scoping.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["TEACHER_SECRET_CODE"] = "123456"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app import models
from app.database import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_group_scoping.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function():
    Base.metadata.create_all(bind=engine)
    main_module.app.dependency_overrides[main_module.get_db] = override_get_db


def teardown_function():
    main_module.app.dependency_overrides.clear()
    models.User.query = None
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


client = TestClient(main_module.app)


def test_teacher_only_sees_own_groups():
    teacher_a = models.User(
        full_name="Teacher A",
        email="teacherA@example.com",
        password_hash="x",
        teacher=True,
    )
    teacher_b = models.User(
        full_name="Teacher B",
        email="teacherB@example.com",
        password_hash="x",
        teacher=True,
    )
    group_a = models.Groups(name="Alpha", description="First", teacher_id=teacher_a.id if teacher_a.id else None)
    group_b = models.Groups(name="Beta", description="Second", teacher_id=teacher_b.id if teacher_b.id else None)

    with TestingSessionLocal() as db:
        db.add_all([teacher_a, teacher_b, group_a, group_b])
        db.commit()
        db.refresh(teacher_a)
        db.refresh(teacher_b)
        db.refresh(group_a)
        db.refresh(group_b)
        group_a.teacher_id = teacher_a.id
        group_b.teacher_id = teacher_b.id
        db.commit()

    def fake_current_user():
        with TestingSessionLocal() as db:
            return db.query(models.User).filter(models.User.email == "teacherA@example.com").first()

    main_module.app.dependency_overrides[main_module.get_current_user] = fake_current_user
    response = client.get("/groups")
    assert response.status_code == 200
    data = response.json()
    assert [g["name"] for g in data] == ["Alpha"]


def test_other_teacher_cannot_update_group():
    teacher_a = models.User(
        full_name="Teacher A",
        email="teacherA2@example.com",
        password_hash="x",
        teacher=True,
    )
    teacher_b = models.User(
        full_name="Teacher B",
        email="teacherB2@example.com",
        password_hash="x",
        teacher=True,
    )
    group = models.Groups(name="Protected", description="owned by A")

    with TestingSessionLocal() as db:
        db.add_all([teacher_a, teacher_b, group])
        db.commit()
        db.refresh(teacher_a)
        db.refresh(teacher_b)
        db.refresh(group)
        group.teacher_id = teacher_a.id
        db.commit()
        group_id = group.id

    def fake_current_user():
        with TestingSessionLocal() as db:
            return db.query(models.User).filter(models.User.email == "teacherB2@example.com").first()

    main_module.app.dependency_overrides[main_module.get_current_user] = fake_current_user
    response = client.patch("/group/{group_id}".format(group_id=group_id), json={"name": "Hacked"})
    assert response.status_code == 403
