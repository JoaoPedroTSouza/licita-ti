"""Atualização das cotações de moedas para BRL."""
from datetime import UTC

from radar.application.portas import FonteDeCotacoes, Relogio, UnidadeDeTrabalho


class AtualizarCotacoes:
    def __init__(
        self, uow: UnidadeDeTrabalho, fonte: FonteDeCotacoes, relogio: Relogio,
        moedas: tuple[str, ...] = ("USD", "EUR"),
    ) -> None:
        self._uow = uow
        self._fonte = fonte
        self._relogio = relogio
        self._moedas = moedas

    def executar(self) -> int:
        ate = self._relogio.agora().astimezone(UTC).date()
        salvas = 0
        with self._uow:
            for moeda in self._moedas:
                cotacao = self._fonte.cotacao(moeda, ate)
                if cotacao is None:
                    continue
                dia, valor = cotacao
                self._uow.cotacoes.salvar(moeda, dia, valor)
                salvas += 1
            self._uow.commit()
        return salvas
