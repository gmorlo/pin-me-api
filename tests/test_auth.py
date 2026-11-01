from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings
from app.core.constants import DEMO_USER_ID
from app.core.security import create_access_token
from app.main import app


def test_auth_me_requires_token(client) -> None:
    client.headers.pop("Authorization", None)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_with_bearer(client) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "demo@pinme.local"
    assert body["id"] == str(DEMO_USER_ID)


def test_boards_require_auth(client) -> None:
    client.headers.pop("Authorization", None)
    response = client.get("/boards")
    assert response.status_code == 401


def test_dev_login_allowlisted(client) -> None:
    settings = Settings(
        app_env="local",
        auth_dev_bypass=True,
        jwt_secret="test-secret-at-least-32-bytes!!",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    client.headers.pop("Authorization", None)

    response = client.post("/auth/dev-login", json={"email": "demo@pinme.local"})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "demo@pinme.local"
    assert settings.auth_cookie_name in response.cookies


def test_dev_login_rejects_unknown_email(client) -> None:
    settings = Settings(
        app_env="local",
        auth_dev_bypass=True,
        jwt_secret="test-secret-at-least-32-bytes!!",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    client.headers.pop("Authorization", None)

    response = client.post("/auth/dev-login", json={"email": "stranger@example.com"})
    assert response.status_code == 403


def test_dev_login_disabled_by_default(client) -> None:
    settings = Settings(
        app_env="local",
        auth_dev_bypass=False,
        jwt_secret="test-secret-at-least-32-bytes!!",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    client.headers.pop("Authorization", None)

    response = client.post("/auth/dev-login", json={"email": "demo@pinme.local"})
    assert response.status_code == 404


def test_issue_token_roundtrip() -> None:
    settings = get_settings()
    token = create_access_token(
        user_id=DEMO_USER_ID, email="demo@pinme.local", settings=settings
    )
    assert isinstance(token, str) and len(token) > 20



@pytest.mark.parametrize("app_env", ["dev", "development", "test", "staging"])
def test_only_local_may_enable_dev_bypass(app_env) -> None:
    with pytest.raises(ValueError, match="AUTH_DEV_BYPASS"):
        Settings(app_env=app_env, jwt_secret="x" * 32, auth_dev_bypass=True, _env_file=None)
