from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from radar.application.triar import TriarOportunidade
from radar.domain.dinheiro import Dinheiro
from radar.domain.erros import NaoEncontrado, TransicaoInvalida
from radar.domain.oportunidade import (
    Classificacao, Modalidade, Oportunidade, OportunidadeBruta, StatusOportunidade,
    TipoContratacao,
)
from radar.domain.processo import Etapa
from tests.fakes import RelogioFixo, UnidadeDeTrabalhoEmMemoria

AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
PRAZO = AGORA + timedelta(days=10)
VALOR = Dinheiro(Decimal("1000"), "USD")


def cenario():
    uow = UnidadeDeTrabalhoEmMemoria()
    bruta = OportunidadeBruta(
        fonte="ungm", id_externo="a", titulo="Consultoria de dados", organizacao="ONU",
        link="http://x", texto="t", prazo=PRAZO, valor=VALOR,
    )
    op = uow.oportunidades.adicionar(Oportunidade(
        None, bruta, AGORA, status=StatusOportunidade.NOVA,
        classificacao=Classificacao(
            True, 90, "r", Modalidade.REMOTO_TOTAL, "t", "en", TipoContratacao.EMPRESA, "m",
        ),
    ))
    return uow, TriarOportunidade(uow, RelogioFixo(AGORA)), op


def test_interessa_cria_processo_analisando_com_dados_da_oportunidade():
    uow, triar, op = cenario()
    processo = triar.interessa(op.id)
    assert processo.id is not None
    assert processo.etapa == Etapa.ANALISANDO
    assert (processo.titulo, processo.organizacao, processo.link) == (
        "Consultoria de dados", "ONU", "http://x")
    assert processo.valor == VALOR
    assert processo.prazo == PRAZO
    assert processo.oportunidade_id == op.id
    assert op.status == StatusOportunidade.INTERESSA
    assert op.processo_id == processo.id
    assert uow.commits == 1


def test_triar_duas_vezes_levanta_transicao_invalida():
    _, triar, op = cenario()
    triar.interessa(op.id)
    with pytest.raises(TransicaoInvalida):
        triar.interessa(op.id)
    with pytest.raises(TransicaoInvalida):
        triar.descartar(op.id, "motivo")


def test_descartar_guarda_motivo_e_entra_nos_descartes_recentes():
    uow, triar, op = cenario()
    triar.descartar(op.id, "valor baixo")
    assert op.status == StatusOportunidade.DESCARTADA
    assert op.motivo_usuario == "valor baixo"
    assert [d.motivo for d in uow.oportunidades.descartes_recentes()] == ["valor baixo"]
    assert uow.commits == 1


def test_descartar_com_motivo_em_branco_guarda_none():
    _, triar, op = cenario()
    triar.descartar(op.id, "   ")
    assert op.status == StatusOportunidade.DESCARTADA
    assert op.motivo_usuario is None


def test_oportunidade_inexistente_levanta_nao_encontrado():
    _, triar, _ = cenario()
    with pytest.raises(NaoEncontrado):
        triar.interessa(999)
    with pytest.raises(NaoEncontrado):
        triar.descartar(999, None)
