"""Processo agendado: coletas diárias + lembretes de prazo.

Rodar: python -m app.worker
"""

import logging
from datetime import timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.coletor.executar import enviar_lembretes, executar_coleta, hoje_br
from app.config import get_settings
from app.db import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("worker")


def job_coleta() -> None:
    db = SessionLocal()
    try:
        # Busca hoje e ontem: o PNCP às vezes publica com atraso e o upsert evita duplicatas
        executar_coleta(db, data_ref=hoje_br(), dias=2)
    finally:
        db.close()


def job_lembretes() -> None:
    db = SessionLocal()
    try:
        n = enviar_lembretes(db)
        if n:
            log.info("Lembretes de prazo enviados: %d", n)
    finally:
        db.close()


def main() -> None:
    s = get_settings()
    init_db()
    sched = BlockingScheduler(timezone=s.timezone)
    sched.add_job(job_coleta, CronTrigger(hour=s.coleta_horarios, minute=5, timezone=s.timezone),
                  id="coleta", max_instances=1, coalesce=True)
    sched.add_job(job_lembretes, CronTrigger(minute=30, timezone=s.timezone),
                  id="lembretes", max_instances=1, coalesce=True)
    log.info("Worker iniciado. Coletas às %sh (+5min), lembretes a cada hora.", s.coleta_horarios)
    job_coleta()  # primeira coleta ao subir
    sched.start()


if __name__ == "__main__":
    main()
