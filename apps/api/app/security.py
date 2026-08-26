"""Minimal auth/RBAC scaffolding.

This intentionally does not implement a full SSO/OAuth flow (out of scope
for this platform's first version) but establishes the seam everything
else depends on: `get_current_user` resolves a User from a bearer token,
and `require_role` gates endpoints by UserRole. Swapping in real SSO later
only means changing `get_current_user`'s implementation.
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from hom_core.enums import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def verify_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Gate for endpoints only training-worker/inference services should
    call (job status/log callbacks, worker heartbeats). Uses a constant
    time comparison against a shared secret from settings/.env."""
    settings = get_settings()
    if x_internal_token is None or not secrets.compare_digest(x_internal_token, settings.internal_api_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid internal service token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, role: UserRole) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        user_email: str | None = payload.get("sub")
    except JWTError:
        raise unauthorized
    if user_email is None:
        raise unauthorized
    user = db.query(User).filter(User.email == user_email).first()
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_role(*allowed: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted to perform this action",
            )
        return user

    return dependency
