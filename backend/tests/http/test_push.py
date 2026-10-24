import json


def test_chave_publica(cliente_logado):
    r = cliente_logado.get("/api/push/chave-publica")
    assert r.status_code == 200 and r.json() == {"chave": ""}


def test_push_inscrever_e_testar(cliente_logado_push, envios):
    c = cliente_logado_push
    corpo = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "P", "auth": "A"}}
    assert c.post("/api/push/inscrever", json=corpo).status_code == 204
    assert c.post("/api/push/inscrever", json=corpo).status_code == 204  # idempotente
    r = c.post("/api/push/teste")
    assert r.status_code == 200 and r.json() == {"entregues": 1}
    assert len(envios) == 1
    assert envios[0]["subscription_info"]["endpoint"] == "https://push.example/abc"
    assert json.loads(envios[0]["data"]) == {
        "title": "Radar", "body": "Notificação de teste", "url": "http://localhost:3000/ajustes",
    }


def test_push_teste_sem_inscricao(cliente_logado):
    assert cliente_logado.post("/api/push/teste").json() == {"entregues": 0}
