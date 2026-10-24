"""Rotas de lembretes."""
from fastapi import APIRouter, Depends, Response, status

from radar.container import Container
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import LembreteDTO, LembreteIn, lembrete_dto

router = APIRouter(prefix="/lembretes")


@router.get("", response_model=list[LembreteDTO])
def listar(pendentes: bool = True, c: Container = Depends(obter_container)):
    """Lembretes não concluídos (vencidos ou futuros) por `vence_em`. Os concluídos nunca
    são listados; `pendentes` existe só por compatibilidade com o cliente."""
    with c.uow() as uow:
        lembretes = uow.lembretes.nao_concluidos()
    return [lembrete_dto(x) for x in sorted(lembretes, key=lambda x: x.vence_em)]


@router.post("", response_model=LembreteDTO, status_code=status.HTTP_201_CREATED)
def criar(corpo: LembreteIn, c: Container = Depends(obter_container)):
    return lembrete_dto(c.funil().criar_lembrete(corpo.texto, corpo.vence_em, corpo.processo_id))


@router.post("/{lembrete_id}/concluir", response_model=LembreteDTO)
def concluir(lembrete_id: int, c: Container = Depends(obter_container)):
    return lembrete_dto(c.funil().concluir_lembrete(lembrete_id))


@router.delete("/{lembrete_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(lembrete_id: int, c: Container = Depends(obter_container)):
    c.funil().remover_lembrete(lembrete_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
