from tests.http.conftest import montar_container


def test_fabricas_devolvem_uow_e_casos_de_uso_novos_a_cada_chamada(tmp_path):
    c = montar_container(tmp_path)
    assert c.uow() is not c.uow()
    assert c.triar() is not c.triar()
    assert c.painel() is not c.painel()
    assert c.triar()._uow is not c.triar()._uow
    assert c.coletar()._uow is not c.coletar()._uow
    assert c.funil()._uow is not c.funil()._uow
    assert c.rede()._uow is not c.rede()._uow
