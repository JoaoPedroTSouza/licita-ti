"""Caso de uso: triar uma oportunidade da Entrada (interessa ou descartar)."""
from radar.application.portas import Relogio, UnidadeDeTrabalho
from radar.domain.erros import NaoEncontrado, TransicaoInvalida
from radar.domain.oportunidade import Oportunidade, StatusOportunidade
from radar.domain.processo import Processo


class TriarOportunidade:
    def __init__(self, uow: UnidadeDeTrabalho, relogio: Relogio) -> None:
        self._uow = uow
        self._relogio = relogio

    def interessa(self, oportunidade_id: int) -> Processo:
        with self._uow:
            op = self._obter_nova(oportunidade_id)
            processo = self._uow.processos.adicionar(Processo.novo(
                op.bruta.titulo,
                self._relogio.agora(),
                organizacao=op.bruta.organizacao,
                oportunidade_id=op.id,
                valor=op.valor,
                prazo=op.prazo,
                link=op.bruta.link,
            ))
            op.status = StatusOportunidade.INTERESSA
            op.processo_id = processo.id
            self._uow.oportunidades.salvar(op)
            self._uow.commit()
            return processo

    def descartar(self, oportunidade_id: int, motivo: str | None) -> None:
        with self._uow:
            op = self._obter_nova(oportunidade_id)
            op.status = StatusOportunidade.DESCARTADA
            op.motivo_usuario = (motivo or "").strip() or None
            self._uow.oportunidades.salvar(op)
            self._uow.commit()

    def _obter_nova(self, oportunidade_id: int) -> Oportunidade:
        op = self._uow.oportunidades.obter(oportunidade_id)
        if op is None:
            raise NaoEncontrado(f"Oportunidade {oportunidade_id} não encontrada.")
        if op.status != StatusOportunidade.NOVA:
            raise TransicaoInvalida("Só oportunidades novas podem ser triadas.")
        return op
