from datetime import datetime, timedelta, timezone

import pytest

from radar.domain.admissao import avaliar_admissao
from radar.domain.oportunidade import (
    Classificacao,
    Modalidade,
    MotivoDescarteAuto,
    OportunidadeBruta,
    TipoContratacao,
)

AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def classif(**kw) -> Classificacao:
    base = dict(
        relevante=True, nota=80, resumo="r", modalidade=Modalidade.REMOTO_TOTAL,
        trecho_modalidade="100% remote", idioma="en",
        tipo_contratacao=TipoContratacao.EMPRESA, motivo="m",
    )
    base.update(kw)
    return Classificacao(**base)


def bruta(**kw) -> OportunidadeBruta:
    base = dict(fonte="f", id_externo="1", titulo="t", organizacao="o", link="http://x", texto="x")
    base.update(kw)
    return OportunidadeBruta(**base)


def test_remoto_total_em_ingles_relevante_e_admitida():
    assert avaliar_admissao(classif(), prazo=None, agora=AGORA) is None


@pytest.mark.parametrize("modalidade", [Modalidade.COM_PRESENCA, Modalidade.INDEFINIDO])
def test_qualquer_presenca_ou_duvida_descarta(modalidade):
    assert avaliar_admissao(classif(modalidade=modalidade), None, AGORA) == MotivoDescarteAuto.NAO_REMOTA


def test_espanhol_descarta():
    assert avaliar_admissao(classif(idioma="es"), None, AGORA) == MotivoDescarteAuto.IDIOMA


def test_portugues_e_admitido():
    assert avaliar_admissao(classif(idioma="pt"), None, AGORA) is None


def test_prazo_vencido_descarta():
    assert avaliar_admissao(classif(), AGORA - timedelta(minutes=1), AGORA) == MotivoDescarteAuto.PRAZO_VENCIDO


def test_prazo_futuro_nao_descarta():
    assert avaliar_admissao(classif(), AGORA + timedelta(minutes=1), AGORA) is None


def test_sem_prazo_nao_descarta_por_prazo():
    assert avaliar_admissao(classif(prazo=None), None, AGORA) is None


def test_presenca_tem_precedencia_sobre_idioma():
    c = classif(modalidade=Modalidade.COM_PRESENCA, idioma="fr")
    assert avaliar_admissao(c, None, AGORA) == MotivoDescarteAuto.NAO_REMOTA


def test_irrelevante_descarta():
    assert avaliar_admissao(classif(relevante=False), None, AGORA) == MotivoDescarteAuto.IRRELEVANTE


@pytest.mark.parametrize("nota", [-1, 101])
def test_nota_fora_do_intervalo_levanta(nota):
    with pytest.raises(ValueError):
        classif(nota=nota)


def test_chave_ignora_acento_caixa_e_pontuacao():
    a = bruta(titulo="Sistema de Vigilância — Saúde", organizacao="OPAS")
    b = bruta(titulo="sistema de vigilancia saude", organizacao="opas.")
    assert a.chave_deduplicacao() == b.chave_deduplicacao()


def test_chave_inclui_data_do_prazo():
    com = bruta(prazo=datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc))
    sem = bruta()
    assert com.chave_deduplicacao().endswith("|2026-11-01")
    assert sem.chave_deduplicacao().endswith("|-")
