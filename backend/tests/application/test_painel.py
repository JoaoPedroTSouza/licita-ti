from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from radar.application.painel import MontarPainelDoDia
from radar.domain.contato import Contato
from radar.domain.dinheiro import Dinheiro
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import (
    Classificacao, Modalidade, Oportunidade, OportunidadeBruta, StatusOportunidade,
    TipoContratacao,
)
from radar.domain.processo import Etapa, Processo
from tests.fakes import RelogioFixo, UnidadeDeTrabalhoEmMemoria

UTC = timezone.utc
TZ = ZoneInfo("America/Sao_Paulo")
AGORA = datetime(2026, 10, 23, 15, 0, tzinfo=UTC)


def cenario(agora=AGORA):
    uow = UnidadeDeTrabalhoEmMemoria()
    return uow, MontarPainelDoDia(uow, RelogioFixo(agora), TZ)


def lembrete(uow, vence_em, texto="x", processo_id=None):
    return uow.lembretes.adicionar(Lembrete(None, texto, vence_em, processo_id))


def processo(uow, titulo="P", etapa=Etapa.ANALISANDO, valor=None, prazo=None):
    p = Processo.novo(titulo, AGORA, valor=valor, prazo=prazo)
    p.etapa = etapa
    return uow.processos.adicionar(p)


def test_lembrete_23h30_brt_aparece_hoje():
    uow, caso = cenario()
    lembrete(uow, datetime(2026, 10, 24, 2, 30, tzinfo=UTC))  # 23:30 BRT de 23/10
    assert [i.tipo for i in caso.executar().para_fazer] == ["lembrete"]


def test_lembrete_de_amanha_nao_aparece():
    uow, caso = cenario()
    lembrete(uow, datetime(2026, 10, 24, 3, 30, tzinfo=UTC))  # 00:30 BRT de 24/10
    assert caso.executar().para_fazer == []


def test_ordem_lembretes_prazos_contatos():
    uow, caso = cenario()
    contato = uow.contatos.adicionar(Contato(None, "Ana", frequencia_dias=7))
    p = processo(uow, "Edital", prazo=AGORA + timedelta(days=2))
    tardio = lembrete(uow, datetime(2026, 10, 23, 20, 0, tzinfo=UTC), "B", p.id)
    cedo = lembrete(uow, datetime(2026, 10, 22, 12, 0, tzinfo=UTC), "A")
    itens = caso.executar().para_fazer
    assert [(i.tipo, i.titulo) for i in itens] == [
        ("lembrete", "A"), ("lembrete", "B"), ("prazo", "Prazo: Edital"), ("contato", "Falar com Ana"),
    ]
    assert [i.ref_id for i in itens] == [cedo.id, tardio.id, p.id, contato.id]
    assert [i.processo_id for i in itens] == [None, p.id, p.id, None]
    assert itens[2].quando == p.prazo


def test_prazo_fora_da_janela_ou_passado_ou_fechado_nao_aparece():
    uow, caso = cenario()
    processo(uow, "longe", prazo=AGORA + timedelta(days=5))
    processo(uow, "passado", prazo=AGORA - timedelta(hours=1))
    processo(uow, "fechado", etapa=Etapa.FECHADO, prazo=AGORA + timedelta(days=1))
    processo(uow, "sem prazo")
    assert caso.executar().para_fazer == []


def test_valor_aberto_converte_e_ignora_fechados():
    uow, caso = cenario()
    uow.cotacoes.salvar("USD", date(2026, 10, 22), Decimal("5.00"))
    processo(uow, valor=Dinheiro(Decimal("120000"), "BRL"))
    processo(uow, valor=Dinheiro(Decimal("1000"), "USD"))
    processo(uow, etapa=Etapa.FECHADO, valor=Dinheiro(Decimal("999"), "BRL"))
    funil = caso.executar().funil
    assert funil.valor_aberto_brl == Decimal("125000.00")
    assert funil.sem_conversao == 0
    assert funil.contagem[Etapa.ANALISANDO] == 2
    assert funil.contagem[Etapa.FECHADO] == 1
    assert funil.contagem[Etapa.PERDIDO] == 0
    assert set(funil.contagem) == set(Etapa)


def test_moeda_sem_taxa_conta_em_sem_conversao():
    uow, caso = cenario()
    processo(uow, valor=Dinheiro(Decimal("10"), "JPY"))
    processo(uow, valor=Dinheiro(Decimal("100"), "BRL"))
    funil = caso.executar().funil
    assert funil.sem_conversao == 1
    assert funil.valor_aberto_brl == Decimal("100")


def nova(uow, nota, titulo):
    bruta = OportunidadeBruta("f", titulo, titulo, "Org", "http://x", "t")
    c = Classificacao(True, nota, "r", Modalidade.REMOTO_TOTAL, "t", "pt",
                      TipoContratacao.EMPRESA, "m")
    return uow.oportunidades.adicionar(
        Oportunidade(None, bruta, AGORA, StatusOportunidade.NOVA, c)
    )


def test_melhores_novas_no_maximo_cinco_por_nota():
    uow, caso = cenario()
    for n in (10, 90, 50, 70, 30, 80, 60):
        nova(uow, n, f"op{n}")
    notas = [o.classificacao.nota for o in caso.executar().melhores_novas]
    assert notas == [90, 80, 70, 60, 50]
