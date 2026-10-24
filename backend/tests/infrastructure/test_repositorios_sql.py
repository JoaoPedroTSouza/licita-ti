"""Mesma bateria de comportamento contra os fakes em memória e contra o SQL."""
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from radar.application.portas import ExecucaoFonte
from radar.domain.contato import Contato
from radar.domain.dinheiro import Dinheiro
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import (
    Classificacao, Modalidade, MotivoDescarteAuto, Oportunidade, OportunidadeBruta,
    StatusOportunidade, TipoContratacao,
)
from radar.domain.perfil import Ajustes, Perfil
from radar.domain.processo import Arquivo, Etapa, Processo
from radar.infrastructure.db.repositorios import (
    UnidadeDeTrabalhoSql, criar_engine, criar_tabelas,
)
from tests.fakes import UnidadeDeTrabalhoEmMemoria

AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


@pytest.fixture(params=["memoria", "sql"])
def uow(request):
    if request.param == "memoria":
        return UnidadeDeTrabalhoEmMemoria()
    engine = criar_engine("sqlite+pysqlite:///:memory:")
    criar_tabelas(engine)
    return UnidadeDeTrabalhoSql(sessionmaker(engine, expire_on_commit=False))


def _bruta(titulo="Consultoria de dados", prazo=None, valor=None, org="Banco Mundial", **kw):
    return OportunidadeBruta(
        fonte="fonte", id_externo=titulo, titulo=titulo, organizacao=org,
        link="https://exemplo.org/1", texto="texto", prazo=prazo, valor=valor, **kw)


def _classificacao(nota=80, **kw):
    return Classificacao(
        relevante=True, nota=nota, resumo="resumo", modalidade=Modalidade.REMOTO_TOTAL,
        trecho_modalidade="100% remoto", idioma="pt", tipo_contratacao=TipoContratacao.EMPRESA,
        motivo="motivo", **kw)


def _op(titulo, status=StatusOportunidade.NOVA, nota=None, prazo=None, coletada_em=AGORA, **kw):
    return Oportunidade(
        None, _bruta(titulo, prazo=prazo), coletada_em, status,
        _classificacao(nota) if nota is not None else None, **kw)


def test_oportunidade_ida_e_volta_preserva_classificacao_e_dinheiro(uow):
    prazo = datetime(2026, 11, 30, 15, 0, tzinfo=UTC)
    op = Oportunidade(
        None,
        _bruta(prazo=prazo, valor=Dinheiro(Decimal("1234.50"), "usd"), pais="BR",
               publicada_em=AGORA, idioma="en"),
        AGORA, StatusOportunidade.INTERESSA,
        _classificacao(91, prazo=prazo + timedelta(days=1), valor=Dinheiro(Decimal("99.99"), "EUR")),
        MotivoDescarteAuto.IDIOMA, "porque sim", 7)
    with uow:
        id_ = uow.oportunidades.adicionar(op).id
        uow.commit()
    with uow:
        lida = uow.oportunidades.obter(id_)
        assert lida == op
        assert lida.bruta.valor == Dinheiro(Decimal("1234.50"), "USD")
        assert lida.classificacao.valor.valor == Decimal("99.99")
        assert lida.classificacao.prazo.tzinfo is not None
        assert lida.bruta.prazo == prazo
        assert uow.oportunidades.obter(9999) is None


def test_oportunidade_sem_classificacao_nem_valor(uow):
    with uow:
        id_ = uow.oportunidades.adicionar(_op("Simples")).id
        uow.commit()
    with uow:
        lida = uow.oportunidades.obter(id_)
        assert lida.classificacao is None and lida.bruta.valor is None and lida.bruta.prazo is None


def test_salvar_atualiza_status_e_motivo(uow):
    with uow:
        op = uow.oportunidades.adicionar(_op("Mudar", StatusOportunidade.PENDENTE))
        uow.commit()
    with uow:
        op = uow.oportunidades.obter(op.id)
        op.status = StatusOportunidade.DESCARTADA
        op.motivo_usuario = "baixo valor"
        uow.oportunidades.salvar(op)
        uow.commit()
    with uow:
        lida = uow.oportunidades.obter(op.id)
        assert lida.status == StatusOportunidade.DESCARTADA and lida.motivo_usuario == "baixo valor"


def test_existe_chave(uow):
    op = _op("Chave única")
    with uow:
        uow.oportunidades.adicionar(op)
        uow.commit()
    with uow:
        assert uow.oportunidades.existe_chave(op.bruta.chave_deduplicacao())
        assert not uow.oportunidades.existe_chave("outra|coisa|-")


def test_pendentes_respeitam_limite_e_ordem_de_insercao(uow):
    with uow:
        for i in range(3):
            uow.oportunidades.adicionar(_op(f"P{i}", StatusOportunidade.PENDENTE))
        uow.oportunidades.adicionar(_op("Nova"))
        uow.commit()
    with uow:
        assert [o.bruta.titulo for o in uow.oportunidades.pendentes(2)] == ["P0", "P1"]


