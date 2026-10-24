"""Fonte UNGM: avisos de compras da ONU (https://www.ungm.org/Public/Notice).

A página pública busca com um POST JSON em /Public/Notice/Search, protegido por token
anti-CSRF (campo oculto da própria página + cookie) e devolve HTML parcial com as linhas.
Prazos vêm como "03-Nov-2026 18:00 (GMT -3.00)" e são convertidos para UTC; se vier só a
data, vale 23:59 no fuso informado (UTC se não houver). Datas de publicação ficam à 00:00 UTC.
"""
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time as hora, timedelta, timezone

import httpx
from bs4 import BeautifulSoup, Tag

from radar.domain.oportunidade import OportunidadeBruta

log = logging.getLogger(__name__)

BASE = "https://www.ungm.org"
PAUSA_SEGUNDOS = 1.0
POR_PAGINA = 15
MAX_PAGINAS = 3
USER_AGENT = "RadarBot/1.0 (consulta pessoal de oportunidades; contato: jpsouzatavaress@gmail.com)"
# Ids de país usados pelo filtro da página (select #selNoticeCountry).
PAISES = {"Brazil": 2320}
_MESES = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


@dataclass(frozen=True)
class ConsultaUngm:
    pais: str | None
    palavras: tuple[str, ...]


CONSULTAS_PADRAO = (
    ConsultaUngm(pais="Brazil", palavras=()),
    ConsultaUngm(pais=None, palavras=("software", "information technology",
                                      "digital platform", "web development", "database")),
)


class FonteUngm:
    nome = "ungm"

    def __init__(self, http: httpx.Client, consultas: list[ConsultaUngm],
                 pausa: Callable[[float], None] = time.sleep,
                 conhecido: Callable[[OportunidadeBruta], bool] | None = None) -> None:
        self._http = http
        self._conhecido = conhecido
        self._consultas = consultas
        self._pausa = pausa
        self._primeira = True

    def buscar(self, desde: date) -> list[OportunidadeBruta]:
        self._primeira = True
        token = self._token()
        avisos: dict[str, OportunidadeBruta] = {}
        for consulta in self._consultas:
            for titulo in consulta.palavras or ("",):
                for aviso in self._buscar_consulta(token, consulta.pais, titulo, desde):
                    avisos.setdefault(aviso.id_externo, aviso)
        return [a if self._conhecido and self._conhecido(a) else self._com_detalhe(a)
                for a in avisos.values()]

    def _requisitar(self, metodo: str, caminho: str, **kwargs) -> httpx.Response:
        if not self._primeira:
            self._pausa(PAUSA_SEGUNDOS)
        self._primeira = False
        resposta = self._http.request(metodo, BASE + caminho, headers={
            "User-Agent": USER_AGENT, **kwargs.pop("headers", {})}, **kwargs)
        resposta.raise_for_status()
        return resposta

    def _token(self) -> str:
        pagina = BeautifulSoup(self._requisitar("GET", "/Public/Notice").text, "html.parser")
        campo = pagina.find("input", attrs={"name": "__RequestVerificationToken"})
        if not isinstance(campo, Tag) or not campo.get("value"):
            raise ValueError("UNGM: token anti-CSRF não encontrado na página de busca")
        return str(campo["value"])

    def _buscar_consulta(self, token: str, pais: str | None, titulo: str,
                         desde: date) -> list[OportunidadeBruta]:
        if pais is not None and pais not in PAISES:
            raise ValueError(f"UNGM: país sem id conhecido: {pais}")
        encontrados: list[OportunidadeBruta] = []
        for pagina in range(MAX_PAGINAS):
            corpo = {
                "PageIndex": pagina, "PageSize": POR_PAGINA, "Title": titulo, "Description": "",
                "Reference": "", "PublishedFrom": f"{desde:%d/%m/%Y}", "PublishedTo": "",
                "DeadlineFrom": "", "DeadlineTo": "",
                "Countries": [PAISES[pais]] if pais else [], "Agencies": [], "UNSPSCs": [],
                "NoticeTypes": [], "SortField": "DatePublished", "SortAscending": False,
                "isPicker": False, "IsSustainable": False, "IsActive": True,
                "NoticeDisplayType": None, "NoticeSearchTotalLabelId": "noticeSearchTotal",
                "TypeOfCompetitions": [],
            }
            html = self._requisitar("POST", "/Public/Notice/Search", json=corpo, headers={
                "RequestVerificationToken": token, "X-Requested-With": "XMLHttpRequest"}).text
            linhas = _extrair_linhas(html)
            encontrados.extend(linhas)
            if len(linhas) < POR_PAGINA:
                break
        else:
            log.warning("UNGM: consulta (pais=%s, titulo=%r) truncada em %d páginas",
                        pais, titulo, MAX_PAGINAS)
        return encontrados

    def _com_detalhe(self, aviso: OportunidadeBruta) -> OportunidadeBruta:
        try:
            html = self._requisitar("GET", f"/Public/Notice/{aviso.id_externo}").text
        except httpx.HTTPError as e:
            log.warning("UNGM: detalhe do aviso %s indisponível: %s", aviso.id_externo, e)
            return aviso
        painel = BeautifulSoup(html, "html.parser").select_one("div.ungm-panel")
        if painel is None:
            return aviso
        detalhe = " ".join(painel.get_text(" ", strip=True).split())
        return OportunidadeBruta(**{**aviso.__dict__, "texto": f"{aviso.texto}\n{detalhe}"})


