from datetime import date, datetime, timedelta, timezone

from radar.application.coletar import ColetarOportunidades
from radar.application.portas import ClassificacaoIndisponivel
from radar.domain.oportunidade import (
    Classificacao, Modalidade, MotivoDescarteAuto, Oportunidade, OportunidadeBruta,
    StatusOportunidade, TipoContratacao,
)
from tests.fakes import (
    ClassificadorFalso, FonteFalsa, NotificadorFalso, RelogioFixo,
    UnidadeDeTrabalhoEmMemoria,
)

AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def bruta(id_externo="a1", titulo="Consultoria de dados", organizacao="ONU", **kw):
    return OportunidadeBruta(
        fonte="ungm", id_externo=id_externo, titulo=titulo, organizacao=organizacao,
        link="http://x", texto="texto", prazo=kw.pop("prazo", AGORA + timedelta(days=20)), **kw,
    )


def classificacao(nota=90, modalidade=Modalidade.REMOTO_TOTAL, idioma="en", relevante=True):
    return Classificacao(
        relevante=relevante, nota=nota, resumo="r", modalidade=modalidade,
        trecho_modalidade="t", idioma=idioma,
        tipo_contratacao=TipoContratacao.EMPRESA, motivo="m",
    )


class Cenario:
    def __init__(self, fontes, respostas=None, classificador="padrao", max_classificacoes=60):
        self.uow = UnidadeDeTrabalhoEmMemoria()
        self.notificador = NotificadorFalso()
        self.classificador = ClassificadorFalso(respostas or {}) if classificador == "padrao" else classificador
        self.caso = ColetarOportunidades(
            self.uow, fontes, self.classificador, self.notificador,
            RelogioFixo(AGORA), "http://app", max_classificacoes,
        )

    def executar(self):
        return self.caso.executar(date(2026, 10, 1))


def test_admite_remota_e_descarta_presencial():
    c = Cenario(
        [FonteFalsa("ungm", [bruta("a"), bruta("b", titulo="Outra coisa")])],
        {"a": classificacao(), "b": classificacao(modalidade=Modalidade.COM_PRESENCA)},
    )
    r = c.executar()
    assert (r.novas, r.admitidas, r.descartadas_auto, r.pendentes) == (2, 1, 1, 0)
    assert len(c.uow.direto.oportunidades.listar(StatusOportunidade.NOVA)) == 1
    desc = c.uow.direto.oportunidades.listar(StatusOportunidade.DESCARTADA_AUTO)
    assert desc[0].motivo_auto == MotivoDescarteAuto.NAO_REMOTA


def test_nao_duplica_na_segunda_coleta():
    c = Cenario([FonteFalsa("ungm", [bruta()])], {"a1": classificacao()})
    assert c.executar().novas == 1
    assert c.executar().novas == 0


def test_deduplica_entre_fontes():
    c = Cenario(
        [FonteFalsa("ungm", [bruta()]), FonteFalsa("opas", [bruta("zz")])],
        {"a1": classificacao(), "zz": classificacao()},
    )
    r = c.executar()
    assert r.novas == 1
    execs = {e.fonte: e for e in c.uow.direto.execucoes.ultimas_por_fonte()}
    assert (execs["opas"].recebidas, execs["opas"].novas) == (1, 0)


def test_deduplica_dentro_do_mesmo_lote():
    c = Cenario([FonteFalsa("ungm", [bruta("a"), bruta("b")])], {"a": classificacao()})
    assert c.executar().novas == 1


def test_falha_de_uma_fonte_nao_interrompe_as_outras():
    c = Cenario(
        [FonteFalsa("ruim", [], erro=RuntimeError("layout mudou")), FonteFalsa("boa", [bruta()])],
        {"a1": classificacao()},
    )
    r = c.executar()
    assert r.erros == {"ruim": "layout mudou"} and r.novas == 1
    assert {e.fonte: e.erro for e in c.uow.direto.execucoes.ultimas_por_fonte()}["ruim"] == "layout mudou"


def test_falha_do_classificador_mantem_pendente():
    c = Cenario([FonteFalsa("ungm", [bruta()])], {"a1": ClassificacaoIndisponivel("fora")})
    r = c.executar()
    assert r.pendentes == 1 and r.admitidas == 0
    assert len(c.uow.direto.oportunidades.listar(StatusOportunidade.PENDENTE)) == 1
    c.classificador.respostas["a1"] = classificacao()
    r = c.executar()
    assert r.novas == 0 and r.admitidas == 1 and r.pendentes == 0
    assert len(c.uow.direto.oportunidades.listar(StatusOportunidade.NOVA)) == 1


def test_sem_classificador_nada_entra_na_entrada():
    c = Cenario([FonteFalsa("ungm", [bruta()])], classificador=None)
    r = c.executar()
    assert r.novas == 1 and r.pendentes == 1
    assert c.uow.direto.oportunidades.listar(StatusOportunidade.NOVA) == []


def test_respeita_teto_de_classificacoes():
    brutas = [bruta(f"i{n}", titulo=f"T{n}") for n in range(5)]
    c = Cenario(
        [FonteFalsa("ungm", brutas)], {b.id_externo: classificacao() for b in brutas},
        max_classificacoes=2,
    )
    r = c.executar()
    assert r.admitidas == 2 and r.pendentes == 3
    assert len(c.uow.direto.oportunidades.listar(StatusOportunidade.PENDENTE)) == 3


def test_alerta_quando_nota_atinge_limiar():
    c = Cenario(
        [FonteFalsa("ungm", [bruta("a"), bruta("b", titulo="Outro")])],
        {"a": classificacao(nota=85), "b": classificacao(nota=84)},
    )
    r = c.executar()
    assert r.alertas == 1 and len(c.notificador.enviadas) == 1
    titulo, corpo, url = c.notificador.enviadas[0]
    op = c.uow.direto.oportunidades.listar(StatusOportunidade.NOVA, None)[0]
    assert titulo == "Oportunidade com nota 85"
    assert corpo == "Consultoria de dados — ONU"
    assert url == f"http://app/entrada/{op.id}"


def test_descarte_automatico_nunca_alerta():
    c = Cenario(
        [FonteFalsa("ungm", [bruta()])],
        {"a1": classificacao(nota=99, modalidade=Modalidade.COM_PRESENCA)},
    )
    assert c.executar().alertas == 0 and c.notificador.enviadas == []


def test_classificador_recebe_descartes_recentes():
    c = Cenario([FonteFalsa("ungm", [bruta()])], {"a1": classificacao()})
    antiga = c.uow.direto.oportunidades.adicionar(
        Oportunidade(
            None, bruta("old", titulo="Velha"), AGORA, status=StatusOportunidade.DESCARTADA,
            motivo_usuario="muito júnior",
        )
    )
    assert antiga.id is not None
    c.executar()
    _, _, descartes = c.classificador.chamadas[0]
    assert [(d.titulo, d.motivo) for d in descartes] == [("Velha", "muito júnior")]
