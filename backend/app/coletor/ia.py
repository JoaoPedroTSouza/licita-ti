"""Classificação e resumo dos editais candidatos com um LLM (Anthropic Claude)."""

from __future__ import annotations

import json
import logging
import re

from app.config import get_settings

log = logging.getLogger(__name__)

SISTEMA = """Você é analista de licitações públicas brasileiras especializado em serviços de TI.
Avalie se a contratação é uma oportunidade real para o perfil do fornecedor descrito.

Considere RELEVANTE: desenvolvimento de sites, portais, sistemas web, aplicativos, APIs/integrações,
sustentação/manutenção de software, fábrica de software, consultoria/assessoria em TI, UX/UI, BI, IA aplicada.
Considere NÃO relevante: compra de equipamentos, licenças de prateleira, impressão, telefonia, links de internet,
cabeamento, suporte presencial de hardware, ou serviços sem componente de software/consultoria.

Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois, com as chaves:
{
  "relevante": true|false,
  "score": inteiro 0-100 (aderência ao perfil e viabilidade para equipe pequena),
  "categoria": uma de ["desenvolvimento web", "sistema sob medida", "aplicativo", "sustentação", "consultoria TI", "fábrica de software", "outro TI", "não TI"],
  "resumo": "2 a 3 frases em português explicando o que o órgão quer contratar",
  "motivo": "1 frase justificando o score (ex.: porte, exigências, presencialidade)",
  "exigencias": ["até 5 exigências prováveis de habilitação/técnicas citadas ou implícitas"]
}"""


def _montar_prompt(edital: dict, perfil: str) -> str:
    valor = edital.get("valor_estimado")
    valor_txt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor else "não informado"
    return f"""PERFIL DO FORNECEDOR:
{perfil}

CONTRATAÇÃO:
- Órgão: {edital.get('orgao')} ({edital.get('municipio')}/{edital.get('uf')})
- Modalidade: {edital.get('modalidade_nome')} | Disputa: {edital.get('modo_disputa')}
- Valor estimado: {valor_txt}
- Objeto: {edital.get('objeto')}
- Informação complementar: {edital.get('informacao_complementar') or '-'}
"""


def _extrair_json(texto: str) -> dict:
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.MULTILINE).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("Resposta sem JSON")
    return json.loads(texto[inicio : fim + 1])


class Classificador:
    def __init__(self):
        s = get_settings()
        self.modelo = s.llm_model
        self.client = None
        if s.anthropic_api_key:
            import anthropic

            self.client = anthropic.Anthropic(api_key=s.anthropic_api_key)

    @property
    def ativo(self) -> bool:
        return self.client is not None

    def classificar(self, edital: dict, perfil: str) -> dict | None:
        if not self.client:
            return None
        try:
            resp = self.client.messages.create(
                model=self.modelo,
                max_tokens=600,
                system=SISTEMA,
                messages=[{"role": "user", "content": _montar_prompt(edital, perfil)}],
            )
            texto = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            dados = _extrair_json(texto)
        except Exception as e:  # rede, cota, JSON inválido…
            log.warning("Falha na classificação IA de %s: %s", edital.get("numero_controle_pncp"), e)
            return None

        score = int(max(0, min(100, int(dados.get("score", 0)))))
        return {
            "ia_processado": True,
            "ia_relevante": bool(dados.get("relevante")),
            "ia_score": score,
            "ia_categoria": str(dados.get("categoria", ""))[:80] or None,
            "ia_resumo": dados.get("resumo"),
            "ia_motivo": dados.get("motivo"),
            "ia_exigencias": [str(x) for x in (dados.get("exigencias") or [])][:5],
        }
