from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


JWT_SECRET = os.getenv("OPERATOR_JWT_SECRET", "change_me_now")
JWT_ALG = "HS256"
JWT_TTL_MINUTES = int(os.getenv("OPERATOR_JWT_TTL_MINUTES", "480"))
ADMIN_USER = os.getenv("OPERATOR_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("OPERATOR_ADMIN_PASSWORD", "change_me")

security = HTTPBearer()


def verify_admin(username: str, password: str) -> bool:
    return username == ADMIN_USER and password == ADMIN_PASSWORD


def create_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_TTL_MINUTES)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        return str(payload["sub"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

