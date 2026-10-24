"""Perfil profissional do dono e ajustes do Radar."""
from dataclasses import dataclass
from datetime import time
from decimal import Decimal


@dataclass
class Perfil:
    texto: str = ""
    faixa_min_brl: Decimal | None = None
    faixa_max_brl: Decimal | None = None


@dataclass
class Ajustes:
    limiar_alerta: int = 85
    horario_resumo: time = time(7, 30)
    avisos_prazo_dias: tuple[int, ...] = (3, 1)

    def __post_init__(self) -> None:
        if not 0 <= self.limiar_alerta <= 100:
            raise ValueError("limiar_alerta deve estar entre 0 e 100.")
