import json

import pytest
from pywebpush import WebPushException
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from radar.infrastructure.db import tabelas as t
from radar.infrastructure.db.repositorios import criar_engine, criar_tabelas
from radar.infrastructure.push.webpush import NotificadorWebPush


@pytest.fixture
def fabrica():
    engine = criar_engine("sqlite+pysqlite:///:memory:")
    criar_tabelas(engine)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()


def _contar(fabrica) -> int:
    with fabrica() as s:
        return s.scalar(select(func.count()).select_from(t.inscricoes_push))


class _Resposta:
    def __init__(self, status_code):
        self.status_code = status_code


def test_inscricao_expirada_e_removida(fabrica):
    chamadas = []

    def enviar(subscription_info, data, vapid_private_key, vapid_claims, ttl):
        chamadas.append((subscription_info, json.loads(data), vapid_claims, ttl))
        if subscription_info["endpoint"] == "https://p/1":
            raise WebPushException("gone", response=_Resposta(410))

    n = NotificadorWebPush(fabrica, "chave", "mailto:a@b.c", enviar=enviar)
    n.inscrever("https://p/1", "k1", "a1", "UA")
    n.inscrever("https://p/2", "k2", "a2", None)
    assert n.enviar("t", "c", "/x") == 1
    assert _contar(fabrica) == 1
    assert chamadas[0][1] == {"title": "t", "body": "c", "url": "/x"}
    assert chamadas[0][2] == {"sub": "mailto:a@b.c"} and chamadas[0][3] == 86400
    assert n.enviar("t", "c", "/") == 1  # só a válida resta


def test_erro_transitorio_mantem_inscricao(fabrica):
    def enviar(**_):
        raise WebPushException("boom", response=_Resposta(500))

    n = NotificadorWebPush(fabrica, "chave", "mailto:a@b.c", enviar=enviar)
    n.inscrever("https://p/1", "k", "a", None)
    assert n.enviar("t", "c", "/") == 0
    assert _contar(fabrica) == 1


def test_sem_vapid_nao_envia(fabrica):
    def enviar(**_):
        raise AssertionError("não deveria enviar")

    n = NotificadorWebPush(fabrica, "", "mailto:a@b.c", enviar=enviar)
    n.inscrever("https://p/1", "k", "a", None)
    assert n.configurado is False
    assert n.enviar("t", "c", "/") == 0
    assert NotificadorWebPush(fabrica, "chave", "mailto:a@b.c").configurado is True


def test_inscrever_duas_vezes_mesmo_endpoint_nao_duplica(fabrica):
    n = NotificadorWebPush(fabrica, "chave", "mailto:a@b.c", enviar=lambda **_: None)
    n.inscrever("https://p/1", "k1", "a1", "UA1")
    n.inscrever("https://p/1", "k2", "a2", "UA2")
    assert _contar(fabrica) == 1
    with fabrica() as s:
        linha = s.execute(select(t.inscricoes_push)).mappings().one()
    assert (linha["p256dh"], linha["auth"], linha["user_agent"]) == ("k2", "a2", "UA2")
