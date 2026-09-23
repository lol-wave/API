import os
from datetime import datetime, timedelta

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


def test_login_with_invalid_password_hash_returns_401():
    with TestingSessionLocal() as db:
        user = models.User(
            full_name="Broken Hash",
            email="broken@example.com",
            password_hash="not-a-valid-password-hash",
            teacher=False,
        )
        db.add(user)
        db.commit()

    response = client.post(
        "/login",
        json={"email": "broken@example.com", "password": "any-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_forgot_password_generic_response_and_rate_limit():
    with TestingSessionLocal() as db:
        user = models.User(
            full_name="Reset User",
            email="reset@example.com",
            password_hash=main_module.ph.hash("OriginalPass123"),
            teacher=False,
        )
        db.add(user)
        db.commit()

    response = client.post("/forgot-password", json={"email": "missing@example.com"})
    assert response.status_code == 200
    assert response.json() == {"message": "If that email exists, a reset link has been sent."}

    for _ in range(3):
        response = client.post("/forgot-password", json={"email": "reset@example.com"})
        assert response.status_code == 200

    response = client.post("/forgot-password", json={"email": "reset@example.com"})
    assert response.status_code == 429
    assert "detail" in response.json()


def test_reset_password_success_and_rejects_used_token():
    with TestingSessionLocal() as db:
        user = models.User(
            full_name="Token User",
            email="tokenuser@example.com",
            password_hash=main_module.ph.hash("old-password-123"),
            teacher=False,
        )
        db.add(user)
        db.commit()

        raw_token = "reset-token-1234567890"
        db.add(
            models.PasswordResetToken(
                user_id=user.id,
                token_hash=main_module.ph.hash(raw_token),
                expires_at=datetime.utcnow() + timedelta(minutes=60),
            )
        )
        db.commit()

    response = client.post(
        "/reset-password",
        json={"token": raw_token, "new_password": "newPass456"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password has been reset."}

    response = client.post(
        "/reset-password",
        json={"token": raw_token, "new_password": "newPass4567"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Reset link is invalid or has expired."}
