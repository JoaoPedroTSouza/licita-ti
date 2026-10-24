def criar(c, **extra):
    r = c.post("/api/processos", json={"titulo": "Consultoria X", **extra})
    assert r.status_code == 201, r.text
    return r.json()


def enviar(c, pid, nome="a.txt", conteudo=b"ola"):
    return c.post(f"/api/processos/{pid}/arquivos", files={"arquivo": (nome, conteudo)})


def test_criar_manual_mover_e_ver_historico(cliente_logado):
    p = criar(cliente_logado, organizacao="ONU", valor={"valor": "1000.50", "moeda": "brl"})
    assert p["etapa"] == "analisando" and p["valor_brl"] == "1000.50"
    r = cliente_logado.post(f"/api/processos/{p['id']}/etapa", json={"etapa": "negociacao"})
    assert r.status_code == 200 and r.json()["etapa"] == "negociacao"
    d = cliente_logado.get(f"/api/processos/{p['id']}").json()
    assert d["historico"][-1]["de"] == "analisando" and d["historico"][-1]["para"] == "negociacao"
    lista = cliente_logado.get("/api/processos").json()
    assert lista[0]["titulo"] == "Consultoria X" and "notas" not in lista[0]


def test_etapa_invalida_422(cliente_logado):
    p = criar(cliente_logado)
    r = cliente_logado.post(f"/api/processos/{p['id']}/etapa", json={"etapa": "ganho"})
    assert r.status_code == 422


def test_processo_inexistente_404(cliente_logado):
    assert cliente_logado.get("/api/processos/999").status_code == 404


def test_editar_so_campos_enviados(cliente_logado):
    p = criar(cliente_logado, organizacao="ONU")
    r = cliente_logado.patch(f"/api/processos/{p['id']}", json={"titulo": "Novo"})
    assert r.json()["titulo"] == "Novo" and r.json()["organizacao"] == "ONU"


def test_editar_null_limpa_campos(cliente_logado):
    p = criar(cliente_logado, organizacao="ONU", prazo="2030-01-01T12:00:00Z")
    pid = p["id"]
    r = cliente_logado.patch(f"/api/processos/{pid}", json={"prazo": None})
    assert r.status_code == 200
    assert cliente_logado.get(f"/api/processos/{pid}").json()["prazo"] is None
    r = cliente_logado.patch(f"/api/processos/{pid}", json={"organizacao": None})
    d = cliente_logado.get(f"/api/processos/{pid}").json()
    assert r.status_code == 200 and d["organizacao"] is None and d["titulo"] == "Consultoria X"


def test_nota(cliente_logado):
    p = criar(cliente_logado)
    r = cliente_logado.post(f"/api/processos/{p['id']}/notas", json={"texto": "ligar amanhã"})
    assert r.json()["notas"][0]["texto"] == "ligar amanhã"


def test_upload_e_download(cliente_logado):
    p = criar(cliente_logado)
    r = enviar(cliente_logado, p["id"], "proposta.pdf", b"%PDF-conteudo")
    assert r.status_code == 201
    a = r.json()
    assert a["nome"] == "proposta.pdf" and a["tamanho"] == 13
    d = cliente_logado.get(f"/api/processos/{p['id']}/arquivos/{a['id']}")
    assert d.status_code == 200 and d.content == b"%PDF-conteudo"
    assert 'attachment; filename="proposta.pdf"' in d.headers["content-disposition"]
    assert d.headers["content-type"] == "application/pdf"
    assert cliente_logado.get(f"/api/processos/{p['id']}").json()["arquivos"][0]["id"] == a["id"]


def test_upload_nome_com_caminho_e_sanitizado(cliente_logado):
    p = criar(cliente_logado)
    r = enviar(cliente_logado, p["id"], nome="../../etc/passwd")
    assert r.json()["nome"] == "passwd"
    r = enviar(cliente_logado, p["id"], nome="rel<at>ório?.txt")
    assert r.json()["nome"] == "rel_at_ório_.txt"
    d = cliente_logado.get(f"/api/processos/{p['id']}/arquivos/{r.json()['id']}")
    assert "filename*=UTF-8''" in d.headers["content-disposition"]


def test_upload_maior_que_limite_413(cliente_logado_limite_1mb):
    c = cliente_logado_limite_1mb
    p = criar(c)
    r = enviar(c, p["id"], conteudo=b"x" * (1024 * 1024 + 1))
    assert r.status_code == 413 and r.json() == {"detail": "Arquivo maior que 1 MB"}
    assert enviar(c, p["id"], conteudo=b"x" * (1024 * 1024)).status_code == 201


def test_vincular_contato_aparece_nos_dois_lados(cliente_logado):
    p = criar(cliente_logado)
    ct = cliente_logado.post("/api/contatos", json={"nome": "Ana"}).json()
    r = cliente_logado.post(f"/api/processos/{p['id']}/contatos/{ct['id']}")
    assert r.status_code == 200 and r.json()["contato_ids"] == [ct["id"]]
    contatos = cliente_logado.get("/api/contatos").json()
    assert contatos[0]["processo_ids"] == [p["id"]]


def test_processo_traz_lembretes(cliente_logado):
    p = criar(cliente_logado)
    cliente_logado.post("/api/lembretes", json={
        "texto": "enviar", "vence_em": "2026-10-25T10:00:00Z", "processo_id": p["id"]})
    d = cliente_logado.get(f"/api/processos/{p['id']}").json()
    assert d["lembretes"][0]["texto"] == "enviar"


def test_rotas_exigem_login(cliente):
    assert cliente.get("/api/processos").status_code == 401
    assert cliente.get("/api/lembretes").status_code == 401
    assert cliente.get("/api/contatos").status_code == 401
    assert cliente.get("/api/push/chave-publica").status_code == 401
