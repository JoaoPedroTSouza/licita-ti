"""Entidades e valores do domínio de oportunidades."""
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from radar.domain.dinheiro import Dinheiro

FUSO_PRAZOS = ZoneInfo("America/Sao_Paulo")


class Modalidade(str, Enum):
    REMOTO_TOTAL = "remoto_total"
    COM_PRESENCA = "com_presenca"
    INDEFINIDO = "indefinido"


class TipoContratacao(str, Enum):
    EMPRESA = "empresa"
    PESSOA_FISICA = "pessoa_fisica"


class StatusOportunidade(str, Enum):
    PENDENTE = "pendente"
    NOVA = "nova"
    INTERESSA = "interessa"
    DESCARTADA = "descartada"
    DESCARTADA_AUTO = "descartada_auto"


class MotivoDescarteAuto(str, Enum):
    NAO_REMOTA = "nao_remota"
    IDIOMA = "idioma"
    PRAZO_VENCIDO = "prazo_vencido"
    IRRELEVANTE = "irrelevante"


def _normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    sem_pontuacao = re.sub(r"[^\w\s]", " ", sem_acento.lower())
    return " ".join(sem_pontuacao.split())


@dataclass(frozen=True)
class OportunidadeBruta:
    fonte: str
    id_externo: str
    titulo: str
    organizacao: str
    link: str
    texto: str
    pais: str | None = None
    prazo: datetime | None = None
    valor: Dinheiro | None = None
    publicada_em: datetime | None = None
    idioma: str | None = None

    def chave_deduplicacao(self) -> str:
        """sha256 de título normalizado + dia do prazo em Brasília.

        A organização fica de fora: cada fonte a nomeia de um jeito ("PAHO", "OPAS/OMS Brasil").
        """
        prazo = self.prazo.astimezone(FUSO_PRAZOS).date().isoformat() if self.prazo else "-"
        partes = f"{_normalizar(self.titulo)}|{prazo}"
        return hashlib.sha256(partes.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Classificacao:
    relevante: bool
    nota: int
    resumo: str
    modalidade: Modalidade
    trecho_modalidade: str
    idioma: str
    tipo_contratacao: TipoContratacao
    motivo: str
    prazo: datetime | None = None
    valor: Dinheiro | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.nota <= 100:
            raise ValueError(f"nota fora de 0..100: {self.nota}")


@dataclass
class Oportunidade:
    id: int | None
    bruta: OportunidadeBruta
    coletada_em: datetime
    status: StatusOportunidade = StatusOportunidade.PENDENTE
    classificacao: Classificacao | None = None
    motivo_auto: MotivoDescarteAuto | None = None
    motivo_usuario: str | None = None
    processo_id: int | None = None

    @property
    def prazo(self) -> datetime | None:
        if self.bruta.prazo:  # o prazo estruturado da fonte vale mais que o lido pela IA
            return self.bruta.prazo
        return self.classificacao.prazo if self.classificacao else None

    @property
    def valor(self) -> Dinheiro | None:
        if self.bruta.valor:
            return self.bruta.valor
        return self.classificacao.valor if self.classificacao else None

    @property
    def pessoa_fisica(self) -> bool:
        return (
            self.classificacao is not None
            and self.classificacao.tipo_contratacao == TipoContratacao.PESSOA_FISICA
        )
