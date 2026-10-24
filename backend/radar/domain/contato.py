"""Contato da rede profissional e regra de atraso de follow-up."""
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Contato:
    id: int | None
    nome: str
    organizacao: str | None = None
    como_conheceu: str | None = None
    ultimo_contato: date | None = None
    frequencia_dias: int | None = None
    processo_ids: set[int] = field(default_factory=set)

    def atrasado(self, hoje: date) -> bool:
        if self.frequencia_dias is None:
            return False
        if self.ultimo_contato is None:
            return True
        return hoje >= self.ultimo_contato + timedelta(days=self.frequencia_dias)

    def registrar_contato(self, dia: date) -> None:
        self.ultimo_contato = dia
