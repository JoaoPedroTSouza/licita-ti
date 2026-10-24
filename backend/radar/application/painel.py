"""Painel do dia: o que fazer hoje, o funil em números e as melhores novas."""
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from radar.application.portas import Relogio, UnidadeDeTrabalho
from radar.domain.dinheiro import converter_para_brl
from radar.domain.oportunidade import Oportunidade, StatusOportunidade
from radar.domain.processo import Etapa, Processo

LIMITE_MELHORES_NOVAS = 5


@dataclass(frozen=True)
class ItemParaFazer:
    tipo: Literal["lembrete", "prazo", "contato"]
    titulo: str
    quando: datetime | date | None
    ref_id: int
    processo_id: int | None


@dataclass(frozen=True)
class ResumoFunil:
    contagem: dict[Etapa, int]
    valor_aberto_brl: Decimal
    sem_conversao: int


@dataclass(frozen=True)
class PainelDoDia:
    dia: date
    para_fazer: list[ItemParaFazer]
    funil: ResumoFunil
    melhores_novas: list[Oportunidade]


class MontarPainelDoDia:
    def __init__(self, uow: UnidadeDeTrabalho, relogio: Relogio, tz: ZoneInfo) -> None:
        self._uow = uow
        self._relogio = relogio
        self._tz = tz

    def executar(self) -> PainelDoDia:
        agora = self._relogio.agora()
        hoje = agora.astimezone(self._tz).date()
        with self._uow:
            ajustes = self._uow.configuracoes.ajustes()
            processos = self._uow.processos.listar()
            lembretes = sorted(
                (l for l in self._uow.lembretes.nao_concluidos() if l.pendente_ate(hoje, self._tz)),
                key=lambda l: l.vence_em,
            )
            contatos = self._uow.contatos.listar()
            taxas = self._uow.cotacoes.mais_recentes()
            melhores = self._uow.oportunidades.listar(
                StatusOportunidade.NOVA, limite=LIMITE_MELHORES_NOVAS
            )

        limite = hoje + timedelta(days=max(ajustes.avisos_prazo_dias, default=0))
        com_prazo = sorted(
            (
                p for p in processos
                if p.aberto and p.prazo is not None and agora <= p.prazo
                and p.prazo.astimezone(self._tz).date() <= limite
            ),
            key=lambda p: p.prazo,
        )
        para_fazer = (
            [ItemParaFazer("lembrete", l.texto, l.vence_em, l.id, l.processo_id) for l in lembretes]
            + [ItemParaFazer("prazo", f"Prazo: {p.titulo}", p.prazo, p.id, p.id) for p in com_prazo]
            + [
                ItemParaFazer("contato", f"Falar com {c.nome}", c.ultimo_contato, c.id, None)
                for c in contatos if c.atrasado(hoje)
            ]
        )
        return PainelDoDia(hoje, para_fazer, _resumir_funil(processos, taxas), melhores)


def _resumir_funil(processos: list[Processo], taxas: Mapping[str, Decimal]) -> ResumoFunil:
    contagem = {etapa: 0 for etapa in Etapa}
    total = Decimal("0")
    sem_conversao = 0
    for p in processos:
        contagem[p.etapa] += 1
        if p.aberto and p.valor is not None:
            em_brl = converter_para_brl(p.valor, taxas)
            if em_brl is None:
                sem_conversao += 1
            else:
                total += em_brl
    return ResumoFunil(contagem, total, sem_conversao)
