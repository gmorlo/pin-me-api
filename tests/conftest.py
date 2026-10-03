from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import DEMO_USER_ID
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User  # noqa: F401 — register metadata
from app.models.image import SourceType
from app.storage import clear_source_cache
from app.storage.base import ResolvedContent
from app.storage.registry import get_source


class FakeLocalUploadSource:
    source_type = SourceType.LOCAL_UPLOAD.value

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def upload(
        self,
        *,
        board_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> str:
        key = f"boards/{board_id}/{filename}"
        self.objects[key] = (data, content_type)
        return key

    def resolve(self, image) -> ResolvedContent:
        assert image.storage_key is not None
        data, content_type = self.objects[image.storage_key]
        return ResolvedContent(data=data, content_type=content_type)

    def delete(self, storage_key: str) -> None:
        self.objects.pop(storage_key, None)


@pytest.fixture()
def fake_storage(monkeypatch: pytest.MonkeyPatch) -> FakeLocalUploadSource:
    fake = FakeLocalUploadSource()
    clear_source_cache()

    def _get_source(source_type: str):
        if source_type == SourceType.LOCAL_UPLOAD.value:
            return fake
        return get_source(source_type)

    monkeypatch.setattr("app.services.images.get_source", _get_source)
    monkeypatch.setattr("app.services.boards.get_source", _get_source)
    yield fake
    clear_source_cache()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    session.add(
        User(
            id=DEMO_USER_ID,
            email="demo@pinme.local",
            username="demo",
            password_hash=None,
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(
    db_session: Session, fake_storage: FakeLocalUploadSource
) -> Generator[TestClient, None, None]:
    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
