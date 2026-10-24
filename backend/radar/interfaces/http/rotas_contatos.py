"""Rotas da rede profissional."""
from datetime import date

from fastapi import APIRouter, Depends, status

from radar.container import Container
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import ContatoDTO, ContatoEdicaoIn, ContatoNovoIn, contato_dto

router = APIRouter(prefix="/contatos")


def _hoje(c: Container) -> date:
    return c.relogio.agora().astimezone(c.tz).date()


@router.get("", response_model=list[ContatoDTO])
def listar(c: Container = Depends(obter_container)):
    hoje = _hoje(c)
    return [contato_dto(x, hoje) for x in c.rede().listar()]


@router.post("", response_model=ContatoDTO, status_code=status.HTTP_201_CREATED)
def criar(corpo: ContatoNovoIn, c: Container = Depends(obter_container)):
    return contato_dto(c.rede().criar(**corpo.model_dump()), _hoje(c))


@router.patch("/{contato_id}", response_model=ContatoDTO)
def editar(contato_id: int, corpo: ContatoEdicaoIn, c: Container = Depends(obter_container)):
    """Altera só os campos presentes no corpo (aceita null, exceto em `nome`)."""
    campos = {k: getattr(corpo, k) for k in corpo.model_fields_set}
    return contato_dto(c.rede().editar(contato_id, **campos), _hoje(c))


@router.post("/{contato_id}/registrar-contato", response_model=ContatoDTO)
def registrar_contato(contato_id: int, c: Container = Depends(obter_container)):
    return contato_dto(c.rede().registrar_contato(contato_id), _hoje(c))
