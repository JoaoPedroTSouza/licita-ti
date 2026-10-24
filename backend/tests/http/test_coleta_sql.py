"""Coleta de ponta a ponta com o Container e a unidade de trabalho SQL (SQLite em memória)."""
from datetime import date, timedelta

from radar.domain.oportunidade import (
    Classificacao, Modalidade, OportunidadeBruta, StatusOportunidade, TipoContratacao,
)
from tests.fakes import ClassificadorFalso, FonteFalsa
from tests.http.conftest import AGORA, montar_container


def _bruta(id_externo: str, titulo: str, link: str | None = "https://x/1") -> OportunidadeBruta:
    return OportunidadeBruta(
        fonte="f", id_externo=id_externo, titulo=titulo, organizacao="Org", link=link,
        texto="texto", prazo=AGORA + timedelta(days=20),
    )


def _remota() -> Classificacao:
    return Classificacao(
        relevante=True, nota=50, resumo="r", modalidade=Modalidade.REMOTO_TOTAL,
        trecho_modalidade="remoto", idioma="pt", tipo_contratacao=TipoContratacao.EMPRESA,
        motivo="m",
    )


def _container(tmp_path, fontes, respostas):
    c = montar_container(tmp_path)
    c.fontes = fontes
    c.classificador = ClassificadorFalso(respostas)
    return c


def test_coleta_grava_novas_e_registra_execucoes(tmp_path):
    c = _container(
        tmp_path,
        [FonteFalsa("quebrada", [], erro=RuntimeError("fora do ar")),
         FonteFalsa("boa", [_bruta("a", "Consultoria A"), _bruta("b", "Consultoria B")])],
        {"a": _remota(), "b": _remota()},
    )
    r = c.coletar().executar(date(2026, 10, 1))
    assert (r.novas, r.admitidas, r.pendentes) == (2, 2, 0)
    assert r.erros == {"quebrada": "fora do ar"}
    with c.uow() as uow:
        assert len(uow.oportunidades.listar(StatusOportunidade.NOVA)) == 2
        execs = {e.fonte: e for e in uow.execucoes.ultimas_por_fonte()}
    assert execs["quebrada"].erro == "fora do ar"
    assert (execs["boa"].recebidas, execs["boa"].novas, execs["boa"].erro) == (2, 2, None)


def test_erro_de_persistencia_faz_rollback_e_as_demais_fontes_seguem(tmp_path):
    # link None viola NOT NULL no INSERT: a sessão precisa de rollback antes de seguir
    c = _container(
        tmp_path,
        [FonteFalsa("ruim", [_bruta("x", "Valida antes"), _bruta("y", "Sem link", link=None)]),
         FonteFalsa("boa", [_bruta("a", "Consultoria A")])],
        {"a": _remota()},
    )
    r = c.coletar().executar(date(2026, 10, 1))
    assert "ruim" in r.erros and r.novas == 1 and r.admitidas == 1
    with c.uow() as uow:
        titulos = [o.bruta.titulo for o in uow.oportunidades.listar(StatusOportunidade.NOVA)]
        assert uow.oportunidades.pendentes(10) == []
        execs = {e.fonte: e for e in uow.execucoes.ultimas_por_fonte()}
    assert titulos == ["Consultoria A"]
    assert execs["ruim"].erro and execs["ruim"].novas == 0
    assert execs["boa"].erro is None
