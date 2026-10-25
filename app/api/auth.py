from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import AuthStatus, DevLoginRequest, UserRead
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Ephemeral OAuth CSRF states (single-process local API is fine for Stage 007).
_pending_states: set[str] = set()


def _set_auth_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=not settings.is_local,
        max_age=settings.jwt_expire_hours * 3600,
        path="/",
    )


def _clear_auth_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
        samesite="lax",
        secure=not settings.is_local,
    )


@router.get("/status", response_model=AuthStatus)
def auth_status(settings: Settings = Depends(get_settings)) -> AuthStatus:
    return AuthStatus(
        google_configured=settings.google_oauth_configured,
        dev_bypass=settings.auth_dev_bypass and settings.is_local,
    )


@router.get("/me", response_model=UserRead)
def auth_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/google/start")
def google_start(settings: Settings = Depends(get_settings)) -> RedirectResponse:
    state = auth_service.new_oauth_state()
    _pending_states.add(state)
    url = auth_service.build_google_authorize_url(settings=settings, state=state)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    web = settings.web_app_origin.rstrip("/")
    if error:
        return RedirectResponse(url=f"{web}/login?error=google_denied", status_code=302)
    if not code or not state or state not in _pending_states:
        return RedirectResponse(url=f"{web}/login?error=invalid_state", status_code=302)
    _pending_states.discard(state)

    try:
        email = await auth_service.exchange_google_code(code, settings)
        user = auth_service.require_allowlisted_user(db, email)
        token = auth_service.issue_token_for_user(user, settings)
    except HTTPException as exc:
        detail = "not_allowlisted" if exc.status_code == 403 else "auth_failed"
        return RedirectResponse(url=f"{web}/login?error={detail}", status_code=302)

    response = RedirectResponse(url=f"{web}/boards", status_code=302)
    _set_auth_cookie(response, token, settings)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> None:
    _clear_auth_cookie(response, settings)


@router.post("/dev-login", response_model=UserRead)
def dev_login(
    payload: DevLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if not (settings.auth_dev_bypass and settings.is_local):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev login disabled",
        )
    user = auth_service.require_allowlisted_user(db, payload.email)
    token = auth_service.issue_token_for_user(user, settings)
    _set_auth_cookie(response, token, settings)
    return user
