from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from radar.domain.lembrete import Lembrete
from radar.domain.perfil import Ajustes, Perfil

SP = ZoneInfo("America/Sao_Paulo")


def test_lembrete_concluido_nao_e_pendente():
    v = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
    assert Lembrete(None, "x", v).pendente_ate(date(2026, 10, 23), SP)
    assert not Lembrete(None, "x", v, concluido=True).pendente_ate(date(2026, 10, 23), SP)


def test_pendente_usa_o_dia_no_fuso_local():
    # 01:00 UTC de 24/10 ainda é 22:00 de 23/10 em São Paulo
    v = datetime(2026, 10, 24, 1, 0, tzinfo=timezone.utc)
    l = Lembrete(None, "x", v)
    assert l.pendente_ate(date(2026, 10, 23), SP)
    assert not l.pendente_ate(date(2026, 10, 22), SP)


def test_ajustes_padrao():
    a = Ajustes()
    assert a.limiar_alerta == 85 and a.avisos_prazo_dias == (3, 1)
    assert (a.horario_resumo.hour, a.horario_resumo.minute) == (7, 30)


@pytest.mark.parametrize("limiar", [-1, 101])
def test_limiar_fora_da_faixa_levanta(limiar):
    with pytest.raises(ValueError):
        Ajustes(limiar_alerta=limiar)


def test_perfil_padrao():
    p = Perfil()
    assert p.texto == "" and p.faixa_min_brl is None and p.faixa_max_brl is None
    assert Perfil("x", Decimal("1"), Decimal("2")).faixa_max_brl == Decimal("2")
