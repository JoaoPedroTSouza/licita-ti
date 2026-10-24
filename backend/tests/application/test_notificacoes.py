from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from radar.application.notificacoes import EnviarResumoDiario, VerificarPrazos, textos_resumo
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import (
    Classificacao, Modalidade, Oportunidade, OportunidadeBruta, StatusOportunidade,
    TipoContratacao,
)
from radar.domain.processo import Etapa, Processo
from tests.fakes import NotificadorFalso, UnidadeDeTrabalhoEmMemoria

UTC = timezone.utc
TZ = ZoneInfo("America/Sao_Paulo")
URL = "https://radar.exemplo"


@pytest.mark.parametrize("n,m,esperado", [
    (1, 1, "1 oportunidade nova, 1 tarefa para hoje"),
    (3, 0, "3 oportunidades novas, 0 tarefas para hoje"),
    (0, 2, "0 oportunidades novas, 2 tarefas para hoje"),
])
def test_textos_resumo(n, m, esperado):
    assert textos_resumo(n, m) == esperado


class Relogio:
    def __init__(self, agora):
        self._agora = agora

    def agora(self):
        return self._agora

    def avancar(self, **kw):
        self._agora += timedelta(**kw)


def resumo(agora):
    uow = UnidadeDeTrabalhoEmMemoria()
    n = NotificadorFalso()
    relogio = Relogio(agora)
    return uow, n, relogio, EnviarResumoDiario(uow, n, relogio, TZ, URL)


def add_nova(uow, agora):
    bruta = OportunidadeBruta("f", "1", "T", "O", "http://x", "t")
    c = Classificacao(True, 90, "r", Modalidade.REMOTO_TOTAL, "t", "pt", TipoContratacao.EMPRESA, "m")
    uow.direto.oportunidades.adicionar(Oportunidade(None, bruta, agora - timedelta(hours=2), StatusOportunidade.NOVA, c))


def test_resumo_antes_do_horario_nao_envia():
    agora = datetime(2026, 10, 23, 10, 29, tzinfo=UTC)  # 07:29 BRT
    uow, n, _, caso = resumo(agora)
    add_nova(uow, agora)
    assert caso.executar() is False
    assert n.enviadas == []


def test_resumo_envia_uma_vez_por_dia():
    agora = datetime(2026, 10, 23, 10, 30, tzinfo=UTC)  # 07:30 BRT
    uow, n, relogio, caso = resumo(agora)
    add_nova(uow, agora)
    assert caso.executar() is True
    relogio.avancar(hours=1, minutes=30)  # 09:00 BRT
    assert caso.executar() is False
    assert n.enviadas == [("Radar · bom dia", "1 oportunidade nova, 0 tarefas para hoje", f"{URL}/hoje")]
    assert uow.direto.configuracoes.obter_estado("ultimo_resumo") == "2026-10-23"


def test_resumo_no_dia_seguinte_envia_de_novo():
    agora = datetime(2026, 10, 23, 10, 30, tzinfo=UTC)
    uow, n, relogio, caso = resumo(agora)
    add_nova(uow, agora)
    caso.executar()
    relogio.avancar(days=1)
    add_nova(uow, relogio.agora())
    assert caso.executar() is True
    assert len(n.enviadas) == 2


def test_resumo_vazio_nao_envia_mas_marca_o_dia():
    agora = datetime(2026, 10, 23, 10, 30, tzinfo=UTC)
    uow, n, _, caso = resumo(agora)
    assert caso.executar() is False
    assert n.enviadas == []
    assert uow.direto.configuracoes.obter_estado("ultimo_resumo") == "2026-10-23"


def test_resumo_conta_tarefas_do_painel():
    agora = datetime(2026, 10, 23, 10, 30, tzinfo=UTC)
    uow, n, _, caso = resumo(agora)
    uow.direto.lembretes.adicionar(Lembrete(None, "x", agora))
    caso.executar()
    assert n.enviadas[0][1] == "0 oportunidades novas, 1 tarefa para hoje"


