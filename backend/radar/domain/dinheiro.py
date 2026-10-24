"""Valor monetário e conversão para BRL."""
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Dinheiro:
    valor: Decimal
    moeda: str  # ISO 4217 maiúsculo

    def __post_init__(self) -> None:
        object.__setattr__(self, "moeda", self.moeda.upper())


def converter_para_brl(d: Dinheiro, taxas: Mapping[str, Decimal]) -> Decimal | None:
    """Converte para BRL; `None` se a moeda não tem taxa. `taxas` mapeia moeda -> BRL."""
    if d.moeda == "BRL":
        return d.valor
    taxa = taxas.get(d.moeda)
    if taxa is None:
        return None
    return (d.valor * taxa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
