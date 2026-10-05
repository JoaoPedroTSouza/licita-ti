from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Status = Literal["novo", "analisando", "participando", "descartado"]


class LoginIn(BaseModel):
    senha: str


class TokenOut(BaseModel):
    token: str


class EditalResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_controle_pncp: str
    objeto: str
    orgao: str | None
    uf: str | None
    municipio: str | None
    modalidade_nome: str | None
    valor_estimado: float | None
    data_publicacao: datetime | None
    data_encerramento: datetime | None
    ia_relevante: bool | None
    ia_score: int | None
    ia_categoria: str | None
    keyword_score: int
    status: str
    favorito: bool


class EditalDetalhe(EditalResumo):
    cnpj: str
    ano: int
    sequencial: int
    numero_compra: str | None
    processo: str | None
    informacao_complementar: str | None
    unidade: str | None
    modo_disputa: str | None
    situacao: str | None
    srp: bool | None
    data_abertura: datetime | None
    link_origem: str | None
    link_pncp: str | None
    keywords_encontradas: list
    ia_resumo: str | None
    ia_motivo: str | None
    ia_exigencias: list
    notas: str | None


class EditalUpdate(BaseModel):
    status: Status | None = None
    favorito: bool | None = None
    notas: str | None = None


class Pagina(BaseModel):
    itens: list[EditalResumo]
    total: int
    pagina: int
    por_pagina: int


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushKeys


class ColetaIn(BaseModel):
    data: str | None = None  # YYYY-MM-DD; padrão = hoje
    dias: int = 1


class Resumo(BaseModel):
    novos_hoje: int
    relevantes_abertos: int
    por_status: dict[str, int]
    encerrando_em_48h: int
    ultima_coleta: datetime | None
