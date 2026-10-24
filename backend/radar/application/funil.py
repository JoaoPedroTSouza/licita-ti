"""Casos de uso do funil: processos, notas, arquivos, contatos vinculados e lembretes."""
from datetime import datetime
from typing import Any

from radar.application.portas import ArmazenamentoArquivos, Relogio, UnidadeDeTrabalho
from radar.domain.dinheiro import Dinheiro
from radar.domain.erros import NaoEncontrado
from radar.domain.lembrete import Lembrete
from radar.domain.processo import Arquivo, Etapa, Processo


_MANTER: Any = object()  # "campo não enviado": diferente de None, que limpa o campo


class Funil:
    def __init__(
        self, uow: UnidadeDeTrabalho, relogio: Relogio, armazenamento: ArmazenamentoArquivos
    ) -> None:
        self._uow = uow
        self._relogio = relogio
        self._armazenamento = armazenamento

    def criar_manual(
        self, titulo: str, organizacao: str | None, valor: Dinheiro | None,
        prazo: datetime | None,
    ) -> Processo:
        with self._uow:
            processo = self._uow.processos.adicionar(Processo.novo(
                titulo, self._relogio.agora(), organizacao=organizacao, valor=valor, prazo=prazo,
            ))
            self._uow.commit()
            return processo

    def editar(
        self, processo_id: int, *, titulo: str | None = None, organizacao: str | None = _MANTER,
        valor: Dinheiro | None = _MANTER, prazo: datetime | None = _MANTER,
        link: str | None = _MANTER,
    ) -> Processo:
        """Campos omitidos ficam como estão; passar None limpa organizacao, valor, prazo ou link."""
        with self._uow:
            p = self._processo(processo_id)
            if titulo is not None:
                p.titulo = titulo
            if organizacao is not _MANTER:
                p.organizacao = organizacao
            if valor is not _MANTER:
                p.valor = valor
            if prazo is not _MANTER and prazo != p.prazo:
                p.prazo = prazo
                p.avisos_prazo_enviados.clear()
            if link is not _MANTER:
                p.link = link
            self._uow.processos.salvar(p)
            self._uow.commit()
            return p

    def mover(self, processo_id: int, etapa: Etapa) -> Processo:
        with self._uow:
            p = self._processo(processo_id)
            p.mover(etapa, self._relogio.agora())
            self._uow.processos.salvar(p)
            self._uow.commit()
            return p

    def anotar(self, processo_id: int, texto: str) -> Processo:
        with self._uow:
            p = self._processo(processo_id)
            p.anotar(texto, self._relogio.agora())
            self._uow.processos.salvar(p)
            self._uow.commit()
            return p

    def anexar(self, processo_id: int, nome: str, conteudo: bytes) -> Arquivo:
        with self._uow:
            p = self._processo(processo_id)
            chave = self._armazenamento.salvar(nome, conteudo)
            # o repositório guarda os arquivos dentro do processo; o id é local a ele
            proximo = max((a.id or 0 for a in p.arquivos), default=0) + 1
            arquivo = Arquivo(proximo, nome, chave, len(conteudo), self._relogio.agora())
            p.anexar(arquivo)
            self._uow.processos.salvar(p)
            self._uow.commit()
            return arquivo

    def abrir_arquivo(self, processo_id: int, arquivo_id: int) -> tuple[Arquivo, bytes]:
        with self._uow:
            p = self._processo(processo_id)
            arquivo = next((a for a in p.arquivos if a.id == arquivo_id), None)
            if arquivo is None:
                raise NaoEncontrado(f"Arquivo {arquivo_id} não encontrado.")
            return arquivo, self._armazenamento.abrir(arquivo.chave)

    def vincular_contato(self, processo_id: int, contato_id: int) -> None:
        with self._uow:
            p = self._processo(processo_id)
            c = self._uow.contatos.obter(contato_id)
            if c is None:
                raise NaoEncontrado(f"Contato {contato_id} não encontrado.")
            p.vincular_contato(contato_id)
            c.processo_ids.add(processo_id)
            self._uow.processos.salvar(p)
            self._uow.contatos.salvar(c)
            self._uow.commit()

    def criar_lembrete(
        self, texto: str, vence_em: datetime, processo_id: int | None
    ) -> Lembrete:
        with self._uow:
            if processo_id is not None:
                self._processo(processo_id)
            lembrete = self._uow.lembretes.adicionar(Lembrete(None, texto, vence_em, processo_id))
            self._uow.commit()
            return lembrete

    def concluir_lembrete(self, lembrete_id: int) -> Lembrete:
        with self._uow:
            lembrete = self._lembrete(lembrete_id)
            lembrete.concluido = True
            self._uow.lembretes.salvar(lembrete)
            self._uow.commit()
            return lembrete

    def remover_lembrete(self, lembrete_id: int) -> None:
        with self._uow:
            self._lembrete(lembrete_id)
            self._uow.lembretes.remover(lembrete_id)
            self._uow.commit()

    def _processo(self, processo_id: int) -> Processo:
        p = self._uow.processos.obter(processo_id)
        if p is None:
            raise NaoEncontrado(f"Processo {processo_id} não encontrado.")
        return p

    def _lembrete(self, lembrete_id: int) -> Lembrete:
        lembrete = self._uow.lembretes.obter(lembrete_id)
        if lembrete is None:
            raise NaoEncontrado(f"Lembrete {lembrete_id} não encontrado.")
        return lembrete
