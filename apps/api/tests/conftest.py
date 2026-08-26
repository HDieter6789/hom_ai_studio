import os

# Point the app at an in-memory SQLite database before any app module is
# imported, so app.config.get_settings() picks this up.
os.environ["HOM_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["HOM_SECRET_KEY"] = "test-secret"
os.environ["HOM_INTERNAL_API_TOKEN"] = "test-internal-token"
os.environ["HOM_STORAGE_ROOT"] = "./.test_storage"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as database
import app.models  # noqa: F401 - registers all tables on Base.metadata
from app.database import Base
from app.main import app as fastapi_app
from app.security import create_access_token, hash_password
from app.models.user import User
from hom_core.enums import UserRole

@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_storage():
    import shutil

    yield
    shutil.rmtree(os.environ["HOM_STORAGE_ROOT"], ignore_errors=True)


test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def _no_real_queue(monkeypatch):
    """Business-logic tests exercise services directly and must not
    require a live Redis broker. Job/deployment *enqueuing* itself is
    infrastructure glue, not something these tests assert on."""
    import app.worker_client as worker_client

    monkeypatch.setattr(worker_client, "enqueue_training_job", lambda job_id: None)
    monkeypatch.setattr(worker_client, "enqueue_cancel_training_job", lambda job_id: None)
    monkeypatch.setattr(worker_client, "enqueue_deployment", lambda deployment_id: None)
    monkeypatch.setattr(worker_client, "enqueue_stop_deployment", lambda deployment_id: None)


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _get_db_override():
        yield db

    fastapi_app.dependency_overrides[database.get_db] = _get_db_override
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def _make(email: str = "engineer@hom.local", role: UserRole = UserRole.ML_ENGINEER) -> tuple[User, str]:
        user = User(email=email, hashed_password=hash_password("changeme"), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=user.email, role=user.role)
        return user, token

    return _make


@pytest.fixture
def auth_headers(make_user):
    _, token = make_user()
    return {"Authorization": f"Bearer {token}"}