def test_listar_ordena_por_nota_desc_e_prazo_nulo_no_fim(uow):
    dia = datetime(2026, 11, 1, tzinfo=UTC)
    with uow:
        uow.oportunidades.adicionar(_op("sem prazo 90", nota=90))
        uow.oportunidades.adicionar(_op("prazo tarde 90", nota=90, prazo=dia + timedelta(days=5)))
        uow.oportunidades.adicionar(_op("prazo cedo 90", nota=90, prazo=dia))
        uow.oportunidades.adicionar(_op("nota 95", nota=95))
        uow.oportunidades.adicionar(_op("sem nota"))
        uow.oportunidades.adicionar(_op("interessa", StatusOportunidade.INTERESSA, nota=99))
        uow.commit()
    with uow:
        titulos = [o.bruta.titulo for o in uow.oportunidades.listar(StatusOportunidade.NOVA)]
        assert titulos == ["nota 95", "prazo cedo 90", "prazo tarde 90", "sem prazo 90", "sem nota"]
        assert len(uow.oportunidades.listar(StatusOportunidade.NOVA, limite=2)) == 2


def test_contar_novas_desde(uow):
    with uow:
        uow.oportunidades.adicionar(_op("velha", coletada_em=AGORA - timedelta(days=2)))
        uow.oportunidades.adicionar(_op("recente", coletada_em=AGORA))
        uow.oportunidades.adicionar(_op("pendente", StatusOportunidade.PENDENTE))
        uow.commit()
    with uow:
        assert uow.oportunidades.contar_novas_desde(AGORA - timedelta(hours=1)) == 1


def test_descartes_recentes_so_com_motivo_do_usuario(uow):
    with uow:
        uow.oportunidades.adicionar(_op("com motivo A", StatusOportunidade.DESCARTADA, motivo_usuario="caro"))
        uow.oportunidades.adicionar(_op("sem motivo", StatusOportunidade.DESCARTADA))
        uow.oportunidades.adicionar(_op("auto", StatusOportunidade.DESCARTADA_AUTO, motivo_usuario="x"))
        uow.oportunidades.adicionar(_op("com motivo B", StatusOportunidade.DESCARTADA, motivo_usuario="longe"))
        uow.commit()
    with uow:
        recentes = uow.oportunidades.descartes_recentes()
        assert [(d.titulo, d.motivo) for d in recentes] == [
            ("com motivo B", "longe"), ("com motivo A", "caro")]
        assert len(uow.oportunidades.descartes_recentes(limite=1)) == 1


def test_processo_ida_e_volta_com_notas_arquivos_historico_contatos_e_avisos(uow):
    prazo = datetime(2026, 12, 1, 10, 0, tzinfo=UTC)
    p = Processo.novo("Projeto X", AGORA, organizacao="ONU", prazo=prazo, link="https://x",
                      valor=Dinheiro(Decimal("5000.00"), "BRL"), oportunidade_id=3)
    p.anotar("primeira", AGORA)
    p.anotar("segunda", AGORA + timedelta(hours=1))
    p.anexar(Arquivo(1, "proposta.pdf", "k1", 10, AGORA))
    p.anexar(Arquivo(2, "anexo.pdf", "k2", 20, AGORA))
    p.mover(Etapa.PROPOSTA_ENVIADA, AGORA + timedelta(days=1))
    p.vincular_contato(4)
    p.vincular_contato(2)
    p.avisos_prazo_enviados.update({3, 1})
    with uow:
        id_ = uow.processos.adicionar(p).id
        uow.commit()
    with uow:
        lido = uow.processos.obter(id_)
        assert lido == p
        assert [n.texto for n in lido.notas] == ["primeira", "segunda"]
        assert [a.id for a in lido.arquivos] == [1, 2]
        assert [m.para for m in lido.historico] == [Etapa.ANALISANDO, Etapa.PROPOSTA_ENVIADA]
        assert lido.contato_ids == {2, 4} and lido.avisos_prazo_enviados == {1, 3}
        lido.anotar("terceira", AGORA)
        lido.avisos_prazo_enviados.discard(3)
        lido.contato_ids.discard(4)
        uow.processos.salvar(lido)
        uow.commit()
    with uow:
        relido = uow.processos.obter(id_)
        assert [n.texto for n in relido.notas] == ["primeira", "segunda", "terceira"]
        assert relido.avisos_prazo_enviados == {1} and relido.contato_ids == {2}
        assert [x.id for x in uow.processos.listar()] == [id_]
        assert len(relido.arquivos) == 2 and len(relido.historico) == 2


