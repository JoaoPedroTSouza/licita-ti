"""Processo agendado: coleta, resumo diário, avisos de prazo e cotações.

Rodar: python -m radar.interfaces.worker
"""
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from radar.config import get_settings
from radar.container import Container

log = logging.getLogger("worker")


def _protegido(nome: str, acao: Callable[[], object]) -> Callable[[], None]:
    """Falha num job é logada e nunca derruba o worker."""

    def rodar() -> None:
        try:
            acao()
        except Exception:
            log.exception("Falha no job '%s'", nome)

    return rodar


def _coletar(container: Container) -> None:
    desde = datetime.now(ZoneInfo(container.settings.timezone)).date() - timedelta(days=2)
    container.coletar().executar(desde)


def registrar_jobs(agendador, container: Container) -> None:
    s = container.settings
    tz = s.timezone
    opcoes = {"max_instances": 1, "coalesce": True}

    agendador.add_job(
        _protegido("coleta", lambda: _coletar(container)),
        CronTrigger(hour=s.coleta_horarios, minute=5, timezone=tz), id="coleta", **opcoes,
    )
    agendador.add_job(
        _protegido("resumo", lambda: container.resumo_diario().executar()),
        IntervalTrigger(minutes=15, timezone=tz), id="resumo", **opcoes,
    )
    agendador.add_job(
        _protegido("prazos", lambda: container.verificar_prazos().executar()),
        CronTrigger(minute=30, timezone=tz), id="prazos", **opcoes,
    )
    agendador.add_job(
        _protegido("cotacoes", lambda: container.atualizar_cotacoes().executar()),
        CronTrigger(hour=14, minute=0, timezone=tz), id="cotacoes", **opcoes,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = get_settings()
    container = Container.de_settings(settings)
    agendador = BlockingScheduler(timezone=settings.timezone)
    registrar_jobs(agendador, container)
    # Ao subir: cotações e uma coleta, com a mesma proteção dos jobs agendados
    _protegido("cotacoes", lambda: container.atualizar_cotacoes().executar())()
    _protegido("coleta", lambda: _coletar(container))()
    log.info("Worker iniciado. Coletas às %sh (+5min).", settings.coleta_horarios)
    agendador.start()


if __name__ == "__main__":
    main()
