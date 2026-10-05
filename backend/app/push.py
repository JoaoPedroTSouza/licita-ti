"""Envio de notificações Web Push (VAPID) para todos os dispositivos inscritos."""

from __future__ import annotations

import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PushSubscription

log = logging.getLogger(__name__)


def push_configurado() -> bool:
    s = get_settings()
    return bool(s.vapid_private_key and s.vapid_public_key)


def enviar_para_todos(db: Session, titulo: str, corpo: str, url: str = "/", tag: str | None = None) -> int:
    """Envia a notificação para todas as inscrições. Retorna quantas foram entregues."""
    s = get_settings()
    if not push_configurado():
        log.info("Push não configurado (VAPID ausente); notificação ignorada: %s", titulo)
        return 0

    payload = json.dumps({"title": titulo, "body": corpo, "url": url, "tag": tag})
    entregues = 0
    for sub in db.query(PushSubscription).all():
        try:
            webpush(
                subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                data=payload,
                vapid_private_key=s.vapid_private_key,
                vapid_claims={"sub": s.vapid_subject},
                ttl=60 * 60 * 24,
            )
            entregues += 1
        except WebPushException as e:
            status = getattr(e.response, "status_code", None)
            if status in (404, 410):  # inscrição expirada/removida no aparelho
                db.delete(sub)
                db.commit()
            else:
                log.warning("Falha no push (%s): %s", status, e)
    return entregues
