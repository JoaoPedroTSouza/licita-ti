"""Rotas de perfil, ajustes e status do sistema."""
from datetime import time

from fastapi import APIRouter, Depends

from radar.container import Container
from radar.domain.perfil import Ajustes, Perfil
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import (
    AjustesDTO, PerfilDTO, StatusDTO, ajustes_dto, execucao_dto, perfil_dto,
)

router = APIRouter()


@router.get("/perfil", response_model=PerfilDTO)
def obter_perfil(c: Container = Depends(obter_container)):
    with c.uow() as uow:
        return perfil_dto(uow.configuracoes.perfil())


@router.put("/perfil", response_model=PerfilDTO)
def salvar_perfil(corpo: PerfilDTO, c: Container = Depends(obter_container)):
    perfil = Perfil(corpo.texto, corpo.faixa_min_brl, corpo.faixa_max_brl)
    with c.uow() as uow:
        uow.configuracoes.salvar_perfil(perfil)
        uow.commit()
    return perfil_dto(perfil)


@router.get("/ajustes", response_model=AjustesDTO)
def obter_ajustes(c: Container = Depends(obter_container)):
    with c.uow() as uow:
        return ajustes_dto(uow.configuracoes.ajustes())


@router.put("/ajustes", response_model=AjustesDTO)
def salvar_ajustes(corpo: AjustesDTO, c: Container = Depends(obter_container)):
    ajustes = Ajustes(
        corpo.limiar_alerta, time.fromisoformat(corpo.horario_resumo),
        tuple(corpo.avisos_prazo_dias),
    )
    with c.uow() as uow:
        uow.configuracoes.salvar_ajustes(ajustes)
        uow.commit()
    return ajustes_dto(ajustes)


@router.get("/status", response_model=StatusDTO)
def status(c: Container = Depends(obter_container)):
    with c.uow() as uow:
        execucoes = uow.execucoes.ultimas_por_fonte()
    return StatusDTO(
        ia_configurada=c.classificador is not None,
        push_configurado=c.notificador.configurado,
        fontes=[execucao_dto(e) for e in execucoes],
    )
