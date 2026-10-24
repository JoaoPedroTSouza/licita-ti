"""Fonte OPAS Brasil: página de licitações (https://www.paho.org/pt/licitacoes-e-oportunidades-opas-no-brasil).

A página é HTML renderizado no servidor (Drupal) com texto livre no corpo: cada aviso é uma
sequência de parágrafos: título (em negrito), "Prazo final para envio de propostas: dd/mm/aaaa"
e um link "Clique aqui". Prazos "dd/mm/aaaa" valem 23:59 em America/Sao_Paulo, convertidos para UTC.
A URL antiga /pt/licitacoes-opas redireciona para a atual.
"""
import re
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup, Tag

from radar.domain.oportunidade import OportunidadeBruta

URL = "https://www.paho.org/pt/licitacoes-e-oportunidades-opas-no-brasil"
USER_AGENT = "RadarBot/1.0 (consulta pessoal de oportunidades; contato: jpsouzatavaress@gmail.com)"
BRT = ZoneInfo("America/Sao_Paulo")
_PRAZO = re.compile(r"prazo[^\d]*(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)
_MARCADORES = re.compile(r"^[^\w(\[]+")  # emojis e símbolos no início da linha


class FonteOpas:
    nome = "opas"

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def buscar(self, desde: date) -> list[OportunidadeBruta]:
        resposta = self._http.get(URL, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
        resposta.raise_for_status()
        corpo = BeautifulSoup(resposta.text, "html.parser").select_one(
            "article div.field--name-body")
        if corpo is None:
            raise ValueError("OPAS: corpo da página de licitações não encontrado")
        paragrafos = corpo.find_all("p")
        itens = [self._item(paragrafos, i) for i, p in enumerate(paragrafos)
                 if _PRAZO.search(p.get_text(" ", strip=True))]
        if not itens:
            raise ValueError("OPAS: formato da página não reconhecido (nenhum aviso com prazo)")
        limite = datetime.combine(desde, time.min, tzinfo=BRT)
        return [i for i in itens if i.prazo >= limite]

    @staticmethod
    def _item(paragrafos: list[Tag], posicao: int) -> OportunidadeBruta:
        m = _PRAZO.search(paragrafos[posicao].get_text(" ", strip=True))
        dia, mes, ano = (int(g) for g in m.groups())
        prazo = datetime(ano, mes, dia, 23, 59, tzinfo=BRT).astimezone(timezone.utc)
        titulo = _limpar(paragrafos[posicao - 1].get_text(" ", strip=True)) if posicao else ""
        link = _link(paragrafos, posicao)
        if not titulo or link is None:
            raise ValueError("OPAS: aviso sem título ou sem link: " + paragrafos[posicao].get_text(" ", strip=True))
        return OportunidadeBruta(
            fonte="opas", id_externo=link, titulo=titulo, organizacao="OPAS/OMS Brasil",
            link=link, texto=f"{titulo}\n{_limpar(paragrafos[posicao].get_text(' ', strip=True))}",
            pais="Brasil", idioma="pt", prazo=prazo)


def _link(paragrafos: list[Tag], posicao: int) -> str | None:
    for p in paragrafos[posicao:]:
        if p is not paragrafos[posicao] and _PRAZO.search(p.get_text(" ", strip=True)):
            return None  # chegou no próximo aviso sem achar link
        a = p.find("a", href=True)
        if a is not None:
            return str(httpx.URL(URL).join(str(a["href"])))
    return None


def _limpar(texto: str) -> str:
    return _MARCADORES.sub("", texto).strip()
