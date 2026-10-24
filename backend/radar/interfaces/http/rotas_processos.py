"""Rotas do funil: processos, notas, arquivos e contatos vinculados."""
import mimetypes
import re
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status

from radar.container import Container
from radar.domain.erros import NaoEncontrado
from radar.domain.processo import Processo
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import (
    ArquivoDTO, EtapaIn, NotaIn, ProcessoDTO, ProcessoEdicaoIn, ProcessoNovoIn,
    ProcessoResumoDTO, arquivo_dto, processo_dto, processo_resumo_dto,
)

router = APIRouter(prefix="/processos")


def nome_seguro(nome: str | None) -> str:
    limpo = re.sub(r"[^\w.\- ]", "_", Path(nome or "").name)[:120]
    return limpo or "arquivo"


def _ver(c: Container, processo: Processo) -> ProcessoDTO:
    with c.uow() as uow:
        taxas = uow.cotacoes.mais_recentes()
        lembretes = uow.lembretes.do_processo(processo.id)
    return processo_dto(processo, taxas, lembretes)


def _obter(c: Container, processo_id: int) -> Processo:
    with c.uow() as uow:
        processo = uow.processos.obter(processo_id)
    if processo is None:
        raise NaoEncontrado(f"Processo {processo_id} não encontrado.")
    return processo


@router.get("", response_model=list[ProcessoResumoDTO])
def listar(c: Container = Depends(obter_container)):
    with c.uow() as uow:
        processos = uow.processos.listar()
        taxas = uow.cotacoes.mais_recentes()
    return [processo_resumo_dto(p, taxas) for p in processos]


@router.post("", response_model=ProcessoDTO, status_code=status.HTTP_201_CREATED)
def criar(corpo: ProcessoNovoIn, c: Container = Depends(obter_container)):
    valor = corpo.valor.para_dominio() if corpo.valor else None
    return _ver(c, c.funil().criar_manual(corpo.titulo, corpo.organizacao, valor, corpo.prazo))


@router.get("/{processo_id}", response_model=ProcessoDTO)
def detalhar(processo_id: int, c: Container = Depends(obter_container)):
    return _ver(c, _obter(c, processo_id))


@router.patch("/{processo_id}", response_model=ProcessoDTO)
def editar(processo_id: int, corpo: ProcessoEdicaoIn, c: Container = Depends(obter_container)):
    """Altera só os campos presentes no corpo; enviar null limpa organizacao, valor,
    prazo ou link (o título não pode ser limpo)."""
    campos = {k: getattr(corpo, k) for k in corpo.model_fields_set}
    if campos.get("valor") is not None:
        campos["valor"] = corpo.valor.para_dominio()
    return _ver(c, c.funil().editar(processo_id, **campos))


@router.post("/{processo_id}/etapa", response_model=ProcessoDTO)
def mover(processo_id: int, corpo: EtapaIn, c: Container = Depends(obter_container)):
    return _ver(c, c.funil().mover(processo_id, corpo.etapa))


@router.post("/{processo_id}/notas", response_model=ProcessoDTO)
def anotar(processo_id: int, corpo: NotaIn, c: Container = Depends(obter_container)):
    return _ver(c, c.funil().anotar(processo_id, corpo.texto))


@router.post(
    "/{processo_id}/arquivos", response_model=ArquivoDTO, status_code=status.HTTP_201_CREATED
)
def anexar(processo_id: int, arquivo: UploadFile, c: Container = Depends(obter_container)):
    limite = c.settings.arquivo_max_mb * 1024 * 1024
    conteudo = arquivo.file.read(limite + 1)
    if len(conteudo) > limite:
        raise HTTPException(413, f"Arquivo maior que {c.settings.arquivo_max_mb} MB")
    return arquivo_dto(c.funil().anexar(processo_id, nome_seguro(arquivo.filename), conteudo))


@router.get("/{processo_id}/arquivos/{arquivo_id}")
def baixar(processo_id: int, arquivo_id: int, c: Container = Depends(obter_container)):
    arquivo, conteudo = c.funil().abrir_arquivo(processo_id, arquivo_id)
    nome = nome_seguro(arquivo.nome)
    ascii_ = nome.encode("ascii", "replace").decode().replace("?", "_")
    disposicao = f'attachment; filename="{ascii_}"'
    if not nome.isascii():
        disposicao += "; filename*=UTF-8" + chr(39) * 2 + quote(nome)
    tipo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
    return Response(conteudo, media_type=tipo, headers={"Content-Disposition": disposicao})


@router.post("/{processo_id}/contatos/{contato_id}", response_model=ProcessoDTO)
def vincular_contato(processo_id: int, contato_id: int, c: Container = Depends(obter_container)):
    c.funil().vincular_contato(processo_id, contato_id)
    return _ver(c, _obter(c, processo_id))
