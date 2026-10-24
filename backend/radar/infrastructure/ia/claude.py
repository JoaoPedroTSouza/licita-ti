"""Classificador de oportunidades sobre a API da Anthropic (Claude)."""
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from radar.application.portas import ClassificacaoIndisponivel, DescarteRecente
from radar.config import Settings
from radar.domain.dinheiro import Dinheiro
from radar.domain.oportunidade import (
    Classificacao, Modalidade, OportunidadeBruta, TipoContratacao,
)
from radar.domain.perfil import Perfil

MAX_TOKENS = 700
MAX_TEXTO = 12_000
MAX_DESCARTES = 20

SISTEMA = """Você avalia chamadas de consultoria para um consultor independente, conforme o Perfil informado.

Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois, com as chaves:
relevante, nota, resumo, modalidade, trecho_modalidade, idioma, tipo_contratacao, prazo, valor, moeda, motivo.

Regras:
- relevante: true ou false.
- nota: inteiro de 0 a 100, considerando o Perfil, a faixa de valor e os descartes recentes.
- resumo: em português, 2 a 3 frases.
- modalidade: "remoto_total" SOMENTE se o texto disser explicitamente que todo o trabalho é remoto e não houver nenhuma viagem, missão, reunião presencial, exigência de residência ou de local, nem formato híbrido. Se houver qualquer um desses, "com_presenca". Se o texto não disser nada, "indefinido".
- trecho_modalidade: o trecho do texto que sustenta a modalidade.
- idioma: código ISO 639-1 do texto da chamada.
- tipo_contratacao: "pessoa_fisica" quando a chamada for para consultor individual, senão "empresa".
- prazo: data limite em ISO 8601, ou null.
- valor: número, ou null; moeda: código ISO 4217, ou null.
- motivo: uma frase justificando a nota."""


def _extrair_json(texto: str) -> dict:
    texto = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.MULTILINE)
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim < inicio:
        raise ValueError("resposta sem JSON")
    dados = json.loads(texto[inicio : fim + 1])
    if not isinstance(dados, dict):
        raise ValueError("JSON não é um objeto")
    return dados


def _prazo(valor) -> datetime | None:
    if valor is None:
        return None
    prazo = datetime.fromisoformat(valor)
    return prazo.replace(tzinfo=timezone.utc) if prazo.tzinfo is None else prazo


def _dinheiro(valor, moeda) -> Dinheiro | None:
    if valor is None or not moeda:
        return None
    if isinstance(valor, bool):
        raise ValueError("valor inválido")
    try:
        return Dinheiro(Decimal(str(valor)), str(moeda))
    except InvalidOperation as erro:
        raise ValueError("valor inválido") from erro


def _classificacao(dados: dict) -> Classificacao:
    nota = dados["nota"]
    if isinstance(nota, bool) or not isinstance(nota, int):
        raise ValueError("nota deve ser inteira")
    if not isinstance(dados["relevante"], bool):
        raise ValueError("relevante deve ser booleano")
    return Classificacao(
        relevante=dados["relevante"],
        nota=nota,
        resumo=str(dados["resumo"]),
        modalidade=Modalidade(dados["modalidade"]),
        trecho_modalidade=str(dados.get("trecho_modalidade") or ""),
        idioma=str(dados["idioma"]).lower(),
        tipo_contratacao=TipoContratacao(dados["tipo_contratacao"]),
        motivo=str(dados["motivo"]),
        prazo=_prazo(dados.get("prazo")),
        valor=_dinheiro(dados.get("valor"), dados.get("moeda")),
    )


def _mensagem(bruta: OportunidadeBruta, perfil: Perfil, descartes: list[DescarteRecente]) -> str:
    faixa = f"{perfil.faixa_min_brl or '-'} a {perfil.faixa_max_brl or '-'} BRL"
    linhas = [f"- {d.titulo}: {d.motivo}" for d in descartes[:MAX_DESCARTES]]
    valor = f"{bruta.valor.valor} {bruta.valor.moeda}" if bruta.valor else "não informado"
    return (
        f"PERFIL:\n{perfil.texto}\nFaixa de valor desejada: {faixa}\n\n"
        f"DESCARTES RECENTES:\n{chr(10).join(linhas) or '(nenhum)'}\n\n"
        f"CHAMADA:\nTítulo: {bruta.titulo}\nOrganização: {bruta.organizacao}\n"
        f"País: {bruta.pais or 'não informado'}\n"
        f"Prazo: {bruta.prazo.isoformat() if bruta.prazo else 'não informado'}\n"
        f"Valor: {valor}\nTexto:\n{bruta.texto[:MAX_TEXTO]}"
    )


class ClassificadorClaude:
    def __init__(self, cliente, modelo: str) -> None:
        self._cliente = cliente
        self._modelo = modelo

    def classificar(
        self, bruta: OportunidadeBruta, perfil: Perfil, descartes: list[DescarteRecente]
    ) -> Classificacao:
        try:
            resposta = self._cliente.messages.create(
                model=self._modelo,
                max_tokens=MAX_TOKENS,
                system=SISTEMA,
                messages=[{"role": "user", "content": _mensagem(bruta, perfil, descartes)}],
            )
            texto = "".join(b.text for b in resposta.content if getattr(b, "type", "") == "text")
            return _classificacao(_extrair_json(texto))
        except Exception as erro:
            raise ClassificacaoIndisponivel(f"classificação falhou: {erro}") from erro


def criar_classificador(settings: Settings) -> ClassificadorClaude | None:
    if not settings.anthropic_api_key:
        return None
    import anthropic

    return ClassificadorClaude(
        anthropic.Anthropic(api_key=settings.anthropic_api_key), settings.llm_model
    )
