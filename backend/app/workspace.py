"""Workspace: cadastro de ideias e painel de monitoramento."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import exigir_login
from app.config import get_settings
from app.db import get_db
from app.models import Edital, ExecucaoColeta, Ideia
from app.schemas import IdeiaIn, IdeiaOut, IdeiaUpdate

router = APIRouter(prefix="/api", dependencies=[Depends(exigir_login)])


def _limpar_tags(tags: list[str]) -> list[str]:
    vistas, saida = set(), []
    for t in tags:
        t = " ".join(t.split()).lower()[:40]
        if t and t not in vistas:
            vistas.add(t)
            saida.append(t)
    return saida[:12]


def _validar_edital(db: Session, edital_id: int | None) -> None:
    if edital_id is not None and db.get(Edital, edital_id) is None:
        raise HTTPException(422, "Edital vinculado não existe")


# ---------- Ideias ----------
@router.get("/ideias", response_model=list[IdeiaOut])
def listar_ideias(
    status: str | None = None,
    q: str | None = None,
    edital_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Ideia)
    if status:
        query = query.filter(Ideia.status.in_(status.split(",")))
    if edital_id is not None:
        query = query.filter(Ideia.edital_id == edital_id)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(Ideia.titulo.ilike(termo), Ideia.descricao.ilike(termo)))
    return query.order_by(Ideia.atualizado_em.desc()).limit(500).all()


@router.post("/ideias", response_model=IdeiaOut, status_code=201)
def criar_ideia(body: IdeiaIn, db: Session = Depends(get_db)):
    _validar_edital(db, body.edital_id)
    dados = body.model_dump()
    dados["titulo"] = dados["titulo"].strip()
    dados["tags"] = _limpar_tags(dados["tags"])
    ideia = Ideia(**dados)
    db.add(ideia)
    db.commit()
    db.refresh(ideia)
    return ideia


@router.get("/ideias/{ideia_id}", response_model=IdeiaOut)
def obter_ideia(ideia_id: int, db: Session = Depends(get_db)):
    ideia = db.get(Ideia, ideia_id)
    if not ideia:
        raise HTTPException(404, "Ideia não encontrada")
    return ideia


@router.patch("/ideias/{ideia_id}", response_model=IdeiaOut)
def atualizar_ideia(ideia_id: int, body: IdeiaUpdate, db: Session = Depends(get_db)):
    ideia = db.get(Ideia, ideia_id)
    if not ideia:
        raise HTTPException(404, "Ideia não encontrada")
    campos = body.model_dump(exclude_unset=True)
    if "edital_id" in campos:
        _validar_edital(db, campos["edital_id"])
    if "tags" in campos and campos["tags"] is not None:
        campos["tags"] = _limpar_tags(campos["tags"])
    for campo, valor in campos.items():
        if valor is None and campo not in ("descricao", "potencial_mensal", "edital_id"):
            continue
        setattr(ideia, campo, valor)
    db.commit()
    db.refresh(ideia)
    return ideia


@router.delete("/ideias/{ideia_id}", status_code=204)
def excluir_ideia(ideia_id: int, db: Session = Depends(get_db)):
    ideia = db.get(Ideia, ideia_id)
    if not ideia:
        raise HTTPException(404, "Ideia não encontrada")
    db.delete(ideia)
    db.commit()


# ---------- Painel ----------
def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _relevante(e: Edital) -> bool:
    return bool(e.ia_relevante) or (not e.ia_processado and e.keyword_score >= 4)


@router.get("/painel")
def painel(dias: int = Query(14, ge=7, le=60), db: Session = Depends(get_db)):
    tz = ZoneInfo(get_settings().timezone)
    agora = datetime.now(timezone.utc)
    hoje = agora.astimezone(tz).date()
    inicio = hoje - timedelta(days=dias - 1)
    desde = datetime.combine(inicio, datetime.min.time(), tz)

    # Série diária por data de publicação (calculada em Python para funcionar em qualquer banco)
    recentes = db.query(Edital).filter(Edital.data_publicacao >= desde).all()
    serie = {inicio + timedelta(days=i): {"candidatos": 0, "relevantes": 0} for i in range(dias)}
    for e in recentes:
        d = _aware(e.data_publicacao).astimezone(tz).date()
        if d in serie:
            serie[d]["candidatos"] += 1
            if _relevante(e):
                serie[d]["relevantes"] += 1

    # Editais em aberto, não descartados
    abertos = (
        db.query(Edital)
        .filter(Edital.status != "descartado")
        .filter(or_(Edital.data_encerramento.is_(None), Edital.data_encerramento > agora))
        .all()
    )
    abertos_rel = [e for e in abertos if _relevante(e) or e.status in ("analisando", "participando")]

    janela = agora + timedelta(days=14)
    prazos = sorted(
        (e for e in abertos_rel if e.data_encerramento and _aware(e.data_encerramento) <= janela),
        key=lambda e: _aware(e.data_encerramento),
    )[:40]

    por_uf = Counter(e.uf or "—" for e in abertos_rel).most_common(8)
    por_categoria = Counter(e.ia_categoria or "sem análise" for e in abertos_rel).most_common(6)
    funil = Counter(e.status for e in db.query(Edital.status).all())
    ideias = Counter(s for (s,) in db.query(Ideia.status).all())
    coletas = db.query(ExecucaoColeta).order_by(ExecucaoColeta.id.desc()).limit(8).all()
    valor_aberto = sum(e.valor_estimado or 0 for e in abertos_rel)

    return {
        "gerado_em": agora,
        "kpis": {
            "relevantes_abertos": len(abertos_rel),
            "novos_7d": sum(v["relevantes"] for d, v in serie.items() if d > hoje - timedelta(days=7)),
            "analisando": funil.get("analisando", 0),
            "participando": funil.get("participando", 0),
            "encerrando_48h": sum(1 for e in prazos if _aware(e.data_encerramento) <= agora + timedelta(hours=48)),
            "valor_em_aberto": valor_aberto,
            "ideias_ativas": sum(ideias.get(s, 0) for s in ("nova", "validando", "executando")),
        },
        "serie": [{"data": d.isoformat(), **v} for d, v in serie.items()],
        "prazos": [
            {
                "id": e.id,
                "objeto": e.objeto,
                "orgao": e.orgao,
                "uf": e.uf,
                "status": e.status,
                "ia_score": e.ia_score,
                "valor_estimado": e.valor_estimado,
                "data_encerramento": _aware(e.data_encerramento),
            }
            for e in prazos
        ],
        "por_uf": [{"uf": uf, "total": n} for uf, n in por_uf],
        "por_categoria": [{"categoria": c, "total": n} for c, n in por_categoria],
        "funil": {s: funil.get(s, 0) for s in ("novo", "analisando", "participando", "descartado")},
        "ideias": {s: ideias.get(s, 0) for s in ("nova", "validando", "executando", "concluida", "descartada")},
        "coletas": [
            {
                "id": c.id,
                "finalizado_em": _aware(c.finalizado_em),
                "recebidos": c.recebidos,
                "novos": c.novos,
                "relevantes": c.relevantes,
                "notificados": c.notificados,
                "erro": c.erro,
            }
            for c in coletas
        ],
    }
