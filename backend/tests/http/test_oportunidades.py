from datetime import timedelta
from decimal import Decimal

from radar.domain.dinheiro import Dinheiro
from radar.domain.oportunidade import StatusOportunidade
from tests.http.conftest import AGORA, SENHA, semear


def test_health_sem_token(cliente):
    assert cliente.get("/api/health").json() == {"ok": True}


def test_sem_token_401(cliente):
    assert cliente.get("/api/oportunidades").status_code == 401
    assert cliente.get("/api/painel").status_code == 401


def test_token_invalido_401(cliente):
    r = cliente.get("/api/oportunidades", headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401


def test_login_errado_401(cliente):
    assert cliente.post("/api/auth/login", json={"senha": "errada"}).status_code == 401


def test_login_certo_devolve_token(cliente):
    r = cliente.post("/api/auth/login", json={"senha": SENHA})
    assert r.status_code == 200 and r.json()["token"]


def test_lista_so_novas_ordenadas_por_nota(cliente_logado):
    c = cliente_logado.container
    semear(c, "B", 60)
    semear(c, "A", 90)
    semear(c, "Pendente", 99, status=StatusOportunidade.PENDENTE)
    semear(c, "Descartada", 99, status=StatusOportunidade.DESCARTADA)
    r = cliente_logado.get("/api/oportunidades")
    assert r.status_code == 200
    assert [o["titulo"] for o in r.json()] == ["A", "B"]


def test_lista_filtra_por_status(cliente_logado):
    c = cliente_logado.container
    semear(c, "Nova", 50)
    semear(c, "Desc", 50, status=StatusOportunidade.DESCARTADA)
    r = cliente_logado.get("/api/oportunidades", params={"status": "descartada"})
    assert [o["titulo"] for o in r.json()] == ["Desc"]
    assert cliente_logado.get("/api/oportunidades", params={"status": "xyz"}).status_code == 422


def test_formato_do_dto_com_valor_e_conversao(cliente_logado):
    c = cliente_logado.container
    with c.uow() as uow:
        uow.cotacoes.salvar("USD", AGORA.date(), Decimal("5.50"))
        uow.commit()
    semear(c, "Com valor", 80, valor=Dinheiro(Decimal("1000.00"), "USD"),
           prazo=AGORA + timedelta(days=5))
    semear(c, "Sem taxa", 70, valor=Dinheiro(Decimal("10"), "XYZ"))
    por_titulo = {o["titulo"]: o for o in cliente_logado.get("/api/oportunidades").json()}
    o = por_titulo["Com valor"]
    assert o["valor"] == {"valor": "1000.00", "moeda": "USD"}
    assert o["valor_brl"] == "5500.00"
    assert o["prazo"] == "2026-10-28T12:00:00Z"
    assert o["nota"] == 80 and o["resumo"] == "resumo Com valor"
    assert o["motivo"] == "encaixa no perfil"
    assert o["fonte"] == "teste" and o["status"] == "nova" and o["processo_id"] is None
    assert o["pessoa_fisica"] is False
    assert por_titulo["Sem taxa"]["valor_brl"] is None
    assert por_titulo["Sem taxa"]["valor"] == {"valor": "10", "moeda": "XYZ"}


def test_pessoa_fisica_vem_marcada(cliente_logado):
    semear(cliente_logado.container, "PF", 80, pessoa_fisica=True)
    assert cliente_logado.get("/api/oportunidades").json()[0]["pessoa_fisica"] is True


def test_detalhe_traz_texto_e_trecho(cliente_logado):
    oid = semear(cliente_logado.container, "X", 80)
    r = cliente_logado.get(f"/api/oportunidades/{oid}")
    assert r.status_code == 200
    assert r.json()["texto"] == "texto de X"
    assert r.json()["trecho_modalidade"] == "trabalho remoto"
    assert r.json()["id"] == oid


def test_interessa_devolve_processo_e_some_da_entrada(cliente_logado):
    oid = semear(cliente_logado.container, "X", 80, valor=Dinheiro(Decimal("100"), "BRL"))
    r = cliente_logado.post(f"/api/oportunidades/{oid}/interessa")
    assert r.status_code == 200
    p = r.json()
    assert p["titulo"] == "X" and p["etapa"] == "analisando" and p["oportunidade_id"] == oid
    assert p["valor"] == {"valor": "100", "moeda": "BRL"} and p["valor_brl"] == "100"
    assert p["historico"][0]["de"] is None and p["historico"][0]["para"] == "analisando"
    assert p["notas"] == [] and p["arquivos"] == []
    assert p["contato_ids"] == [] and p["lembretes"] == []
    assert cliente_logado.get("/api/oportunidades").json() == []
    assert cliente_logado.get(f"/api/oportunidades/{oid}").json()["processo_id"] == p["id"]


def test_descartar_devolve_204_e_guarda_motivo(cliente_logado):
    oid = semear(cliente_logado.container, "X", 80)
    r = cliente_logado.post(f"/api/oportunidades/{oid}/descartar", json={"motivo": "  caro  "})
    assert r.status_code == 204 and r.content == b""
    assert cliente_logado.get("/api/oportunidades").json() == []
    with cliente_logado.container.uow() as uow:
        assert uow.oportunidades.obter(oid).motivo_usuario == "caro"


def test_descartar_sem_corpo(cliente_logado):
    oid = semear(cliente_logado.container, "X", 80)
    assert cliente_logado.post(f"/api/oportunidades/{oid}/descartar").status_code == 204


def test_triar_duas_vezes_422(cliente_logado):
    oid = semear(cliente_logado.container, "X", 80)
    assert cliente_logado.post(f"/api/oportunidades/{oid}/interessa").status_code == 200
    r = cliente_logado.post(f"/api/oportunidades/{oid}/interessa")
    assert r.status_code == 422
    assert r.json() == {"detail": "Só oportunidades novas podem ser triadas."}


def test_oportunidade_inexistente_404(cliente_logado):
    assert cliente_logado.get("/api/oportunidades/999").status_code == 404
    assert cliente_logado.post("/api/oportunidades/999/interessa").status_code == 404
    assert cliente_logado.post("/api/oportunidades/999/descartar").status_code == 404
