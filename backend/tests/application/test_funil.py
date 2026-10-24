from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from radar.application.funil import Funil
from radar.domain.contato import Contato
from radar.domain.dinheiro import Dinheiro
from radar.domain.erros import NaoEncontrado
from radar.domain.processo import Etapa
from tests.fakes import (
    ArmazenamentoArquivosEmMemoria, RelogioFixo, UnidadeDeTrabalhoEmMemoria,
)

AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def cenario():
    uow = UnidadeDeTrabalhoEmMemoria()
    armazenamento = ArmazenamentoArquivosEmMemoria()
    return uow, armazenamento, Funil(uow, RelogioFixo(AGORA), armazenamento)


def test_criar_manual_sem_oportunidade():
    uow, _, funil = cenario()
    p = funil.criar_manual("Indicação", "Acme", Dinheiro(Decimal("500"), "BRL"), None)
    assert p.id is not None and p.oportunidade_id is None
    assert p.etapa == Etapa.ANALISANDO
    assert uow.processos.obter(p.id) is p
    assert uow.commits == 1


def test_mudar_prazo_reinicia_avisos():
    _, _, funil = cenario()
    p = funil.criar_manual("X", None, None, AGORA + timedelta(days=5))
    p.avisos_prazo_enviados.add(3)
    funil.editar(p.id, titulo="Y")
    assert p.titulo == "Y" and p.avisos_prazo_enviados == {3}
    funil.editar(p.id, prazo=AGORA + timedelta(days=9))
    assert p.avisos_prazo_enviados == set()


def test_limpar_prazo_reinicia_avisos_e_omitidos_ficam():
    _, _, funil = cenario()
    p = funil.criar_manual("X", "Acme", Dinheiro(Decimal("5"), "BRL"), AGORA + timedelta(days=5))
    p.avisos_prazo_enviados.add(3)
    funil.editar(p.id, titulo="Y")
    assert p.prazo is not None and p.organizacao == "Acme" and p.valor is not None
    funil.editar(p.id, prazo=None, valor=None, organizacao=None)
    assert p.prazo is None and p.valor is None and p.organizacao is None
    assert p.avisos_prazo_enviados == set()


def test_mover_e_anotar():
    _, _, funil = cenario()
    p = funil.criar_manual("X", None, None, None)
    funil.mover(p.id, Etapa.NEGOCIACAO)
    funil.anotar(p.id, "ligar amanhã")
    assert p.etapa == Etapa.NEGOCIACAO
    assert [n.texto for n in p.notas] == ["ligar amanhã"]


def test_anexar_salva_no_armazenamento_e_reabre():
    _, armazenamento, funil = cenario()
    p = funil.criar_manual("X", None, None, None)
    a1 = funil.anexar(p.id, "edital.pdf", b"abc")
    a2 = funil.anexar(p.id, "termo.pdf", b"de")
    assert (a1.id, a2.id) == (1, 2)
    assert a1.tamanho == 3 and a1.enviado_em == AGORA
    assert armazenamento.arquivos[a1.chave] == b"abc"
    arquivo, conteudo = funil.abrir_arquivo(p.id, a2.id)
    assert arquivo.nome == "termo.pdf" and conteudo == b"de"
    with pytest.raises(NaoEncontrado):
        funil.abrir_arquivo(p.id, 99)


def test_vincular_contato_atualiza_os_dois_lados():
    uow, _, funil = cenario()
    p = funil.criar_manual("X", None, None, None)
    c = uow.contatos.adicionar(Contato(None, "Ana"))
    funil.vincular_contato(p.id, c.id)
    assert p.contato_ids == {c.id}
    assert c.processo_ids == {p.id}
    with pytest.raises(NaoEncontrado):
        funil.vincular_contato(p.id, 99)


def test_lembretes_criar_concluir_remover():
    uow, _, funil = cenario()
    p = funil.criar_manual("X", None, None, None)
    lem = funil.criar_lembrete("enviar proposta", AGORA, p.id)
    assert uow.lembretes.do_processo(p.id) == [lem]
    assert funil.concluir_lembrete(lem.id).concluido is True
    funil.remover_lembrete(lem.id)
    assert uow.lembretes.obter(lem.id) is None
    with pytest.raises(NaoEncontrado):
        funil.concluir_lembrete(lem.id)
    with pytest.raises(NaoEncontrado):
        funil.criar_lembrete("x", AGORA, 99)


def test_processo_inexistente_levanta_nao_encontrado():
    _, _, funil = cenario()
    with pytest.raises(NaoEncontrado):
        funil.mover(99, Etapa.FECHADO)
    with pytest.raises(NaoEncontrado):
        funil.editar(99, titulo="x")
    with pytest.raises(NaoEncontrado):
        funil.anotar(99, "x")
    with pytest.raises(NaoEncontrado):
        funil.anexar(99, "a", b"")
    with pytest.raises(NaoEncontrado):
        funil.abrir_arquivo(99, 1)
