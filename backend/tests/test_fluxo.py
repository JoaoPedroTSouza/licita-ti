from datetime import date

from fastapi.testclient import TestClient

from app.coletor.executar import executar_coleta
from app.coletor.filtro import pontuar
from app.coletor.pncp import normalizar
from app.db import SessionLocal, init_db
from app.main import app
from app.models import Edital
from app.preferencias import PADRAO


def item_pncp(seq: int, objeto: str, uf: str = "MG", valor: float = 80000.0) -> dict:
    """Formato real devolvido por GET /v1/contratacoes/publicacao."""
    return {
        "numeroControlePNCP": f"18715000000100-1-{seq:06d}/2026",
        "anoCompra": 2026,
        "sequencialCompra": seq,
        "numeroCompra": f"{seq}/2026",
        "processo": f"PROC-{seq}",
        "objetoCompra": objeto,
        "informacaoComplementar": "",
        "orgaoEntidade": {"cnpj": "18715000000100", "razaoSocial": "MUNICIPIO DE EXEMPLO"},
        "unidadeOrgao": {"ufSigla": uf, "municipioNome": "Exemplo", "nomeUnidade": "Secretaria de Administração"},
        "modalidadeId": 6,
        "modalidadeNome": "Pregão - Eletrônico",
        "modoDisputaNome": "Aberto",
        "situacaoCompraNome": "Divulgada no PNCP",
        "srp": False,
        "valorTotalEstimado": valor,
        "dataPublicacaoPncp": "2026-10-05T09:12:00",
        "dataAberturaProposta": "2026-10-06T08:00:00",
        "dataEncerramentoProposta": "2099-10-20T09:00:00",
        "linkSistemaOrigem": "https://cnetmobile.estaleiro.serpro.gov.br/exemplo",
    }


class FakePNCP:
    def __init__(self, itens):
        self.itens = itens

    def contratacoes_publicadas(self, inicio, fim, modalidade, uf=None):
        return iter(self.itens if modalidade == 6 else [])

    def close(self):
        pass


class FakeIA:
    ativo = True

    def classificar(self, edital, perfil):
        relevante = "aquisição" not in edital["objeto"].lower()
        return {
            "ia_processado": True,
            "ia_relevante": relevante,
            "ia_score": 85 if relevante else 10,
            "ia_categoria": "desenvolvimento web" if relevante else "não TI",
            "ia_resumo": "Resumo de teste.",
            "ia_motivo": "Motivo de teste.",
            "ia_exigencias": ["Atestado de capacidade técnica"],
        }


def test_filtro_acentos_e_limites():
    score, termos, excl = pontuar("Contratação de empresa para DESENVOLVIMENTO de SISTEMA web e Sítio Eletrônico", PADRAO)
    assert "desenvolvimento de sistema" in termos  # ignora caixa
    assert "sitio eletronico" in termos and score >= 2 and not excl

    _, termos, _ = pontuar("Aquisição de produtos de higiene (uso diário)", PADRAO)
    assert "ui" not in termos and "ux" not in termos  # sem falso positivo dentro de palavras

    _, _, excl = pontuar("Aquisição de computadores e sistema operacional", PADRAO)
    assert excl


def test_normalizar():
    d = normalizar(item_pncp(7, "Desenvolvimento de software"))
    assert d["uf"] == "MG" and d["sequencial"] == 7
    assert d["link_pncp"] == "https://pncp.gov.br/app/editais/18715000000100/2026/7"
    assert d["data_publicacao"].tzinfo is not None


def test_coleta_completa_e_api():
    init_db()
    itens = [
        item_pncp(1, "Contratação de empresa para desenvolvimento de sistema web e aplicativo para a Secretaria"),
        item_pncp(2, "Fábrica de software com pagamento por ponto de função"),
        item_pncp(3, "Aquisição de gêneros alimentícios para merenda escolar"),  # fora
        item_pncp(4, "Aquisição de sistema de software de gestão e desenvolvimento de software"),  # IA reprova
    ]
    db = SessionLocal()
    ex = executar_coleta(db, data_ref=date(2026, 10, 5), client=FakePNCP(itens), classificador=FakeIA())
    assert ex.erro is None, ex.erro
    assert ex.recebidos == 4 and ex.novos == 3 and ex.relevantes == 2

    # Re-executar não duplica
    ex2 = executar_coleta(db, data_ref=date(2026, 10, 5), client=FakePNCP(itens), classificador=FakeIA())
    assert ex2.novos == 0 and db.query(Edital).count() == 3
    db.close()

    c = TestClient(app)
    assert c.get("/api/editais").status_code == 401
    assert c.post("/api/auth/login", json={"senha": "errada"}).status_code == 401
    token = c.post("/api/auth/login", json={"senha": "segredo"}).json()["token"]
    h = {"Authorization": f"Bearer {token}"}

    r = c.get("/api/editais", headers=h).json()
    assert r["total"] == 2
    eid = r["itens"][0]["id"]

    r = c.patch(f"/api/editais/{eid}", headers=h, json={"status": "analisando", "favorito": True, "notas": "ok"})
    assert r.status_code == 200 and r.json()["status"] == "analisando"
    assert c.get("/api/editais?filtro=favoritos", headers=h).json()["total"] == 1
    assert c.get("/api/editais?filtro=todos", headers=h).json()["total"] == 3
    assert c.get("/api/editais?q=ponto", headers=h).json()["total"] == 1

    resumo = c.get("/api/resumo", headers=h).json()
    assert resumo["por_status"]["analisando"] == 1

    cfg = c.put("/api/config", headers=h, json={"ufs": ["MG", "SP"], "invalida": 1}).json()
    assert cfg["preferencias"]["ufs"] == ["MG", "SP"] and "invalida" not in cfg["preferencias"]
