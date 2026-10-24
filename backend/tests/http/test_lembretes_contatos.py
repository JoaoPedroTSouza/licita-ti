def test_lembrete_concluir_some_dos_pendentes(cliente_logado):
    a = cliente_logado.post("/api/lembretes", json={
        "texto": "B", "vence_em": "2026-11-02T10:00:00Z"}).json()
    b = cliente_logado.post("/api/lembretes", json={
        "texto": "A", "vence_em": "2026-10-30T10:00:00Z"}).json()
    r = cliente_logado.get("/api/lembretes?pendentes=true")
    assert [x["texto"] for x in r.json()] == ["A", "B"]
    r = cliente_logado.post(f"/api/lembretes/{b['id']}/concluir")
    assert r.status_code == 200 and r.json()["concluido"] is True
    assert [x["id"] for x in cliente_logado.get("/api/lembretes?pendentes=true").json()] == [a["id"]]


def test_lembrete_data_sem_fuso_422(cliente_logado):
    r = cliente_logado.post("/api/lembretes", json={
        "texto": "x", "vence_em": "2026-10-30T10:00:00"})
    assert r.status_code == 422


def test_lembrete_processo_inexistente_404(cliente_logado):
    r = cliente_logado.post("/api/lembretes", json={
        "texto": "x", "vence_em": "2026-10-30T10:00:00Z", "processo_id": 99})
    assert r.status_code == 404


def test_remover_lembrete(cliente_logado):
    a = cliente_logado.post("/api/lembretes", json={
        "texto": "x", "vence_em": "2026-10-30T10:00:00Z"}).json()
    assert cliente_logado.delete(f"/api/lembretes/{a['id']}").status_code == 204
    assert cliente_logado.get("/api/lembretes").json() == []
    assert cliente_logado.delete(f"/api/lembretes/{a['id']}").status_code == 404


def test_contato_registrar_contato_zera_atraso(cliente_logado):
    c = cliente_logado.post("/api/contatos", json={"nome": "Ana", "frequencia_dias": 30}).json()
    assert c["atrasado"] is True and c["ultimo_contato"] is None
    r = cliente_logado.post(f"/api/contatos/{c['id']}/registrar-contato")
    assert r.json()["atrasado"] is False and r.json()["ultimo_contato"] == "2026-10-23"


def test_contato_editar_so_campos_enviados(cliente_logado):
    c = cliente_logado.post("/api/contatos", json={
        "nome": "Ana", "organizacao": "ONU"}).json()
    r = cliente_logado.patch(f"/api/contatos/{c['id']}", json={"nome": "Ana Maria"})
    assert r.json()["nome"] == "Ana Maria" and r.json()["organizacao"] == "ONU"
    assert cliente_logado.patch("/api/contatos/99", json={"nome": "x"}).status_code == 404


def test_contato_nome_vazio_422(cliente_logado):
    assert cliente_logado.post("/api/contatos", json={"nome": " "}).status_code == 422


def test_contatos_atrasados_primeiro(cliente_logado):
    cliente_logado.post("/api/contatos", json={"nome": "Zé"})
    cliente_logado.post("/api/contatos", json={"nome": "Bia", "frequencia_dias": 7})
    assert [c["nome"] for c in cliente_logado.get("/api/contatos").json()] == ["Bia", "Zé"]
