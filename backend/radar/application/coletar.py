"""Caso de uso: coletar oportunidades das fontes, classificar, admitir e alertar."""
from dataclasses import dataclass, field
from datetime import date

from radar.application.portas import (
    ClassificacaoIndisponivel, Classificador, ExecucaoFonte, FonteDeOportunidades,
    Notificador, Relogio, UnidadeDeTrabalho,
)
from radar.domain.admissao import avaliar_admissao
from radar.domain.oportunidade import Oportunidade, StatusOportunidade


@dataclass
class ResumoColeta:
    novas: int = 0
    admitidas: int = 0
    descartadas_auto: int = 0
    pendentes: int = 0
    alertas: int = 0
    erros: dict[str, str] = field(default_factory=dict)


class ColetarOportunidades:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        fontes: list[FonteDeOportunidades],
        classificador: Classificador | None,
        notificador: Notificador,
        relogio: Relogio,
        app_url: str,
        max_classificacoes: int = 60,
    ) -> None:
        self._uow = uow
        self._fontes = fontes
        self._classificador = classificador
        self._notificador = notificador
        self._relogio = relogio
        self._app_url = app_url
        self._max = max_classificacoes

    def executar(self, desde: date) -> ResumoColeta:
        resumo = ResumoColeta()
        for fonte in self._fontes:
            self._coletar_fonte(fonte, desde, resumo)
        if self._classificador is not None:
            self._classificar_pendentes(self._classificador, resumo)
        resumo.pendentes = len(self._uow.oportunidades.pendentes(10**9))
        return resumo

    def _coletar_fonte(
        self, fonte: FonteDeOportunidades, desde: date, resumo: ResumoColeta
    ) -> None:
        iniciada = self._relogio.agora()
        recebidas = novas = 0
        erro = None
        try:
            brutas = fonte.buscar(desde)
            recebidas = len(brutas)
            for bruta in brutas:
                # a chave passa a existir após o adicionar, o que cobre repetidas no lote
                if self._uow.oportunidades.existe_chave(bruta.chave_deduplicacao()):
                    continue
                self._uow.oportunidades.adicionar(Oportunidade(None, bruta, iniciada))
                novas += 1
        except Exception as e:  # uma fonte ruim não derruba as outras
            erro = str(e)
            resumo.erros[fonte.nome] = erro
        resumo.novas += novas
        self._uow.execucoes.registrar(
            ExecucaoFonte(fonte.nome, iniciada, self._relogio.agora(), recebidas, novas, erro)
        )
        self._uow.commit()

    def _classificar_pendentes(self, classificador: Classificador, resumo: ResumoColeta) -> None:
        perfil = self._uow.configuracoes.perfil()
        limiar = self._uow.configuracoes.ajustes().limiar_alerta
        descartes = self._uow.oportunidades.descartes_recentes()
        for op in self._uow.oportunidades.pendentes(self._max):
            try:
                c = classificador.classificar(op.bruta, perfil, descartes)
            except ClassificacaoIndisponivel:
                continue
            op.classificacao = c
            motivo = avaliar_admissao(c, op.prazo, self._relogio.agora())
            if motivo is None:
                op.status = StatusOportunidade.NOVA
                resumo.admitidas += 1
            else:
                op.status = StatusOportunidade.DESCARTADA_AUTO
                op.motivo_auto = motivo
                resumo.descartadas_auto += 1
            self._uow.oportunidades.salvar(op)
            self._uow.commit()
            if motivo is None and c.nota >= limiar:
                self._notificador.enviar(
                    f"Oportunidade com nota {c.nota}",
                    f"{op.bruta.titulo} — {op.bruta.organizacao}",
                    f"{self._app_url}/entrada/{op.id}",
                )
                resumo.alertas += 1
