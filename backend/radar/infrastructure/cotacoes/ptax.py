"""Cotação PTAX do Banco Central (OData Olinda), com recuo em dias sem boletim."""
import json
import logging
from datetime import date, timedelta
from decimal import Decimal

import httpx

log = logging.getLogger(__name__)

URL = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
       "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)")
DIAS_DE_RECUO = 7


class FontePtax:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def cotacao(self, moeda: str, ate: date) -> tuple[date, Decimal] | None:
        for recuo in range(DIAS_DE_RECUO + 1):
            dia = ate - timedelta(days=recuo)
            try:
                boletins = self._boletins(moeda, dia)
                ultimo = max(boletins, key=lambda b: b["dataHoraCotacao"]) if boletins else None
                valor = ultimo["cotacaoVenda"] if ultimo else None
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as e:
                log.warning("PTAX indisponível (%s %s): %s", moeda, dia, e)
                return None
            if valor is not None:
                return dia, valor
        return None

    def _boletins(self, moeda: str, dia: date) -> list[dict]:
        resposta = self._http.get(URL, params={
            "@moeda": f"'{moeda}'", "@dataCotacao": f"'{dia:%m-%d-%Y}'", "$format": "json"})
        resposta.raise_for_status()
        return json.loads(resposta.content, parse_float=Decimal)["value"]
