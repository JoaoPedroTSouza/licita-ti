from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import pytest

from radar.infrastructure.fontes.opas import FonteOpas

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "fontes" / "opas"
URL_ANTIGA = "/pt/licitacoes-opas"
URL_ATUAL = "/pt/licitacoes-e-oportunidades-opas-no-brasil"


def _fonte(arquivo: str | None = None, conteudo: bytes | None = None) -> FonteOpas:
    corpo = conteudo if conteudo is not None else (FIXTURES / arquivo).read_bytes()

    def servidor(req: httpx.Request) -> httpx.Response:
        assert "RadarBot" in req.headers["User-Agent"]
        if req.url.path == URL_ANTIGA:
            return httpx.Response(301, headers={"Location": URL_ATUAL})
        assert req.url.path == URL_ATUAL
        return httpx.Response(200, content=corpo)

    return FonteOpas(httpx.Client(transport=httpx.MockTransport(servidor)))


def test_extrai_itens_com_prazo_em_formato_brasileiro():
    itens = _fonte("pagina_varios.html").buscar(date(2026, 10, 1))

    assert len(itens) == 3
    por_link = {i.link: i for i in itens}
    aviso = por_link["https://www.ungm.org/Public/Notice/999001"]
    assert aviso.fonte == "opas"
    assert aviso.id_externo == aviso.link
    assert aviso.titulo == "Contratação de consultoria para desenvolvimento de sistema de informação em saúde"
    assert aviso.organizacao == "OPAS/OMS Brasil"
    assert aviso.pais == "Brasil"
    assert aviso.idioma == "pt"
    # 08/10/2026 23:59 BRT (UTC-3) == 09/10/2026 02:59 UTC
    assert aviso.prazo == datetime(2026, 10, 9, 2, 59, tzinfo=timezone.utc)
    assert "Prazo final" in aviso.texto and aviso.titulo in aviso.texto
    relativo = por_link["https://www.paho.org/sites/default/files/edital-plataforma.pdf"]
    assert relativo.prazo == datetime(2026, 11, 21, 2, 59, tzinfo=timezone.utc)
    real = next(i for i in itens if i.link.startswith("https://pan-american"))
    assert real.titulo.startswith("Contratação de fornecedor para aquisição de bens móveis")


def test_ignora_itens_com_prazo_passado_em_relacao_a_desde():
    itens = _fonte("pagina_varios.html").buscar(date(2026, 10, 10))

    assert [i.prazo.date() for i in itens] == [date(2026, 11, 21)]


def test_prazo_no_proprio_dia_de_desde_ainda_vale():
    itens = _fonte("pagina_varios.html").buscar(date(2026, 10, 8))

    assert len(itens) == 3


def test_pagina_sem_lista_levanta_erro():
    with pytest.raises(ValueError, match="OPAS"):
        _fonte(conteudo=b"<html><body><main><p>Manutencao</p></main></body></html>").buscar(date(2026, 10, 1))


def test_corpo_sem_avisos_com_prazo_levanta_erro():
    html = b'<article><div class="field--name-body"><p>Nenhuma oportunidade.</p></div></article>'
    with pytest.raises(ValueError, match="OPAS"):
        _fonte(conteudo=html).buscar(date(2026, 10, 1))
