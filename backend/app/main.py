import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import preferencias
from app.auth import exigir_login, gerar_token, senha_confere
from app.coletor.executar import executar_coleta
from app.config import get_settings
from app.db import SessionLocal, get_db, init_db
from app.models import Edital, ExecucaoColeta, PushSubscription
from app.push import enviar_para_todos, push_configurado
from app.workspace import router as workspace_router
from app.schemas import (
    ColetaIn, EditalDetalhe, EditalUpdate, LoginIn, Pagina, PushSubscriptionIn, Resumo, TokenOut,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()

app = FastAPI(title="Licita TI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(workspace_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True, "push": push_configurado(), "ia": bool(settings.anthropic_api_key)}


# ---------- Auth ----------
@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn):
    if not senha_confere(body.senha):
        raise HTTPException(401, "Senha incorreta")
    return TokenOut(token=gerar_token())


# ---------- Editais ----------
def _filtro_relevante():
    return or_(
        Edital.ia_relevante.is_(True),
        (Edital.ia_processado.is_(False)) & (Edital.keyword_score >= 4),
    )


@app.get("/api/editais", response_model=Pagina, dependencies=[Depends(exigir_login)])
def listar_editais(
    filtro: str = Query("relevantes", pattern="^(relevantes|todos|favoritos)$"),
    status: str | None = None,
    uf: str | None = None,
    q: str | None = None,
    abertos: bool = False,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Edital)
    if filtro == "relevantes":
        query = query.filter(_filtro_relevante())
    elif filtro == "favoritos":
        query = query.filter(Edital.favorito.is_(True))
    if status:
        query = query.filter(Edital.status.in_(status.split(",")))
    elif filtro != "favoritos":
        query = query.filter(Edital.status != "descartado")
    if uf:
        query = query.filter(Edital.uf == uf.upper())
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(Edital.objeto.ilike(termo), Edital.orgao.ilike(termo), Edital.municipio.ilike(termo)))
    if abertos:
        query = query.filter(or_(Edital.data_encerramento.is_(None), Edital.data_encerramento > datetime.now(timezone.utc)))

    total = query.count()
    itens = (
        query.order_by(Edital.data_publicacao.desc().nullslast(), Edital.ia_score.desc().nullslast())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    return Pagina(itens=itens, total=total, pagina=pagina, por_pagina=por_pagina)


@app.get("/api/editais/{edital_id}", response_model=EditalDetalhe, dependencies=[Depends(exigir_login)])
def obter_edital(edital_id: int, db: Session = Depends(get_db)):
    e = db.get(Edital, edital_id)
    if not e:
        raise HTTPException(404, "Edital não encontrado")
    return e


@app.patch("/api/editais/{edital_id}", response_model=EditalDetalhe, dependencies=[Depends(exigir_login)])
def atualizar_edital(edital_id: int, body: EditalUpdate, db: Session = Depends(get_db)):
    e = db.get(Edital, edital_id)
    if not e:
        raise HTTPException(404, "Edital não encontrado")
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(e, campo, valor)
    db.commit()
    db.refresh(e)
    return e


@app.get("/api/resumo", response_model=Resumo, dependencies=[Depends(exigir_login)])
def resumo(db: Session = Depends(get_db)):
    agora = datetime.now(timezone.utc)
    inicio_dia = agora - timedelta(hours=24)
    por_status = dict(db.query(Edital.status, func.count()).group_by(Edital.status).all())
    ultima = db.query(func.max(ExecucaoColeta.finalizado_em)).scalar()
    return Resumo(
        novos_hoje=db.query(Edital).filter(Edital.criado_em >= inicio_dia).filter(_filtro_relevante()).count(),
        relevantes_abertos=db.query(Edital)
        .filter(_filtro_relevante())
        .filter(Edital.status != "descartado")
        .filter(or_(Edital.data_encerramento.is_(None), Edital.data_encerramento > agora))
        .count(),
        por_status={s: por_status.get(s, 0) for s in ("novo", "analisando", "participando", "descartado")},
        encerrando_em_48h=db.query(Edital)
        .filter(Edital.status.in_(("analisando", "participando")))
        .filter(Edital.data_encerramento > agora, Edital.data_encerramento <= agora + timedelta(hours=48))
        .count(),
        ultima_coleta=ultima,
    )


# ---------- Preferências ----------
@app.get("/api/config", dependencies=[Depends(exigir_login)])
def obter_config(db: Session = Depends(get_db)):
    return {"preferencias": preferencias.carregar(db), "modalidades": preferencias.MODALIDADES}


@app.put("/api/config", dependencies=[Depends(exigir_login)])
def salvar_config(body: dict, db: Session = Depends(get_db)):
    return {"preferencias": preferencias.salvar(db, body), "modalidades": preferencias.MODALIDADES}


# ---------- Push ----------
@app.get("/api/push/chave-publica")
def chave_publica():
    if not push_configurado():
        raise HTTPException(503, "VAPID não configurado no servidor")
    return {"chave": settings.vapid_public_key}


@app.post("/api/push/inscrever", dependencies=[Depends(exigir_login)])
def inscrever(body: PushSubscriptionIn, db: Session = Depends(get_db)):
    sub = db.query(PushSubscription).filter_by(endpoint=body.endpoint).first()
    if sub:
        sub.p256dh, sub.auth = body.keys.p256dh, body.keys.auth
    else:
        db.add(PushSubscription(endpoint=body.endpoint, p256dh=body.keys.p256dh, auth=body.keys.auth))
    db.commit()
    return {"ok": True}


@app.post("/api/push/cancelar", dependencies=[Depends(exigir_login)])
def cancelar(body: PushSubscriptionIn, db: Session = Depends(get_db)):
    db.query(PushSubscription).filter_by(endpoint=body.endpoint).delete()
    db.commit()
    return {"ok": True}


@app.post("/api/push/teste", dependencies=[Depends(exigir_login)])
def push_teste(db: Session = Depends(get_db)):
    n = enviar_para_todos(db, "Licita TI", "Notificações funcionando ✅", url="/", tag="teste")
    return {"entregues": n}


# ---------- Coleta ----------
def _rodar_coleta(data_ref: date | None, dias: int) -> None:
    db = SessionLocal()
    try:
        executar_coleta(db, data_ref=data_ref, dias=dias)
    finally:
        db.close()


@app.post("/api/coleta", dependencies=[Depends(exigir_login)])
def disparar_coleta(body: ColetaIn, bg: BackgroundTasks):
    data_ref = date.fromisoformat(body.data) if body.data else None
    bg.add_task(_rodar_coleta, data_ref, max(1, min(body.dias, 15)))
    return {"ok": True, "mensagem": "Coleta iniciada; os editais aparecem em alguns minutos."}


@app.get("/api/coleta/historico", dependencies=[Depends(exigir_login)])
def historico(db: Session = Depends(get_db)):
    rows = db.query(ExecucaoColeta).order_by(ExecucaoColeta.id.desc()).limit(20).all()
    return [
        {
            "id": r.id, "iniciado_em": r.iniciado_em, "finalizado_em": r.finalizado_em,
            "data_referencia": r.data_referencia, "recebidos": r.recebidos, "novos": r.novos,
            "relevantes": r.relevantes, "notificados": r.notificados, "erro": r.erro,
        }
        for r in rows
    ]
