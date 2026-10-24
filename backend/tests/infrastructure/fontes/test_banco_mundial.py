import json
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import pytest

from radar.infrastructure.fontes import banco_mundial
from radar.infrastructure.fontes.banco_mundial import FonteBancoMundial

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "fontes" / "banco_mundial"
AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def _fonte(arquivo: str | None = None, conteudo: bytes | None = None,
           pedidos: list[httpx.Request] | None = None) -> FonteBancoMundial:
    corpo = conteudo if conteudo is not None else (FIXTURES / arquivo).read_bytes()

    def servidor(req: httpx.Request) -> httpx.Response:
        assert "RadarBot" in req.headers["User-Agent"]
        assert req.url.path == "/api/v2/procnotices"
        assert req.url.params["notice_type"] == "Request for Expression of Interest"
        if pedidos is not None:
            pedidos.append(req)
        return httpx.Response(200, content=corpo)

    return FonteBancoMundial(httpx.Client(transport=httpx.MockTransport(servidor)), agora=lambda: AGORA)


def test_converte_itens_em_oportunidades_brutas():
    itens = _fonte("eoi_pagina.json").buscar(date(2026, 10, 1))

    por_id = {i.id_externo: i for i in itens}
    assert set(por_id) == {"OP00476722", "OP00476533", "OP00476037", "OP00475655"}
    i = por_id["OP00476722"]
    assert i.fonte == "banco_mundial"
    assert i.titulo.startswith("Consulting Services for Practical Training on Agricultural Drone")
    assert i.organizacao == "Banco Mundial — Strengthening Resilience of the Agriculture Sector Project"
    assert i.link == "https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00476722"
    assert i.pais == "Tajikistan"
    assert i.idioma == "en"
    assert i.prazo == datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    assert i.publicada_em == datetime(2026, 10, 22, tzinfo=timezone.utc)
    assert "REQUEST FOR EXPRESSIONS OF INTEREST" in i.texto and "<p>" not in i.texto
    assert por_id["OP00476037"].idioma == "pt"


def test_mantem_so_avisos_em_aberto_e_publicados_desde_a_data():
    abertos = {i.id_externo for i in _fonte("eoi_pagina.json").buscar(date(2026, 10, 1))}
    assert "OP00476773" not in abertos and "OP00476837" not in abertos  # prazo de 22/10, vencido

    recentes = {i.id_externo for i in _fonte("eoi_pagina.json").buscar(date(2026, 10, 20))}
    assert recentes == {"OP00476722", "OP00476533"}


def test_pagina_ate_passar_de_desde(monkeypatch):
    monkeypatch.setattr(banco_mundial, "POR_PAGINA", 3)
    avisos = json.loads((FIXTURES / "eoi_pagina.json").read_bytes())["procnotices"]
    # ordem da fixture: 22/10 (x4), 19/10, 16/10 -> páginas [22,22,22] e [22,19,16]
    pedidos: list[httpx.Request] = []

    def servidor(req: httpx.Request) -> httpx.Response:
        pedidos.append(req)
        os = int(req.url.params["os"])
        return httpx.Response(200, json={"procnotices": avisos[os:os + 3]})

    fonte = FonteBancoMundial(httpx.Client(transport=httpx.MockTransport(servidor)), agora=lambda: AGORA)

    itens = fonte.buscar(date(2026, 10, 19))
    assert [p.url.params["os"] for p in pedidos] == ["0", "3"]  # a 2ª página já traz 16/10 e encerra
    assert {i.id_externo for i in itens} == {"OP00476722", "OP00476533", "OP00476037"}

    pedidos.clear()
    fonte.buscar(date(2026, 10, 1))  # nada anterior a 01/10: segue até a página vazia
    assert [p.url.params["os"] for p in pedidos] == ["0", "3", "6"]


def test_lista_vazia_legitima_devolve_lista_vazia():
    assert _fonte("eoi_vazia.json").buscar(date(2026, 10, 1)) == []


@pytest.mark.parametrize("corpo", [b'{"erro": "x"}', b"<html>manutencao</html>", b'{"procnotices": {}}'])
def test_resposta_com_formato_inesperado_levanta_erro(corpo):
    with pytest.raises(ValueError, match="Banco Mundial"):
        _fonte(conteudo=corpo).buscar(date(2026, 10, 1))
