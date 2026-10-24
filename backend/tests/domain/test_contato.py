from datetime import date

from radar.domain.contato import Contato


def test_contato_sem_frequencia_nunca_atrasa():
    c = Contato(None, "Ana", ultimo_contato=date(2020, 1, 1))
    assert not c.atrasado(date(2026, 10, 23))


def test_contato_atrasa_no_dia_em_que_vence():
    c = Contato(None, "Ana", ultimo_contato=date(2026, 9, 23), frequencia_dias=30)
    assert not c.atrasado(date(2026, 10, 22)) and c.atrasado(date(2026, 10, 23))


def test_contato_nunca_contatado_com_frequencia_esta_atrasado():
    assert Contato(None, "Ana", frequencia_dias=30).atrasado(date(2026, 10, 23))


def test_registrar_contato_zera_o_atraso():
    c = Contato(None, "Ana", frequencia_dias=30)
    c.registrar_contato(date(2026, 10, 23))
    assert c.ultimo_contato == date(2026, 10, 23)
    assert not c.atrasado(date(2026, 10, 24))
