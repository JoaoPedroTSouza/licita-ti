"""Processo do funil: etapas, notas, arquivos e histórico de mudanças."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from radar.domain.dinheiro import Dinheiro
from radar.domain.erros import ErroDeDominio, TransicaoInvalida


class Etapa(str, Enum):
    ANALISANDO = "analisando"
    PROPOSTA_ENVIADA = "proposta_enviada"
    NEGOCIACAO = "negociacao"
    FECHADO = "fechado"
    PERDIDO = "perdido"


ETAPAS_ABERTAS = frozenset({Etapa.ANALISANDO, Etapa.PROPOSTA_ENVIADA, Etapa.NEGOCIACAO})


@dataclass
class Nota:
    texto: str
    criada_em: datetime


@dataclass
class Arquivo:
    id: int | None
    nome: str
    chave: str
    tamanho: int
    enviado_em: datetime


@dataclass(frozen=True)
class MudancaEtapa:
    de: Etapa | None
    para: Etapa
    em: datetime


@dataclass
class Processo:
    id: int | None
    titulo: str
    organizacao: str | None
    etapa: Etapa
    criado_em: datetime
    oportunidade_id: int | None = None
    valor: Dinheiro | None = None
    prazo: datetime | None = None
    link: str | None = None
    notas: list[Nota] = field(default_factory=list)
    arquivos: list[Arquivo] = field(default_factory=list)
    historico: list[MudancaEtapa] = field(default_factory=list)
    contato_ids: set[int] = field(default_factory=set)
    avisos_prazo_enviados: set[int] = field(default_factory=set)

    @classmethod
    def novo(
        cls,
        titulo: str,
        agora: datetime,
        *,
        organizacao: str | None = None,
        oportunidade_id: int | None = None,
        valor: Dinheiro | None = None,
        prazo: datetime | None = None,
        link: str | None = None,
    ) -> "Processo":
        if not titulo.strip():
            raise ErroDeDominio("O título do processo não pode ser vazio.")
        return cls(
            id=None,
            titulo=titulo.strip(),
            organizacao=organizacao,
            etapa=Etapa.ANALISANDO,
            criado_em=agora,
            oportunidade_id=oportunidade_id,
            valor=valor,
            prazo=prazo,
            link=link,
            historico=[MudancaEtapa(None, Etapa.ANALISANDO, agora)],
        )

    @property
    def aberto(self) -> bool:
        return self.etapa in ETAPAS_ABERTAS

    def mover(self, para: Etapa, agora: datetime) -> None:
        """Qualquer mudança de etapa é permitida (inclusive reabrir), menos para a mesma."""
        if para == self.etapa:
            raise TransicaoInvalida(f"O processo já está em '{para.value}'.")
        self.historico.append(MudancaEtapa(self.etapa, para, agora))
        self.etapa = para

    def anotar(self, texto: str, agora: datetime) -> None:
        self.notas.append(Nota(texto, agora))

    def anexar(self, arquivo: Arquivo) -> None:
        self.arquivos.append(arquivo)

    def vincular_contato(self, contato_id: int) -> None:
        self.contato_ids.add(contato_id)
