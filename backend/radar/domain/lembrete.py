"""Lembrete datado, opcionalmente ligado a um processo."""
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo


@dataclass
class Lembrete:
    id: int | None
    texto: str
    vence_em: datetime
    processo_id: int | None = None
    concluido: bool = False

    def pendente_ate(self, dia: date, tz: ZoneInfo) -> bool:
        return not self.concluido and self.vence_em.astimezone(tz).date() <= dia
