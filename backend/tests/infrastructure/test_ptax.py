import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx

from radar.infrastructure.cotacoes.ptax import FontePtax

FIXTURE = Path(__file__).parent.parent / "fixtures" / "ptax" / "usd.json"


def _fonte(handler) -> FontePtax:
    return FontePtax(httpx.Client(transport=httpx.MockTransport(handler)))


def test_ptax_usa_ultimo_boletim():
    pedidos = []

    def handler(req: httpx.Request) -> httpx.Response:
        pedidos.append(req)
        return httpx.Response(200, content=FIXTURE.read_bytes())

    assert _fonte(handler).cotacao("USD", date(2026, 10, 22)) == (date(2026, 10, 22), Decimal("5.0383"))
    assert "10-22-2026" in str(pedidos[0].url) and "USD" in str(pedidos[0].url)


def test_ptax_recua_no_fim_de_semana():
    vazio = {"value": []}
    com_valor = {"value": [{"cotacaoVenda": 5.1, "dataHoraCotacao": "2026-10-22 13:00:00.0"}]}

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        corpo = com_valor if "10-22-2026" in url else vazio
        return httpx.Response(200, content=json.dumps(corpo).encode())

    # 24/10/2026 é sábado; sexta 23 vazia (feriado simulado); quinta 22 tem valor
    assert _fonte(handler).cotacao("USD", date(2026, 10, 24)) == (date(2026, 10, 22), Decimal("5.1"))


def test_ptax_sem_dados_em_7_dias_devolve_none():
    def handler(req):
        return httpx.Response(200, json={"value": []})

    assert _fonte(handler).cotacao("USD", date(2026, 10, 24)) is None


def test_ptax_erro_http_devolve_none():
    assert _fonte(lambda req: httpx.Response(500)).cotacao("USD", date(2026, 10, 22)) is None


def test_ptax_erro_de_rede_devolve_none():
    def handler(req):
        raise httpx.ConnectError("sem rede")

    assert _fonte(handler).cotacao("USD", date(2026, 10, 22)) is None
