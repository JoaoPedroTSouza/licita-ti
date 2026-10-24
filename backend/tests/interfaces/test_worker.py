"""Agendamento do worker: ids dos jobs e isolamento de falhas."""
import logging
from types import SimpleNamespace

from radar.config import Settings
from radar.interfaces.worker import registrar_jobs


class AgendadorFalso:
    def __init__(self) -> None:
        self.chamadas: list[dict] = []

    def add_job(self, funcao, trigger=None, **kwargs) -> None:
        self.chamadas.append({"funcao": funcao, "trigger": trigger, **kwargs})

    def job(self, id: str):
        return next(c["funcao"] for c in self.chamadas if c["id"] == id)


class CasoQueFalha:
    def executar(self, *args):
        raise RuntimeError("falhou")


class CasoQueConta:
    def __init__(self) -> None:
        self.args: list[tuple] = []

    def executar(self, *args):
        self.args.append(args)


def _container(**fabricas):
    return SimpleNamespace(settings=Settings(), **fabricas)


def test_registra_os_quatro_jobs_com_ids():
    agendador = AgendadorFalso()
    registrar_jobs(agendador, _container())
    assert sorted(c["id"] for c in agendador.chamadas) == ["coleta", "cotacoes", "prazos", "resumo"]
    for c in agendador.chamadas:
        assert c["max_instances"] == 1 and c["coalesce"] is True


def test_falha_no_job_e_logada_e_nao_propaga(caplog):
    agendador = AgendadorFalso()
    container = _container(
        coletar=CasoQueFalha, resumo_diario=CasoQueFalha,
        verificar_prazos=CasoQueFalha, atualizar_cotacoes=CasoQueFalha,
    )
    registrar_jobs(agendador, container)
    with caplog.at_level(logging.ERROR):
        for id in ("coleta", "resumo", "prazos", "cotacoes"):
            agendador.job(id)()
    assert len([r for r in caplog.records if r.levelno == logging.ERROR]) == 4


def test_coleta_usa_hoje_menos_dois_dias_e_fabrica_nova_a_cada_execucao():
    agendador = AgendadorFalso()
    casos: list[CasoQueConta] = []

    def fabrica():
        casos.append(CasoQueConta())
        return casos[-1]

    registrar_jobs(agendador, _container(coletar=fabrica))
    agendador.job("coleta")()
    agendador.job("coleta")()
    assert len(casos) == 2
    desde = casos[0].args[0][0]
    from datetime import date, timedelta
    assert desde in (date.today() - timedelta(days=2), date.today() - timedelta(days=3),
                     date.today() - timedelta(days=1))
