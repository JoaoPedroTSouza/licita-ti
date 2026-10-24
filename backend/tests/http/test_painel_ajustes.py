from datetime import UTC, datetime

from radar.application.portas import ExecucaoFonte
from tests.http.conftest import semear


def test_painel_formato(cliente_logado):
    semear(cliente_logado.container, "A", 90)
    corpo = cliente_logado.get("/api/painel").json()
    assert corpo["dia"] == "2026-10-23"
    assert corpo["para_fazer"] == []
    assert corpo["funil"] == {
        "contagem": {"analisando": 0, "proposta_enviada": 0, "negociacao": 0,
                     "fechado": 0, "perdido": 0},
        "valor_aberto_brl": "0", "sem_conversao": 0,
    }
    assert [o["titulo"] for o in corpo["melhores_novas"]] == ["A"]


def test_painel_conta_processo_e_tira_da_lista_de_novas(cliente_logado):
    oid = semear(cliente_logado.container, "A", 90)
    cliente_logado.post(f"/api/oportunidades/{oid}/interessa")
    corpo = cliente_logado.get("/api/painel").json()
    assert corpo["funil"]["contagem"]["analisando"] == 1
    assert corpo["melhores_novas"] == []


def test_painel_lista_prazo_proximo_para_fazer(cliente_logado):
    from datetime import timedelta
    from tests.http.conftest import AGORA
    oid = semear(cliente_logado.container, "A", 90, prazo=AGORA + timedelta(days=2))
    pid = cliente_logado.post(f"/api/oportunidades/{oid}/interessa").json()["id"]
    item = cliente_logado.get("/api/painel").json()["para_fazer"][0]
    assert item == {"tipo": "prazo", "titulo": "Prazo: A", "quando": "2026-10-25T12:00:00Z",
                    "ref_id": pid, "processo_id": pid}


def test_perfil_padrao_e_atualizacao(cliente_logado):
    assert cliente_logado.get("/api/perfil").json() == {
        "texto": "", "faixa_min_brl": None, "faixa_max_brl": None}
    r = cliente_logado.put("/api/perfil", json={
        "texto": "Dev Python", "faixa_min_brl": "5000.50", "faixa_max_brl": 9000})
    assert r.status_code == 200
    esperado = {"texto": "Dev Python", "faixa_min_brl": "5000.50", "faixa_max_brl": "9000"}
    assert r.json() == esperado
    assert cliente_logado.get("/api/perfil").json() == esperado


def test_ajustes_padrao_e_atualizacao(cliente_logado):
    assert cliente_logado.get("/api/ajustes").json() == {
        "limiar_alerta": 85, "horario_resumo": "07:30", "avisos_prazo_dias": [3, 1]}
    novo = {"limiar_alerta": 70, "horario_resumo": "08:15", "avisos_prazo_dias": [7, 2]}
    assert cliente_logado.put("/api/ajustes", json=novo).json() == novo
    assert cliente_logado.get("/api/ajustes").json() == novo


def test_ajustes_limiar_invalido_422(cliente_logado):
    r = cliente_logado.put("/api/ajustes", json={
        "limiar_alerta": 101, "horario_resumo": "07:30", "avisos_prazo_dias": [3]})
    assert r.status_code == 422
    assert cliente_logado.get("/api/ajustes").json()["limiar_alerta"] == 85


def test_ajustes_horario_invalido_422(cliente_logado):
    r = cliente_logado.put("/api/ajustes", json={
        "limiar_alerta": 80, "horario_resumo": "25:99", "avisos_prazo_dias": [3]})
    assert r.status_code == 422


def test_status_com_ia(cliente_logado):
    corpo = cliente_logado.get("/api/status").json()
    assert corpo["ia_configurada"] is True
    assert corpo["push_configurado"] is True
    assert corpo["fontes"] == []


def test_status_sem_ia(cliente_logado_sem_classificador):
    assert cliente_logado_sem_classificador.get("/api/status").json()["ia_configurada"] is False


def test_status_lista_ultima_execucao_por_fonte(cliente_logado):
    t0 = datetime(2026, 10, 23, 7, 0, tzinfo=UTC)
    with cliente_logado.container.uow() as uow:
        uow.execucoes.registrar(ExecucaoFonte("ungm", t0, t0, 10, 3, None))
        uow.execucoes.registrar(ExecucaoFonte("opas", t0, t0, 0, 0, "falhou"))
        uow.commit()
    fontes = {f["fonte"]: f for f in cliente_logado.get("/api/status").json()["fontes"]}
    assert fontes["ungm"] == {"fonte": "ungm", "finalizada_em": "2026-10-23T07:00:00Z",
                              "recebidas": 10, "novas": 3, "erro": None}
    assert fontes["opas"]["erro"] == "falhou"
