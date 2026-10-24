from datetime import datetime, timedelta, timezone

import pytest

from radar.domain.admissao import avaliar_admissao
from radar.domain.oportunidade import (
    Classificacao,
    Modalidade,
    MotivoDescarteAuto,
    Oportunidade,
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
    a = bruta(titulo="Sistema de Vigilância — Saúde")
    b = bruta(titulo="sistema de vigilancia saude.")
    assert a.chave_deduplicacao() == b.chave_deduplicacao()


def test_chave_e_sha256_hex_de_titulo_e_dia_do_prazo():
    import hashlib

    com = bruta(titulo="Título X", prazo=datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc))
    sem = bruta(titulo="Título X")
    assert com.chave_deduplicacao() == hashlib.sha256(b"titulo x|2026-11-01").hexdigest()
    assert sem.chave_deduplicacao() == hashlib.sha256(b"titulo x|-").hexdigest()
    assert len(bruta(titulo="x" * 5000).chave_deduplicacao()) == 64


def test_chave_ignora_organizacao():
    assert (bruta(organizacao="PAHO").chave_deduplicacao()
            == bruta(organizacao="OPAS/OMS Brasil").chave_deduplicacao())


def test_chave_usa_o_dia_do_prazo_em_brasilia():
    # 23:59 BRT do dia 08 é 02:59 UTC do dia 09; 18:00 BRT do dia 08 é 21:00 UTC do dia 08
    noite = bruta(prazo=datetime(2026, 10, 9, 2, 59, tzinfo=timezone.utc))
    tarde = bruta(prazo=datetime(2026, 10, 8, 21, 0, tzinfo=timezone.utc))
    assert noite.chave_deduplicacao() == tarde.chave_deduplicacao()
    assert noite.chave_deduplicacao() != bruta(
        prazo=datetime(2026, 10, 9, 21, 0, tzinfo=timezone.utc)).chave_deduplicacao()


def test_prazo_da_fonte_vale_mais_que_o_da_ia():
    fonte = datetime(2026, 11, 1, 21, 0, tzinfo=timezone.utc)
    ia = datetime(2026, 12, 1, 21, 0, tzinfo=timezone.utc)
    op = Oportunidade(None, bruta(prazo=fonte), AGORA, classificacao=classif(prazo=ia))
    assert op.prazo == fonte


def test_prazo_da_ia_quando_a_fonte_nao_tem():
    ia = datetime(2026, 12, 1, 21, 0, tzinfo=timezone.utc)
    assert Oportunidade(None, bruta(), AGORA, classificacao=classif(prazo=ia)).prazo == ia
    assert Oportunidade(None, bruta(), AGORA).prazo is None
