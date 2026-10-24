"""Casos de uso da rede profissional: contatos e follow-up."""
from zoneinfo import ZoneInfo

from radar.application.portas import Relogio, UnidadeDeTrabalho
from radar.domain.contato import Contato
from radar.domain.erros import ErroDeDominio, NaoEncontrado

CAMPOS_EDITAVEIS = frozenset({"nome", "organizacao", "como_conheceu", "frequencia_dias"})


class Rede:
    def __init__(self, uow: UnidadeDeTrabalho, relogio: Relogio, tz: ZoneInfo) -> None:
        self._uow = uow
        self._relogio = relogio
        self._tz = tz

    def criar(
        self, nome: str, organizacao: str | None = None, como_conheceu: str | None = None,
        frequencia_dias: int | None = None,
    ) -> Contato:
        if not nome.strip():
            raise ErroDeDominio("O nome do contato não pode ser vazio.")
        with self._uow:
            contato = self._uow.contatos.adicionar(Contato(
                None, nome.strip(), organizacao, como_conheceu,
                frequencia_dias=frequencia_dias,
            ))
            self._uow.commit()
            return contato

    def editar(self, contato_id: int, **campos) -> Contato:
        desconhecidos = set(campos) - CAMPOS_EDITAVEIS
        if desconhecidos:
            raise ErroDeDominio(f"Campos não editáveis: {', '.join(sorted(desconhecidos))}.")
        if "nome" in campos and not (campos["nome"] or "").strip():
            raise ErroDeDominio("O nome do contato não pode ser vazio.")
        with self._uow:
            contato = self._contato(contato_id)
            for campo, valor in campos.items():
                setattr(contato, campo, valor)
            self._uow.contatos.salvar(contato)
            self._uow.commit()
            return contato

    def registrar_contato(self, contato_id: int) -> Contato:
        with self._uow:
            contato = self._contato(contato_id)
            contato.registrar_contato(self._relogio.agora().astimezone(self._tz).date())
            self._uow.contatos.salvar(contato)
            self._uow.commit()
            return contato

    def listar(self) -> list[Contato]:
        hoje = self._relogio.agora().astimezone(self._tz).date()
        return sorted(
            self._uow.contatos.listar(),
            key=lambda c: (not c.atrasado(hoje), c.nome.casefold()),
        )

    def _contato(self, contato_id: int) -> Contato:
        contato = self._uow.contatos.obter(contato_id)
        if contato is None:
            raise NaoEncontrado(f"Contato {contato_id} não encontrado.")
        return contato
