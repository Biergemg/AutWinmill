from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


OPERATOR_ENV = os.getenv("OPERATOR_ENV", "production").lower()

if OPERATOR_ENV in ("dev", "development", "test"):
    JWT_SECRET = os.getenv("OPERATOR_JWT_SECRET", "dev_secret_only")
    ADMIN_PASSWORD = os.getenv("OPERATOR_ADMIN_PASSWORD", "dev_password_only")
else:
    try:
        JWT_SECRET = os.environ["OPERATOR_JWT_SECRET"]
        ADMIN_PASSWORD = os.environ["OPERATOR_ADMIN_PASSWORD"]
    except KeyError as e:
        raise RuntimeError(f"FATAL: La variable de entorno {e} es obligatoria en producción.") from e

JWT_ALG = "HS256"
JWT_TTL_MINUTES = int(os.getenv("OPERATOR_JWT_TTL_MINUTES", "480"))
ADMIN_USER = os.getenv("OPERATOR_ADMIN_USER", "admin")
PLACEHOLDER_FRAGMENTS = ("change_me", "replace_with", "your_", "example", "client_")

security = HTTPBearer()


def verify_admin(username: str, password: str) -> bool:
    return secrets.compare_digest(username, ADMIN_USER) and secrets.compare_digest(password, ADMIN_PASSWORD)


def assert_secure_runtime() -> None:
    if os.getenv("OPERATOR_ENV", "dev").lower() not in {"prod", "production"}:
        return
    insecure = []
    secret_lower = JWT_SECRET.lower()
    password_lower = ADMIN_PASSWORD.lower()
    if len(JWT_SECRET) < 32 or any(fragment in secret_lower for fragment in PLACEHOLDER_FRAGMENTS):
        insecure.append("OPERATOR_JWT_SECRET")
    if len(ADMIN_PASSWORD) < 12 or any(fragment in password_lower for fragment in PLACEHOLDER_FRAGMENTS):
        insecure.append("OPERATOR_ADMIN_PASSWORD")
    if insecure:
        joined = ", ".join(insecure)
        raise RuntimeError(f"Insecure production configuration: {joined}")


def create_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_TTL_MINUTES)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
