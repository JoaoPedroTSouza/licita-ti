"""Composição: monta adaptadores e casos de uso. Cada fábrica devolve instâncias novas
(a unidade de trabalho SQL guarda estado por instância e não é segura entre threads)."""
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import sessionmaker

from radar.application.coletar import ColetarOportunidades
from radar.application.cotacoes import AtualizarCotacoes
from radar.application.funil import Funil
from radar.application.notificacoes import EnviarResumoDiario, VerificarPrazos
from radar.application.painel import MontarPainelDoDia
from radar.application.portas import (
    ArmazenamentoArquivos, Classificador, FonteDeCotacoes, FonteDeOportunidades, Relogio,
)
from radar.application.rede import Rede
from radar.application.triar import TriarOportunidade
from radar.config import Settings
from radar.domain.oportunidade import OportunidadeBruta
from radar.infrastructure.arquivos.disco import ArmazenamentoEmDisco
from radar.infrastructure.cotacoes.ptax import FontePtax
from radar.infrastructure.db.repositorios import (
    UnidadeDeTrabalhoSql, criar_engine, criar_tabelas,
)
from radar.infrastructure.fontes.banco_mundial import FonteBancoMundial
from radar.infrastructure.fontes.opas import FonteOpas
from radar.infrastructure.fontes.ungm import CONSULTAS_PADRAO, FonteUngm
from radar.infrastructure.ia.claude import criar_classificador
from radar.infrastructure.push.webpush import NotificadorWebPush


class RelogioReal:
    def agora(self) -> datetime:
        return datetime.now(UTC)


class Container:
    def __init__(
        self,
        settings: Settings,
        fabrica_sessao: sessionmaker,
        relogio: Relogio,
        notificador: NotificadorWebPush,
        classificador: Classificador | None,
        fontes: list[FonteDeOportunidades],
        armazenamento: ArmazenamentoArquivos,
        fonte_cotacoes: FonteDeCotacoes,
    ) -> None:
        self.settings = settings
        self.fabrica_sessao = fabrica_sessao
        self.relogio = relogio
        self.notificador = notificador
        self.classificador = classificador
        self.fontes = fontes
        self.armazenamento = armazenamento
        self.fonte_cotacoes = fonte_cotacoes
        self.tz = ZoneInfo(settings.timezone)

    @classmethod
    def de_settings(cls, settings: Settings) -> "Container":
        engine = criar_engine(settings.database_url)
        criar_tabelas(engine)
        fabrica = sessionmaker(engine, expire_on_commit=False)
        http = httpx.Client(timeout=30, follow_redirects=True)

        def conhecido(bruta: OportunidadeBruta) -> bool:
            with UnidadeDeTrabalhoSql(fabrica) as uow:
                return uow.oportunidades.existe_chave(bruta.chave_deduplicacao())

        return cls(
            settings=settings,
            fabrica_sessao=fabrica,
            relogio=RelogioReal(),
            notificador=NotificadorWebPush(
                fabrica, settings.vapid_private_key, settings.vapid_subject
            ),
            classificador=criar_classificador(settings),
            fontes=[
                FonteUngm(http, list(CONSULTAS_PADRAO), conhecido=conhecido),
                FonteOpas(http),
                FonteBancoMundial(http),
            ],
            armazenamento=ArmazenamentoEmDisco(Path(settings.arquivos_dir)),
            fonte_cotacoes=FontePtax(http),
        )

    def uow(self) -> UnidadeDeTrabalhoSql:
        return UnidadeDeTrabalhoSql(self.fabrica_sessao)

    def triar(self) -> TriarOportunidade:
        return TriarOportunidade(self.uow(), self.relogio)

    def funil(self) -> Funil:
        return Funil(self.uow(), self.relogio, self.armazenamento)

    def rede(self) -> Rede:
        return Rede(self.uow(), self.relogio, self.tz)

    def painel(self) -> MontarPainelDoDia:
        return MontarPainelDoDia(self.uow(), self.relogio, self.tz)

    def coletar(self) -> ColetarOportunidades:
        return ColetarOportunidades(
            self.uow(), self.fontes, self.classificador, self.notificador, self.relogio,
            self.settings.app_url, self.settings.llm_max_por_execucao,
        )

    def resumo_diario(self) -> EnviarResumoDiario:
        return EnviarResumoDiario(
            self.uow(), self.notificador, self.relogio, self.tz, self.settings.app_url
        )

    def verificar_prazos(self) -> VerificarPrazos:
        return VerificarPrazos(
            self.uow(), self.notificador, self.relogio, self.tz, self.settings.app_url
        )

    def atualizar_cotacoes(self) -> AtualizarCotacoes:
        return AtualizarCotacoes(self.uow(), self.fonte_cotacoes, self.relogio)
