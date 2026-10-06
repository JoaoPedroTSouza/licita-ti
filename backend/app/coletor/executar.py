"""Orquestra uma coleta: PNCP → filtro → banco → IA → notificações."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import preferencias
from app.coletor.filtro import eh_candidato
from app.coletor.ia import Classificador
from app.coletor.pncp import PNCPClient, normalizar
from app.config import get_settings
from app.models import Edital, ExecucaoColeta
from app.push import enviar_para_todos

log = logging.getLogger(__name__)

# Campos que o PNCP pode atualizar (retificações) — status/notas/IA do usuário são preservados
CAMPOS_ATUALIZAVEIS = (
    "objeto", "informacao_complementar", "situacao", "valor_estimado",
    "data_abertura", "data_encerramento", "link_origem", "modo_disputa",
)


def hoje_br() -> date:
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    # SQLite devolve datetimes sem fuso; Postgres devolve com fuso
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _merece_push(e: Edital, prefs: dict, ia_ativa: bool) -> bool:
    if ia_ativa:
        return bool(e.ia_relevante) and (e.ia_score or 0) >= int(prefs.get("score_minimo_ia_push", 60))
    return e.keyword_score >= 4


def _encurtar(texto: str, n: int = 110) -> str:
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def coletar(db: Session, client: PNCPClient, inicio: date, fim: date, prefs: dict, execucao: ExecucaoColeta) -> None:
    for modalidade in prefs.get("modalidades") or []:
        for item in client.contratacoes_publicadas(inicio, fim, int(modalidade)):
            execucao.recebidos += 1
            dados = normalizar(item)
            if not dados["objeto"]:
                continue
            ok, score, termos = eh_candidato(dados, prefs)
            if not ok:
                continue

            existente = db.query(Edital).filter_by(numero_controle_pncp=dados["numero_controle_pncp"]).first()
            if existente:
                for campo in CAMPOS_ATUALIZAVEIS:
                    setattr(existente, campo, dados[campo])
                existente.keyword_score = score
                existente.keywords_encontradas = termos
                continue

            db.add(Edital(**dados, keyword_score=score, keywords_encontradas=termos))
            execucao.novos += 1
            execucao.candidatos += 1
        db.commit()


def classificar_pendentes(db: Session, classificador: Classificador, prefs: dict, limite: int) -> int:
    if not classificador.ativo:
        return 0
    pendentes = (
        db.query(Edital)
        .filter(Edital.ia_processado.is_(False))
        .order_by(Edital.keyword_score.desc(), Edital.data_publicacao.desc())
        .limit(limite)
        .all()
    )
    relevantes = 0
    for e in pendentes:
        dados = {c: getattr(e, c) for c in (
            "numero_controle_pncp", "orgao", "municipio", "uf", "modalidade_nome",
            "modo_disputa", "valor_estimado", "objeto", "informacao_complementar",
        )}
        resultado = classificador.classificar(dados, prefs.get("perfil", ""))
        if resultado is None:
            continue
        for k, v in resultado.items():
            setattr(e, k, v)
        if e.ia_relevante:
            relevantes += 1
        db.commit()
    return relevantes


def notificar_novos(db: Session, prefs: dict, ia_ativa: bool) -> int:
    agora = _agora()
    q = db.query(Edital).filter(Edital.notificado.is_(False))
    if ia_ativa:
        q = q.filter(Edital.ia_processado.is_(True))  # espera a IA avaliar antes de decidir
    pendentes = q.all()

    enviar: list[Edital] = []
    for e in pendentes:
        enc = _aware(e.data_encerramento)
        aberto = enc is None or enc > agora
        if aberto and _merece_push(e, prefs, ia_ativa):
            enviar.append(e)
        e.notificado = True
    db.commit()

    if not enviar:
        return 0

    enviar.sort(key=lambda x: (x.ia_score or 0, x.keyword_score), reverse=True)
    if len(enviar) == 1:
        e = enviar[0]
        titulo = f"Novo edital · {e.uf or ''} {e.modalidade_nome or ''}".strip()
        corpo = _encurtar(e.ia_resumo or e.objeto, 160)
        url = f"/editais/{e.id}"
    else:
        titulo = f"{len(enviar)} novos editais de TI"
        corpo = "\n".join(f"• {_encurtar(x.objeto, 70)}" for x in enviar[:3])
        url = "/editais?filtro=relevantes"
    enviar_para_todos(db, titulo, corpo, url=url, tag="novos-editais")
    return len(enviar)


def enviar_lembretes(db: Session) -> int:
    """Avisa sobre editais em análise/participação cujo prazo de propostas termina em breve."""
    s = get_settings()
    agora = _agora()
    limite = agora + timedelta(hours=s.lembrete_horas_antes)
    proximos = (
        db.query(Edital)
        .filter(Edital.status.in_(("analisando", "participando")))
        .filter(Edital.lembrete_enviado.is_(False))
        .filter(Edital.data_encerramento.isnot(None))
        .all()
    )
    enviados = 0
    for e in proximos:
        enc = _aware(e.data_encerramento)
        if not (agora < enc <= limite):
            continue
        horas = int((enc - agora).total_seconds() // 3600)
        prazo = f"em {horas}h" if horas < 24 else f"em {horas // 24} dia(s)"
        enviar_para_todos(
            db,
            f"⏰ Prazo encerra {prazo}",
            _encurtar(e.objeto, 140),
            url=f"/editais/{e.id}",
            tag=f"prazo-{e.id}",
        )
        e.lembrete_enviado = True
        enviados += 1
    db.commit()
    return enviados


def executar_coleta(
    db: Session,
    data_ref: date | None = None,
    dias: int = 1,
    client: PNCPClient | None = None,
    classificador: Classificador | None = None,
) -> ExecucaoColeta:
    s = get_settings()
    prefs = preferencias.carregar(db)
    fim = data_ref or hoje_br()
    inicio = fim - timedelta(days=max(1, dias) - 1)

    execucao = ExecucaoColeta(
        data_referencia=fim.isoformat(), recebidos=0, novos=0, candidatos=0, relevantes=0, notificados=0
    )
    db.add(execucao)
    db.commit()

    proprio_client = client is None
    client = client or PNCPClient()
    classificador = classificador or Classificador()
    try:
        coletar(db, client, inicio, fim, prefs, execucao)
        execucao.relevantes = classificar_pendentes(db, classificador, prefs, s.llm_max_por_execucao)
        execucao.notificados = notificar_novos(db, prefs, classificador.ativo)
    except Exception as e:
        log.exception("Coleta falhou")
        execucao.erro = str(e)[:2000]
    finally:
        if proprio_client:
            client.close()
        execucao.finalizado_em = _agora()
        db.commit()

    log.info(
        "Coleta %s: recebidos=%d novos=%d relevantes=%d notificados=%d",
        fim, execucao.recebidos, execucao.novos, execucao.relevantes, execucao.notificados,
    )
    return execucao
