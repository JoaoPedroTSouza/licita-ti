"""Cliente da API de Consulta do PNCP (https://pncp.gov.br/api/consulta/swagger-ui/index.html).

Endpoint usado: GET /v1/contratacoes/publicacao
  - dataInicial / dataFinal: yyyyMMdd
  - codigoModalidadeContratacao: obrigatório (uma modalidade por chamada)
  - pagina (>=1), tamanhoPagina (10..50)
  - uf: opcional
Respostas: 200 com {data, totalPaginas, paginasRestantes, ...} ou 204 quando vazio.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import Iterator
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)
TZ_BR = ZoneInfo("America/Sao_Paulo")


class PNCPClient:
    def __init__(self, base_url: str | None = None, page_size: int | None = None, timeout: float = 40.0):
        s = get_settings()
        self.base_url = (base_url or s.pncp_base_url).rstrip("/")
        self.page_size = max(10, min(50, page_size or s.pncp_page_size))
        self.http = httpx.Client(
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": "licita-ti/1.0"},
        )

    def close(self) -> None:
        self.http.close()

    def _get(self, path: str, params: dict, tentativas: int = 4) -> dict | None:
        url = f"{self.base_url}{path}"
        for i in range(tentativas):
            try:
                r = self.http.get(url, params=params)
            except httpx.HTTPError as e:
                log.warning("PNCP erro de rede (%s), tentativa %d", e, i + 1)
                time.sleep(2 ** i)
                continue
            if r.status_code == 204:
                return None
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                log.warning("PNCP %s, tentativa %d", r.status_code, i + 1)
                time.sleep(2 ** (i + 1))
                continue
            # 400/422: parâmetros inválidos — não adianta repetir
            log.error("PNCP %s: %s", r.status_code, r.text[:300])
            return None
        raise RuntimeError(f"PNCP indisponível após {tentativas} tentativas: {path}")

    def contratacoes_publicadas(
        self, inicio: date, fim: date, modalidade: int, uf: str | None = None
    ) -> Iterator[dict]:
        pagina = 1
        while True:
            params = {
                "dataInicial": inicio.strftime("%Y%m%d"),
                "dataFinal": fim.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": modalidade,
                "pagina": pagina,
                "tamanhoPagina": self.page_size,
            }
            if uf:
                params["uf"] = uf
            dados = self._get("/v1/contratacoes/publicacao", params)
            if not dados or not dados.get("data"):
                return
            yield from dados["data"]
            if not dados.get("paginasRestantes"):
                return
            pagina += 1
            time.sleep(0.3)  # gentileza com a API pública


def _dt(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        return None
    # O PNCP devolve horário de Brasília sem fuso
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ_BR)


def normalizar(item: dict) -> dict:
    """Converte um item da API para os campos do modelo Edital."""
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    cnpj = orgao.get("cnpj") or ""
    ano = item.get("anoCompra") or 0
    seq = item.get("sequencialCompra") or 0
    return {
        "numero_controle_pncp": item.get("numeroControlePNCP") or f"{cnpj}-{ano}-{seq}",
        "cnpj": cnpj,
        "ano": ano,
        "sequencial": seq,
        "numero_compra": item.get("numeroCompra"),
        "processo": item.get("processo"),
        "objeto": (item.get("objetoCompra") or "").strip(),
        "informacao_complementar": (item.get("informacaoComplementar") or "").strip() or None,
        "orgao": orgao.get("razaoSocial"),
        "unidade": unidade.get("nomeUnidade"),
        "uf": unidade.get("ufSigla"),
        "municipio": unidade.get("municipioNome"),
        "modalidade_id": item.get("modalidadeId"),
        "modalidade_nome": item.get("modalidadeNome"),
        "modo_disputa": item.get("modoDisputaNome"),
        "situacao": item.get("situacaoCompraNome"),
        "srp": item.get("srp"),
        "valor_estimado": item.get("valorTotalEstimado"),
        "data_publicacao": _dt(item.get("dataPublicacaoPncp")),
        "data_abertura": _dt(item.get("dataAberturaProposta")),
        "data_encerramento": _dt(item.get("dataEncerramentoProposta")),
        "link_origem": item.get("linkSistemaOrigem") or item.get("linkProcessoEletronico"),
        "link_pncp": f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}" if cnpj else None,
    }
