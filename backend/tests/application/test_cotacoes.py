from datetime import date, datetime, timezone
from decimal import Decimal

from radar.application.cotacoes import AtualizarCotacoes
from tests.fakes import RelogioFixo, UnidadeDeTrabalhoEmMemoria


class FonteFalsaDeCotacoes:
    def __init__(self, respostas):
        self.respostas = respostas
        self.pedidos = []

    def cotacao(self, moeda, ate):
        self.pedidos.append((moeda, ate))
        return self.respostas.get(moeda)


RELOGIO = RelogioFixo(datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc))


def test_salva_o_que_vier():
    uow = UnidadeDeTrabalhoEmMemoria()
    fonte = FonteFalsaDeCotacoes({"USD": (date(2026, 10, 22), Decimal("5.10")),
                                  "EUR": (date(2026, 10, 22), Decimal("5.90"))})
    assert AtualizarCotacoes(uow, fonte, RELOGIO).executar() == 2
    assert uow.cotacoes.mais_recentes() == {"USD": Decimal("5.10"), "EUR": Decimal("5.90")}
    assert fonte.pedidos == [("USD", date(2026, 10, 23)), ("EUR", date(2026, 10, 23))]
    assert uow.commits == 1


def test_cotacao_indisponivel_mantem_anterior():
    uow = UnidadeDeTrabalhoEmMemoria()
    uow.cotacoes.salvar("USD", date(2026, 10, 20), Decimal("5.00"))
    fonte = FonteFalsaDeCotacoes({"EUR": (date(2026, 10, 22), Decimal("5.90"))})
    assert AtualizarCotacoes(uow, fonte, RELOGIO).executar() == 1
    assert uow.cotacoes.mais_recentes() == {"USD": Decimal("5.00"), "EUR": Decimal("5.90")}
