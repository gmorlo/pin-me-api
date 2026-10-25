from __future__ import annotations

import secrets
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token
from app.models.user import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def ensure_allowlist_user(db: Session, email: str) -> User:
    """Create allowlisted user if missing (startup seed only)."""
    normalized = normalize_email(email)
    existing = get_user_by_email(db, normalized)
    if existing is not None:
        return existing

    base = normalized.split("@", 1)[0][:60] or "user"
    username = base
    suffix = 1
    while db.scalar(select(User).where(User.username == username)) is not None:
        username = f"{base}{suffix}"[:80]
        suffix += 1

    user = User(email=normalized, username=username, password_hash=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def require_allowlisted_user(db: Session, email: str) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Google account is not allowlisted. Ask the owner to add your email.",
        )
    return user


def issue_token_for_user(user: User, settings: Settings) -> str:
    return create_access_token(user_id=user.id, email=user.email, settings=settings)


def build_google_authorize_url(*, settings: Settings, state: str) -> str:
    if not settings.google_oauth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured (set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET).",
        )
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def new_oauth_state() -> str:
    return secrets.token_urlsafe(24)


async def exchange_google_code(code: str, settings: Settings) -> str:
    """Exchange auth code for Google access token; return email."""
    if not settings.google_oauth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token exchange failed",
            )
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google did not return an access token",
            )

        info_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if info_response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user info",
            )
        email = info_response.json().get("email")
        if not email or not info_response.json().get("email_verified", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is missing or unverified",
            )
        return normalize_email(email)
