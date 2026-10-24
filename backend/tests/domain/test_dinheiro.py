from decimal import Decimal

from radar.domain.dinheiro import Dinheiro, converter_para_brl


def test_converte_usd_pela_taxa():
    assert converter_para_brl(Dinheiro(Decimal("1000"), "USD"), {"USD": Decimal("5.4321")}) == Decimal("5432.10")


def test_brl_nao_precisa_de_taxa():
    assert converter_para_brl(Dinheiro(Decimal("120000"), "BRL"), {}) == Decimal("120000")


def test_moeda_sem_taxa_devolve_none():
    assert converter_para_brl(Dinheiro(Decimal("10"), "CHF"), {"USD": Decimal("5")}) is None
