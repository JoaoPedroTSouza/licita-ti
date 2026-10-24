"""Notificações: resumo diário da manhã e avisos de prazo."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from radar.application.painel import MontarPainelDoDia
from radar.application.portas import Notificador, Relogio, UnidadeDeTrabalho
from radar.domain.processo import Processo

CHAVE_ULTIMO_RESUMO = "ultimo_resumo"


def textos_resumo(novas: int, tarefas: int) -> str:
    oportunidades = "oportunidade nova" if novas == 1 else "oportunidades novas"
    tarefas_txt = "tarefa" if tarefas == 1 else "tarefas"
    return f"{novas} {oportunidades}, {tarefas} {tarefas_txt} para hoje"


class EnviarResumoDiario:
    def __init__(
        self, uow: UnidadeDeTrabalho, notificador: Notificador, relogio: Relogio,
        tz: ZoneInfo, app_url: str,
    ) -> None:
        self._uow = uow
        self._notificador = notificador
        self._relogio = relogio
        self._tz = tz
        self._app_url = app_url

    def executar(self) -> bool:
        agora = self._relogio.agora()
        local = agora.astimezone(self._tz)
        hoje = local.date().isoformat()
        with self._uow:
            if local.time() < self._uow.configuracoes.ajustes().horario_resumo:
                return False
            if self._uow.configuracoes.obter_estado(CHAVE_ULTIMO_RESUMO) == hoje:
                return False
            novas = self._uow.oportunidades.contar_novas_desde(agora - timedelta(hours=24))
        # O painel abre a própria unidade de trabalho; não aninhar.
        tarefas = len(MontarPainelDoDia(self._uow, self._relogio, self._tz).executar().para_fazer)
        with self._uow:
            self._uow.configuracoes.salvar_estado(CHAVE_ULTIMO_RESUMO, hoje)
            self._uow.commit()
        if novas == 0 and tarefas == 0:
            return False
        self._notificador.enviar(
            "Radar · bom dia", textos_resumo(novas, tarefas), f"{self._app_url}/hoje"
        )
        return True


class VerificarPrazos:
    def __init__(
        self, uow: UnidadeDeTrabalho, notificador: Notificador, relogio: Relogio,
        tz: ZoneInfo, app_url: str,
    ) -> None:
        self._uow = uow
        self._notificador = notificador
        self._relogio = relogio
        self._tz = tz
        self._app_url = app_url

    def executar(self) -> int:
        agora = self._relogio.agora()
        hoje = agora.astimezone(self._tz).date()
        enviados = 0
        with self._uow:
            limiares = self._uow.configuracoes.ajustes().avisos_prazo_dias
            for p in self._uow.processos.listar():
                if not p.aberto or p.prazo is None or p.prazo < agora:
                    continue
                prazo_local = p.prazo.astimezone(self._tz)
                dias_restantes = (prazo_local.date() - hoje).days
                atingidos = [
                    d for d in limiares
                    if d not in p.avisos_prazo_enviados and dias_restantes <= d
                ]
                if not atingidos:
                    continue
                self._avisar(p, min(atingidos), prazo_local.strftime("%d/%m %H:%M"))
                p.avisos_prazo_enviados.update(atingidos)
                self._uow.processos.salvar(p)
                enviados += 1
            self._uow.commit()
        return enviados

    def _avisar(self, p: Processo, dias: int, quando: str) -> None:
        unidade = "dia" if dias == 1 else "dias"
        self._notificador.enviar(
            f"Prazo em {dias} {unidade}: {p.titulo}", quando,
            f"{self._app_url}/funil?processo={p.id}",
        )
