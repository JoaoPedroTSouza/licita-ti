"""Rotas da Entrada: listar, detalhar e triar oportunidades."""
from fastapi import APIRouter, Depends, Response, status

from radar.container import Container
from radar.domain.erros import NaoEncontrado
from radar.domain.oportunidade import StatusOportunidade
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import (
    DescartarIn, OportunidadeDetalheDTO, OportunidadeDTO, ProcessoDTO,
    oportunidade_detalhe_dto, oportunidade_dto, processo_dto,
)

router = APIRouter(prefix="/oportunidades")


@router.get("", response_model=list[OportunidadeDTO])
def listar(
    status: StatusOportunidade = StatusOportunidade.NOVA,
    c: Container = Depends(obter_container),
):
    with c.uow() as uow:
        ops = uow.oportunidades.listar(status)
        taxas = uow.cotacoes.mais_recentes()
    return [oportunidade_dto(op, taxas) for op in ops]


@router.get("/{oportunidade_id}", response_model=OportunidadeDetalheDTO)
def detalhar(oportunidade_id: int, c: Container = Depends(obter_container)):
    with c.uow() as uow:
        op = uow.oportunidades.obter(oportunidade_id)
        taxas = uow.cotacoes.mais_recentes()
    if op is None:
        raise NaoEncontrado(f"Oportunidade {oportunidade_id} não encontrada.")
    return oportunidade_detalhe_dto(op, taxas)


@router.post("/{oportunidade_id}/interessa", response_model=ProcessoDTO)
def interessa(oportunidade_id: int, c: Container = Depends(obter_container)):
    processo = c.triar().interessa(oportunidade_id)
    with c.uow() as uow:
        taxas = uow.cotacoes.mais_recentes()
        lembretes = uow.lembretes.do_processo(processo.id)
    return processo_dto(processo, taxas, lembretes)


@router.post("/{oportunidade_id}/descartar", status_code=status.HTTP_204_NO_CONTENT)
def descartar(
    oportunidade_id: int, corpo: DescartarIn | None = None,
    c: Container = Depends(obter_container),
):
    c.triar().descartar(oportunidade_id, corpo.motivo if corpo else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