def test_lembretes(uow):
    vence = AGORA + timedelta(days=1)
    with uow:
        a = uow.lembretes.adicionar(Lembrete(None, "A", vence, 5))
        b = uow.lembretes.adicionar(Lembrete(None, "B", vence, None))
        c = uow.lembretes.adicionar(Lembrete(None, "C", vence, 5))
        uow.commit()
    with uow:
        assert uow.lembretes.obter(a.id) == Lembrete(a.id, "A", vence, 5, False)
        c = uow.lembretes.obter(c.id)
        c.concluido = True
        uow.lembretes.salvar(c)
        uow.lembretes.remover(b.id)
        uow.commit()
    with uow:
        assert [x.texto for x in uow.lembretes.nao_concluidos()] == ["A"]
        assert [x.texto for x in uow.lembretes.do_processo(5)] == ["A", "C"]
        assert uow.lembretes.obter(b.id) is None


def test_contatos_ida_e_volta(uow):
    with uow:
        c = uow.contatos.adicionar(
            Contato(None, "Ana", "ONU", "evento", date(2026, 9, 1), 30, {1, 2}))
        uow.contatos.adicionar(Contato(None, "Beto"))
        uow.commit()
    with uow:
        lido = uow.contatos.obter(c.id)
        assert lido == Contato(c.id, "Ana", "ONU", "evento", date(2026, 9, 1), 30, {1, 2})
        lido.registrar_contato(date(2026, 10, 1))
        lido.processo_ids.add(3)
        uow.contatos.salvar(lido)
        uow.commit()
    with uow:
        assert uow.contatos.obter(c.id).processo_ids == {1, 2, 3}
        assert [x.nome for x in uow.contatos.listar()] == ["Ana", "Beto"]


def test_ajustes_padrao_quando_vazio(uow):
    with uow:
        assert uow.configuracoes.ajustes() == Ajustes()
        assert uow.configuracoes.perfil() == Perfil()
        assert uow.configuracoes.obter_estado("x") is None


def test_configuracoes_ida_e_volta(uow):
    ajustes = Ajustes(limiar_alerta=70, horario_resumo=time(6, 15), avisos_prazo_dias=(7, 2, 1))
    perfil = Perfil("dados e IA", Decimal("5000.00"), None)
    with uow:
        uow.configuracoes.salvar_ajustes(ajustes)
        uow.configuracoes.salvar_perfil(perfil)
        uow.configuracoes.salvar_estado("ultima", "a")
        uow.configuracoes.salvar_estado("ultima", "b")
        uow.commit()
    with uow:
        assert uow.configuracoes.ajustes() == ajustes
        assert uow.configuracoes.perfil() == perfil
        assert uow.configuracoes.obter_estado("ultima") == "b"
        uow.configuracoes.salvar_ajustes(Ajustes(limiar_alerta=10))
        uow.commit()
    with uow:
        assert uow.configuracoes.ajustes().limiar_alerta == 10


def test_execucoes_ultima_por_fonte(uow):
    def exe(fonte, novas):
        return ExecucaoFonte(fonte, AGORA, AGORA + timedelta(seconds=5), 10, novas, None)

    with uow:
        uow.execucoes.registrar(exe("a", 1))
        uow.execucoes.registrar(exe("b", 2))
        uow.execucoes.registrar(ExecucaoFonte("a", AGORA, AGORA, 0, 0, "falhou"))
        uow.commit()
    with uow:
        ultimas = uow.execucoes.ultimas_por_fonte()
        assert [(e.fonte, e.erro) for e in ultimas] == [("a", "falhou"), ("b", None)]
        assert ultimas[1] == exe("b", 2)


def test_cotacoes_mais_recentes_por_moeda(uow):
    with uow:
        uow.cotacoes.salvar("USD", date(2026, 10, 20), Decimal("5.4321"))
        uow.cotacoes.salvar("USD", date(2026, 10, 22), Decimal("5.5000"))
        uow.cotacoes.salvar("USD", date(2026, 10, 21), Decimal("5.1000"))
        uow.cotacoes.salvar("EUR", date(2026, 10, 22), Decimal("6.1234"))
        uow.cotacoes.salvar("EUR", date(2026, 10, 22), Decimal("6.2000"))
        uow.commit()
    with uow:
        assert uow.cotacoes.mais_recentes() == {"USD": Decimal("5.5"), "EUR": Decimal("6.2")}


def test_sessao_segue_usavel_apos_varios_commits(uow):
    with uow:
        uow.oportunidades.adicionar(_op("um"))
        uow.commit()
        op = uow.oportunidades.adicionar(_op("dois"))
        uow.commit()
        assert uow.oportunidades.obter(op.id).bruta.titulo == "dois"


def test_rollback_em_excecao(uow):
    with uow:
        uow.oportunidades.adicionar(_op("persistida"))
        uow.commit()
    with pytest.raises(RuntimeError):
        with uow:
            uow.oportunidades.adicionar(_op("perdida"))
            raise RuntimeError("falha")
    with uow:
        assert uow.oportunidades.contar_novas_desde(AGORA - timedelta(days=1)) == 1
        assert not uow.oportunidades.existe_chave(_bruta("perdida").chave_deduplicacao())