PRAZO = datetime(2026, 10, 26, 15, 0, tzinfo=UTC)  # 12:00 BRT de 26/10


def prazos(agora, prazo=PRAZO, etapa=Etapa.ANALISANDO):
    uow = UnidadeDeTrabalhoEmMemoria()
    p = Processo.novo("Edital X", agora, prazo=prazo)
    p.etapa = etapa
    uow.direto.processos.adicionar(p)
    n = NotificadorFalso()
    relogio = Relogio(agora)
    return uow, p, n, relogio, VerificarPrazos(uow, n, relogio, TZ, URL)


def test_aviso_de_prazo_3_e_1_dia_sem_repetir():
    _, p, n, relogio, caso = prazos(PRAZO - timedelta(days=3))  # 23/10 12:00 BRT
    assert caso.executar() == 1
    assert n.enviadas == [("Prazo em 3 dias: Edital X", "26/10 12:00", f"{URL}/funil?processo={p.id}")]
    assert p.avisos_prazo_enviados == {3}
    assert caso.executar() == 0
    relogio.avancar(days=2)  # 25/10 12:00 BRT: falta 1 dia de calendario
    assert caso.executar() == 1
    assert n.enviadas[1][0] == "Prazo em 1 dia: Edital X"
    assert p.avisos_prazo_enviados == {3, 1}


def test_varios_limiares_de_uma_vez_enviam_um_aviso():
    _, p, n, _, caso = prazos(PRAZO - timedelta(hours=20))
    assert caso.executar() == 1
    assert n.enviadas[0][0] == "Prazo em 1 dia: Edital X"
    assert p.avisos_prazo_enviados == {3, 1}


def test_prazo_passado_nao_avisa():
    _, p, n, _, caso = prazos(PRAZO + timedelta(hours=1))
    assert caso.executar() == 0
    assert n.enviadas == [] and p.avisos_prazo_enviados == set()


def test_processo_fechado_ou_distante_nao_avisa():
    _, _, n, _, caso = prazos(PRAZO - timedelta(days=1), etapa=Etapa.FECHADO)
    assert caso.executar() == 0
    _, _, n, _, caso = prazos(PRAZO - timedelta(days=10))
    assert caso.executar() == 0


def test_prazo_hoje_usa_texto_proprio():
    _, p, n, _, caso = prazos(PRAZO - timedelta(hours=2))  # 10:00 BRT de 26/10
    assert caso.executar() == 1
    assert n.enviadas[0][0] == "Prazo hoje: Edital X"
    assert p.avisos_prazo_enviados == {3, 1}


def test_texto_usa_dias_reais_e_nao_o_limiar():
    _, p, n, _, caso = prazos(PRAZO - timedelta(days=2))  # 24/10: limiar 3 atingido, faltam 2
    assert caso.executar() == 1
    assert n.enviadas[0][0] == "Prazo em 2 dias: Edital X"
    assert p.avisos_prazo_enviados == {3}


def test_falha_do_notificador_preserva_avisos_ja_confirmados():
    agora = PRAZO - timedelta(days=3)
    uow = UnidadeDeTrabalhoEmMemoria()
    for titulo in ("Um", "Dois"):
        uow.direto.processos.adicionar(Processo.novo(titulo, agora, prazo=PRAZO))

    class NotificadorQuebrado(NotificadorFalso):
        def enviar(self, titulo, corpo, url):
            if "Dois" in titulo:
                raise RuntimeError("push fora do ar")
            return super().enviar(titulo, corpo, url)

    caso = VerificarPrazos(uow, NotificadorQuebrado(), Relogio(agora), TZ, URL)
    with pytest.raises(RuntimeError):
        caso.executar()
    um, dois = uow.direto.processos.listar()
    assert um.avisos_prazo_enviados == {3}
    assert dois.avisos_prazo_enviados == set()
    assert uow.commits == 1
