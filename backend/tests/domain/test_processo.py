from datetime import datetime, timezone

import pytest

from radar.domain.erros import ErroDeDominio, TransicaoInvalida
from radar.domain.processo import ETAPAS_ABERTAS, Arquivo, Etapa, MudancaEtapa, Processo

T0 = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 10, 24, 9, 0, tzinfo=timezone.utc)


def test_novo_processo_comeca_analisando_com_historico():
    p = Processo.novo("CRM", T0, organizacao="ACME")
    assert p.etapa is Etapa.ANALISANDO
    assert p.organizacao == "ACME"
    assert p.criado_em == T0
    assert p.historico == [MudancaEtapa(None, Etapa.ANALISANDO, T0)]


def test_mover_registra_historico():
    p = Processo.novo("CRM", T0)
    p.mover(Etapa.PROPOSTA_ENVIADA, T1)
    assert p.etapa is Etapa.PROPOSTA_ENVIADA
    assert p.historico[-1] == MudancaEtapa(Etapa.ANALISANDO, Etapa.PROPOSTA_ENVIADA, T1)


def test_mover_para_mesma_etapa_levanta():
    p = Processo.novo("CRM", T0)
    with pytest.raises(TransicaoInvalida):
        p.mover(Etapa.ANALISANDO, T1)
    assert len(p.historico) == 1


def test_fechado_pode_ser_reaberto():
    p = Processo.novo("CRM", T0)
    p.mover(Etapa.FECHADO, T1)
    assert not p.aberto
    p.mover(Etapa.NEGOCIACAO, T1)
    assert p.aberto
    assert p.historico[-1] == MudancaEtapa(Etapa.FECHADO, Etapa.NEGOCIACAO, T1)


def test_aberto_somente_nas_tres_primeiras_etapas():
    assert ETAPAS_ABERTAS == {Etapa.ANALISANDO, Etapa.PROPOSTA_ENVIADA, Etapa.NEGOCIACAO}
    p = Processo.novo("CRM", T0)
    for etapa in Etapa:
        p.etapa = etapa
        assert p.aberto == (etapa in ETAPAS_ABERTAS)


@pytest.mark.parametrize("titulo", ["", "   "])
def test_titulo_vazio_levanta(titulo):
    with pytest.raises(ErroDeDominio):
        Processo.novo(titulo, T0)


def test_anotar_anexar_e_vincular_contato():
    p = Processo.novo("CRM", T0)
    p.anotar("ligar amanhã", T1)
    arq = Arquivo(None, "proposta.pdf", "k/1", 10, T1)
    p.anexar(arq)
    p.vincular_contato(7)
    p.vincular_contato(7)
    assert p.notas[0].texto == "ligar amanhã" and p.notas[0].criada_em == T1
    assert p.arquivos == [arq]
    assert p.contato_ids == {7}
