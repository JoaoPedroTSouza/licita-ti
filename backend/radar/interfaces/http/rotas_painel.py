"""Rota do painel do dia."""
from fastapi import APIRouter, Depends

from radar.container import Container
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import PainelDTO, painel_dto

router = APIRouter()


@router.get("/painel", response_model=PainelDTO)
def painel(c: Container = Depends(obter_container)):
    resultado = c.painel().executar()
    with c.uow() as uow:
        taxas = uow.cotacoes.mais_recentes()
    return painel_dto(resultado, taxas)
