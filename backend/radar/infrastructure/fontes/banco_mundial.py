"""Fonte Banco Mundial: avisos de aquisição (https://search.worldbank.org/api/v2/procnotices).

Pedimos só `notice_type = Request for Expression of Interest` (consultorias), ordenados por data
de publicação decrescente, em páginas de 100 (`rows`/`os`); a API ignora filtros de data, então
paramos de paginar ao passar de `desde`. Os avisos são globais: a regra "somente remoto" fica no
classificador/domínio. `submission_deadline_date` + `submission_deadline_time` são tratados como UTC
(a API não informa o fuso local do mutuário). Avisos sem prazo são mantidos; vencidos, descartados.
"""
import re
from collections.abc import Callable
from datetime import date, datetime, timezone

import httpx
from bs4 import BeautifulSoup

from radar.domain.oportunidade import OportunidadeBruta

URL = "https://search.worldbank.org/api/v2/procnotices"
URL_AVISO = "https://projects.worldbank.org/en/projects-operations/procurement-detail/"
TIPO_CONSULTORIA = "Request for Expression of Interest"
USER_AGENT = "RadarBot/1.0 (consulta pessoal de oportunidades; contato: jpsouzatavaress@gmail.com)"
POR_PAGINA = 100
MAX_PAGINAS = 10
_MESES = {m: i for i, m in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
_IDIOMAS = {"english": "en", "french": "fr", "portuguese": "pt", "spanish; castilian": "es",
            "spanish": "es", "russian": "ru", "arabic": "ar", "chinese": "zh"}


class FonteBancoMundial:
    nome = "banco_mundial"

    def __init__(self, http: httpx.Client,
                 agora: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._http = http
        self._agora = agora

    def buscar(self, desde: date) -> list[OportunidadeBruta]:
        agora = self._agora()
        itens: list[OportunidadeBruta] = []
        for pagina in range(MAX_PAGINAS):
            avisos = self._pagina(pagina * POR_PAGINA)
            publicados = [(a, _data_aviso(a)) for a in avisos]
            for aviso, publicada in publicados:
                if publicada.date() < desde:
                    continue
                item = _item(aviso, publicada)
                if item.prazo is None or item.prazo >= agora:
                    itens.append(item)
            if len(avisos) < POR_PAGINA or publicados[-1][1].date() < desde:
                break
        return itens

    def _pagina(self, deslocamento: int) -> list[dict]:
        resposta = self._http.get(URL, headers={"User-Agent": USER_AGENT}, params={
            "format": "json", "apilang": "en", "notice_type": TIPO_CONSULTORIA,
            "srt": "noticedate", "order": "desc", "rows": POR_PAGINA, "os": deslocamento})
        resposta.raise_for_status()
        try:
            avisos = resposta.json()["procnotices"]
        except (ValueError, KeyError, TypeError) as erro:
            raise ValueError("Banco Mundial: resposta sem a lista 'procnotices'") from erro
        if not isinstance(avisos, list):
            raise ValueError("Banco Mundial: 'procnotices' não é uma lista")
        return avisos


def _data_aviso(aviso: dict) -> datetime:
    try:
        dia, mes, ano = str(aviso["noticedate"]).split("-")
        return datetime(int(ano), _MESES[mes], int(dia), tzinfo=timezone.utc)
    except (KeyError, ValueError) as erro:
        raise ValueError(f"Banco Mundial: data de aviso não reconhecida: {aviso.get('noticedate')!r}") from erro


def _prazo(aviso: dict) -> datetime | None:
    data = aviso.get("submission_deadline_date")
    if not data:
        return None
    try:
        prazo = datetime.fromisoformat(str(data).replace("Z", "+00:00"))
        hora = aviso.get("submission_deadline_time")
        if hora:
            h, m = (int(p) for p in str(hora).split(":")[:2])
            prazo = prazo.replace(hour=h, minute=m)
        return prazo.astimezone(timezone.utc)
    except ValueError as erro:
        raise ValueError(f"Banco Mundial: prazo não reconhecido: {data!r} {aviso.get('submission_deadline_time')!r}") from erro


def _item(aviso: dict, publicada: datetime) -> OportunidadeBruta:
    try:
        id_aviso, titulo, projeto = aviso["id"], aviso["bid_description"], aviso["project_name"]
    except KeyError as erro:
        raise ValueError(f"Banco Mundial: aviso sem o campo {erro}") from erro
    pais = aviso.get("project_ctry_name") or None
    corpo = _texto_plano(aviso.get("notice_text") or "")
    return OportunidadeBruta(
        fonte="banco_mundial", id_externo=id_aviso, titulo=titulo.strip(),
        organizacao="Banco Mundial — " + projeto, link=URL_AVISO + id_aviso,
        texto="\n".join(p for p in (titulo.strip(), projeto, pais or "", corpo) if p),
        pais=pais, idioma=_IDIOMAS.get(str(aviso.get("notice_lang_name", "")).lower()),
        prazo=_prazo(aviso), publicada_em=publicada)


def _texto_plano(html: str) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(" ", strip=True)).strip()
