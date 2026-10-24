"""Notificador Web Push (VAPID): entrega a todos os aparelhos inscritos."""
import json
import logging
from datetime import UTC, datetime

from pywebpush import WebPushException, webpush
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import sessionmaker

from radar.infrastructure.db import tabelas as t

log = logging.getLogger(__name__)

TTL_SEGUNDOS = 60 * 60 * 24


class NotificadorWebPush:
    def __init__(self, fabrica_sessao: sessionmaker, vapid_private_key: str,
                 vapid_subject: str, enviar=webpush) -> None:
        self._fabrica = fabrica_sessao
        self._chave = vapid_private_key
        self._subject = vapid_subject
        self._enviar = enviar

    @property
    def configurado(self) -> bool:
        return bool(self._chave)

    def inscrever(self, endpoint: str, p256dh: str, auth: str, user_agent: str | None) -> None:
        with self._fabrica() as s, s.begin():
            existe = s.scalar(select(t.inscricoes_push.c.id).where(t.inscricoes_push.c.endpoint == endpoint))
            if existe is None:
                s.execute(insert(t.inscricoes_push).values(
                    endpoint=endpoint, p256dh=p256dh, auth=auth, user_agent=user_agent,
                    criado_em=datetime.now(UTC)))
            else:
                s.execute(update(t.inscricoes_push).where(t.inscricoes_push.c.id == existe)
                          .values(p256dh=p256dh, auth=auth, user_agent=user_agent))

    def enviar(self, titulo: str, corpo: str, url: str) -> int:
        if not self.configurado:
            log.info("Push não configurado (VAPID ausente); notificação ignorada: %s", titulo)
            return 0
        payload = json.dumps({"title": titulo, "body": corpo, "url": url})
        with self._fabrica() as s:
            inscricoes = s.execute(select(t.inscricoes_push)).mappings().all()
        entregues = 0
        expiradas: list[int] = []
        for sub in inscricoes:
            try:
                self._enviar(
                    subscription_info={"endpoint": sub["endpoint"],
                                       "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}},
                    data=payload, vapid_private_key=self._chave,
                    vapid_claims={"sub": self._subject}, ttl=TTL_SEGUNDOS)
                entregues += 1
            except WebPushException as e:
                status = getattr(e.response, "status_code", None)
                if status in (404, 410):  # inscrição expirada/removida no aparelho
                    expiradas.append(sub["id"])
                else:
                    log.warning("Falha no push (%s): %s", status, e)
        if expiradas:
            with self._fabrica() as s, s.begin():
                s.execute(delete(t.inscricoes_push).where(t.inscricoes_push.c.id.in_(expiradas)))
        return entregues
