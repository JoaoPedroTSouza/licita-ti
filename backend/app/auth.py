import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

_bearer = HTTPBearer(auto_error=False)


def senha_confere(senha: str) -> bool:
    return hmac.compare_digest(senha.encode(), get_settings().app_password.encode())


def gerar_token() -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(days=s.jwt_expire_days)
    return jwt.encode({"sub": "owner", "exp": exp}, s.jwt_secret, algorithm="HS256")


def exigir_login(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login")
    try:
        payload = jwt.decode(cred.credentials, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada")
    return payload["sub"]
