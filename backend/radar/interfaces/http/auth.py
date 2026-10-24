"""Autenticação por senha única + JWT (HS256)."""
import hmac
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from radar.config import Settings
from radar.container import Container

_bearer = HTTPBearer(auto_error=False)


def obter_container(request: Request) -> Container:
    return request.app.state.container


def senha_confere(settings: Settings, senha: str) -> bool:
    return hmac.compare_digest(senha.encode(), settings.app_password.encode())


def gerar_token(settings: Settings) -> str:
    exp = datetime.now(UTC) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode({"sub": "owner", "exp": exp}, settings.jwt_secret, algorithm="HS256")


def exigir_login(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: Container = Depends(obter_container),
) -> str:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login")
    try:
        payload = jwt.decode(
            cred.credentials, container.settings.jwt_secret, algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada")
    return payload["sub"]
