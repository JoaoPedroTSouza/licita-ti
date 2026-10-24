"""Aplicação FastAPI: rotas protegidas por JWT e tradução dos erros de domínio."""
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from radar.config import get_settings
from radar.container import Container
from radar.domain.erros import ErroDeDominio, NaoEncontrado
from radar.interfaces.http import rotas_ajustes, rotas_oportunidades, rotas_painel
from radar.interfaces.http.auth import (
    exigir_login, gerar_token, obter_container, senha_confere,
)
from radar.interfaces.http.dtos import LoginIn, TokenDTO


def criar_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title="Radar")
    app.state.container = container or Container.de_settings(get_settings())

    @app.exception_handler(NaoEncontrado)
    def _nao_encontrado(_: Request, erro: NaoEncontrado) -> JSONResponse:
        return JSONResponse({"detail": str(erro)}, status_code=404)

    @app.exception_handler(ErroDeDominio)
    @app.exception_handler(ValueError)
    def _regra_violada(_: Request, erro: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(erro)}, status_code=422)

    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict:
        return {"ok": True}

    @api.post("/auth/login", response_model=TokenDTO)
    def login(corpo: LoginIn, c: Container = Depends(obter_container)):
        if not senha_confere(c.settings, corpo.senha):
            raise HTTPException(401, "Senha incorreta")
        return TokenDTO(token=gerar_token(c.settings))

    protegido = APIRouter(dependencies=[Depends(exigir_login)])
    protegido.include_router(rotas_oportunidades.router)
    protegido.include_router(rotas_painel.router)
    protegido.include_router(rotas_ajustes.router)
    api.include_router(protegido)
    app.include_router(api)
    return app
