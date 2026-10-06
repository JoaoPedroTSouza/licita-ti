from datetime import date

from fastapi.testclient import TestClient

from app.coletor.executar import executar_coleta
from app.db import SessionLocal, init_db
from app.main import app
from app.models import Edital
from tests.test_fluxo import FakeIA, FakePNCP, item_pncp


def _login(c: TestClient) -> dict:
    token = c.post("/api/auth/login", json={"senha": "segredo"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_ideias_crud():
    init_db()
    c = TestClient(app)
    h = _login(c)
    assert c.get("/api/ideias").status_code == 401

    r = c.post("/api/ideias", headers=h, json={
        "titulo": "  Micro-SaaS de orçamento para prestadores ",
        "tipo": "produto",
        "prioridade": "alta",
        "tags": ["SaaS", "saas", "  nicho  ", ""],
        "potencial_mensal": 3000,
    })
    assert r.status_code == 201, r.text
    ideia = r.json()
    assert ideia["titulo"] == "Micro-SaaS de orçamento para prestadores"
    assert ideia["tags"] == ["saas", "nicho"] and ideia["status"] == "nova"

    assert c.post("/api/ideias", headers=h, json={"titulo": ""}).status_code == 422
    assert c.post("/api/ideias", headers=h, json={"titulo": "x", "status": "voando"}).status_code == 422
    assert c.post("/api/ideias", headers=h, json={"titulo": "x", "edital_id": 99999}).status_code == 422

    r = c.patch(f"/api/ideias/{ideia['id']}", headers=h, json={"status": "validando", "potencial_mensal": None})
    assert r.json()["status"] == "validando" and r.json()["potencial_mensal"] is None

    assert len(c.get("/api/ideias?status=validando", headers=h).json()) == 1
    assert len(c.get("/api/ideias?q=orçamento", headers=h).json()) == 1

    assert c.delete(f"/api/ideias/{ideia['id']}", headers=h).status_code == 204
    assert c.get(f"/api/ideias/{ideia['id']}", headers=h).status_code == 404


def test_painel_e_ideia_vinculada():
    init_db()
    db = SessionLocal()
    itens = [item_pncp(101, "Desenvolvimento de sistema web para a ouvidoria municipal", uf="SP")]
    executar_coleta(db, data_ref=date(2026, 10, 5), client=FakePNCP(itens), classificador=FakeIA())
    edital = db.query(Edital).filter_by(sequencial=101).one()
    db.close()

    c = TestClient(app)
    h = _login(c)
    r = c.post("/api/ideias", headers=h, json={"titulo": "Proposta ouvidoria", "tipo": "proposta", "edital_id": edital.id})
    assert r.status_code == 201
    assert r.json()["edital"]["id"] == edital.id
    assert len(c.get(f"/api/ideias?edital_id={edital.id}", headers=h).json()) == 1

    p = c.get("/api/painel", headers=h).json()
    assert p["kpis"]["relevantes_abertos"] >= 1
    assert p["kpis"]["ideias_ativas"] >= 1
    assert len(p["serie"]) == 14
    assert any(u["uf"] == "SP" for u in p["por_uf"])
    assert set(p["funil"]) == {"novo", "analisando", "participando", "descartado"}
    assert p["coletas"] and "erro" in p["coletas"][0]