def _extrair_linhas(html: str) -> list[OportunidadeBruta]:
    sopa = BeautifulSoup(html, "html.parser")
    linhas = sopa.select("div.tableRow.dataRow[data-noticeid]")
    if not linhas:
        if "noticeSearchScript" in html:  # resposta válida de busca sem resultados
            return []
        raise ValueError("UNGM: formato da resposta de busca não reconhecido (sem linhas de aviso)")
    return [_aviso(linha) for linha in linhas]


def _aviso(linha: Tag) -> OportunidadeBruta:
    celulas = linha.find_all("div", class_="tableCell", recursive=False)
    if len(celulas) < 8:
        raise ValueError(f"UNGM: linha de aviso com {len(celulas)} colunas (esperadas 8)")
    titulo_tag = celulas[1].select_one("span.ungm-title")
    titulo = _texto(titulo_tag) if titulo_tag else _texto(celulas[1])
    _, _, prazo, publicada, agencia, tipo, referencia, pais = (_texto(c) for c in celulas[:8])
    id_aviso = str(linha["data-noticeid"])
    return OportunidadeBruta(
        fonte="ungm", id_externo=id_aviso, titulo=titulo, organizacao=agencia,
        link=f"{BASE}/Public/Notice/{id_aviso}",
        texto="\n".join((titulo, tipo, f"Referência: {referencia}", agencia, pais)),
        pais=pais or None, prazo=_converter_prazo(prazo), publicada_em=_converter_data(publicada))


def _texto(celula: Tag) -> str:
    for lixo in celula.find_all("script"):
        lixo.decompose()
    return " ".join(celula.get_text(" ", strip=True).split())


def _converter_data(texto: str) -> datetime | None:
    m = re.search(r"(\d{2})-([A-Z][a-z]{2})-(\d{4})", texto)
    if not m or m[2] not in _MESES:
        return None
    return datetime(int(m[3]), _MESES[m[2]], int(m[1]), tzinfo=timezone.utc)


def _converter_prazo(texto: str) -> datetime | None:
    dia = _converter_data(texto)
    if dia is None:
        return None
    h = re.search(r"\b(\d{1,2}):(\d{2})\b", texto)
    deslocamento = re.search(r"GMT\s*([+-]?\d+(?:\.\d+)?)", texto)
    fuso = timezone(timedelta(hours=float(deslocamento[1]))) if deslocamento else timezone.utc
    horario = hora(int(h[1]), int(h[2])) if h else hora(23, 59)
    return datetime.combine(dia.date(), horario, tzinfo=fuso).astimezone(timezone.utc)
