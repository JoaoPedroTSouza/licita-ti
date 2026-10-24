import json
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import pytest

from radar.infrastructure.fontes.ungm import CONSULTAS_PADRAO, ConsultaUngm, FonteUngm

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "fontes" / "ungm"


def _ler(nome: str) -> bytes:
    return (FIXTURES / nome).read_bytes()


class ServidorUngm:
    """Imita o UNGM: página de busca (token), POST de busca e detalhe do aviso."""

    def __init__(self, listas: dict[str, bytes] | None = None, padrao: str = "lista_brasil.html"):
        self.buscas: list[dict] = []
        self.detalhes: list[str] = []
        self.listas = listas or {}
        self.padrao = padrao

    def __call__(self, req: httpx.Request) -> httpx.Response:
        if req.method == "GET" and req.url.path == "/Public/Notice":
            return httpx.Response(200, content=_ler("pagina_busca.html"))
        if req.method == "POST" and req.url.path == "/Public/Notice/Search":
            assert req.headers["RequestVerificationToken"]
            corpo = json.loads(req.content)
            self.buscas.append(corpo)
            if corpo["PageIndex"] > 0:
                return httpx.Response(200, content=_ler("lista_vazia.html"))
            return httpx.Response(200, content=self.listas.get(corpo["Title"], _ler(self.padrao)))
        if req.url.path.startswith("/Public/Notice/"):
            self.detalhes.append(req.url.path.rsplit("/", 1)[1])
            return httpx.Response(200, content=_ler("detalhe_316419.html"))
        return httpx.Response(404)


def _fonte(servidor, consultas, pausas=None):
    http = httpx.Client(transport=httpx.MockTransport(servidor))
    return FonteUngm(http, consultas, pausa=(pausas.append if pausas is not None else lambda s: None))


BRASIL = ConsultaUngm(pais="Brazil", palavras=())


def test_extrai_avisos_da_lista():
    avisos = _fonte(ServidorUngm(), [BRASIL]).buscar(date(2026, 10, 20))

    assert len(avisos) == 15
    lta = next(a for a in avisos if a.id_externo == "316419")
    assert lta.fonte == "ungm"
    assert lta.titulo == "Acordo de Longo Prazo (LTA) para Aulas de Português para funcionários internacionais"
    assert lta.organizacao == "UNICEF"
    assert lta.pais == "Brazil"
    # 03-Nov-2026 18:00 (GMT -3.00) == 21:00 UTC
    assert lta.prazo == datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc)
    assert lta.publicada_em == datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)
    assert "Request for proposal" in lta.texto and "UNICEF Brasil" in lta.texto


def test_link_aponta_para_o_aviso():
    avisos = _fonte(ServidorUngm(), [BRASIL]).buscar(date(2026, 10, 20))

    assert all(a.link == f"https://www.ungm.org/Public/Notice/{a.id_externo}" for a in avisos)


def test_html_sem_tabela_levanta_erro():
    servidor = ServidorUngm(listas={"": b"<html><body>Please verify you are human</body></html>"})

    with pytest.raises(ValueError, match="UNGM"):
        _fonte(servidor, [BRASIL]).buscar(date(2026, 10, 20))


def test_busca_sem_resultados_nao_e_erro():
    assert _fonte(ServidorUngm(padrao="lista_vazia.html"), [BRASIL]).buscar(date(2026, 10, 20)) == []


def test_filtros_da_requisicao():
    servidor = ServidorUngm()
    _fonte(servidor, [BRASIL]).buscar(date(2026, 10, 20))

    busca = servidor.buscas[0]
    assert busca["PublishedFrom"] == "20/10/2026"
    assert busca["IsActive"] is True
    assert busca["Countries"] == [2320]


def test_aplica_as_duas_consultas_e_junta_resultados():
    servidor = ServidorUngm(listas={"software": _ler("lista_software.html")})
    consultas = [BRASIL, ConsultaUngm(pais=None, palavras=("software",))]

    avisos = _fonte(servidor, consultas).buscar(date(2026, 10, 1))

    titulos_de_busca = [b["Title"] for b in servidor.buscas if b["PageIndex"] == 0]
    assert titulos_de_busca == ["", "software"]
    ids = [a.id_externo for a in avisos]
    assert len(ids) == len(set(ids)) > 15  # junta e remove repetidos
    assert len(servidor.detalhes) == len(ids)  # no máximo um detalhe por aviso


def test_pausa_de_um_segundo_entre_requisicoes():
    pausas: list[float] = []
    _fonte(ServidorUngm(), [BRASIL], pausas).buscar(date(2026, 10, 20))

    assert pausas and set(pausas) == {1.0}


def test_pais_desconhecido_levanta_erro():
    with pytest.raises(ValueError, match="Atlantis"):
        _fonte(ServidorUngm(), [ConsultaUngm(pais="Atlantis", palavras=())]).buscar(date(2026, 10, 20))


def test_consultas_padrao():
    assert CONSULTAS_PADRAO == (
        ConsultaUngm(pais="Brazil", palavras=()),
        ConsultaUngm(pais=None, palavras=("software", "information technology",
                                          "digital platform", "web development", "database")),
    )
