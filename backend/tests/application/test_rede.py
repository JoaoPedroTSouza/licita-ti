from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from radar.application.rede import Rede
from radar.domain.erros import ErroDeDominio, NaoEncontrado
from tests.fakes import RelogioFixo, UnidadeDeTrabalhoEmMemoria

TZ = ZoneInfo("America/Sao_Paulo")


def cenario(agora=datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)):
    uow = UnidadeDeTrabalhoEmMemoria()
    return uow, Rede(uow, RelogioFixo(agora), TZ)


def test_rede_lista_atrasados_primeiro():
    _, rede = cenario()
    rede.criar("Zé")
    rede.criar("Bia", frequencia_dias=30)  # nunca contatada: atrasada
    rede.criar("Ana")
    c = rede.criar("Caio", frequencia_dias=30)
    rede.registrar_contato(c.id)  # em dia
    assert [x.nome for x in rede.listar()] == ["Bia", "Ana", "Caio", "Zé"]


def test_registrar_contato_usa_dia_de_brasilia():
    _, rede = cenario(datetime(2026, 10, 24, 1, 0, tzinfo=timezone.utc))
    c = rede.criar("Ana")
    assert rede.registrar_contato(c.id).ultimo_contato == date(2026, 10, 23)


def test_editar_so_aceita_campos_editaveis():
    _, rede = cenario()
    c = rede.criar("Ana")
    rede.editar(c.id, nome="Ana B", organizacao="ONU", frequencia_dias=15)
    assert (c.nome, c.organizacao, c.frequencia_dias) == ("Ana B", "ONU", 15)
    with pytest.raises(ErroDeDominio):
        rede.editar(c.id, ultimo_contato=date(2026, 1, 1))
    with pytest.raises(ErroDeDominio):
        rede.editar(c.id, nome="  ")


def test_contato_inexistente_levanta_nao_encontrado():
    _, rede = cenario()
    with pytest.raises(NaoEncontrado):
        rede.editar(99, nome="x")
    with pytest.raises(NaoEncontrado):
        rede.registrar_contato(99)


def test_criar_com_nome_em_branco_levanta_erro_de_dominio():
    uow, rede = cenario()
    with pytest.raises(ErroDeDominio):
        rede.criar("   ")
    assert uow.direto.contatos.listar() == []
