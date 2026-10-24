"""Dublês em memória das portas, compartilhados pelos testes de aplicação e interface."""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

from radar.application.portas import DescarteRecente, ExecucaoFonte
from radar.domain.oportunidade import (
    Classificacao, Oportunidade, OportunidadeBruta, StatusOportunidade,
)
from radar.domain.perfil import Ajustes, Perfil


class _Repositorio:
    """Guarda os próprios objetos recebidos, com ids sequenciais."""

    def __init__(self) -> None:
        self._itens: dict[int, object] = {}
        self._proximo = 1

    def adicionar(self, item):
        item.id = self._proximo
        self._itens[item.id] = item
        self._proximo += 1
        return item

    def obter(self, id: int):
        return self._itens.get(id)

    def salvar(self, item) -> None:
        self._itens[item.id] = item

    def listar(self) -> list:
        return list(self._itens.values())


class RepositorioOportunidadesEmMemoria(_Repositorio):
    def listar(self, status: StatusOportunidade, limite: int | None = None) -> list[Oportunidade]:
        itens = [o for o in self._itens.values() if o.status == status]
        itens.sort(key=lambda o: (
            -(o.classificacao.nota if o.classificacao else 0),
            o.prazo is None,
            o.prazo.timestamp() if o.prazo else 0,
        ))
        return itens if limite is None else itens[:limite]

    def existe_chave(self, chave: str) -> bool:
        return any(o.bruta.chave_deduplicacao() == chave for o in self._itens.values())

    def pendentes(self, limite: int) -> list[Oportunidade]:
        return [o for o in self._itens.values() if o.status == StatusOportunidade.PENDENTE][:limite]

    def contar_novas_desde(self, desde: datetime) -> int:
        return sum(
            1 for o in self._itens.values()
            if o.status == StatusOportunidade.NOVA and o.coletada_em >= desde
        )

    def descartes_recentes(self, limite: int = 20) -> list[DescarteRecente]:
        descartadas = [
            o for o in self._itens.values()
            if o.status == StatusOportunidade.DESCARTADA and o.motivo_usuario
        ]
        return [DescarteRecente(o.bruta.titulo, o.motivo_usuario) for o in reversed(descartadas)][:limite]


class RepositorioProcessosEmMemoria(_Repositorio):
    pass


class RepositorioLembretesEmMemoria(_Repositorio):
    def remover(self, id: int) -> None:
        self._itens.pop(id, None)

    def nao_concluidos(self) -> list:
        return [x for x in self._itens.values() if not x.concluido]

    def do_processo(self, processo_id: int) -> list:
        return [x for x in self._itens.values() if x.processo_id == processo_id]


class RepositorioContatosEmMemoria(_Repositorio):
    pass


class RepositorioConfiguracoesEmMemoria:
    def __init__(self) -> None:
        self._perfil: Perfil | None = None
        self._ajustes: Ajustes | None = None
        self._estado: dict[str, str] = {}

    def perfil(self) -> Perfil:
        return self._perfil if self._perfil is not None else Perfil()

    def salvar_perfil(self, perfil: Perfil) -> None:
        self._perfil = perfil

    def ajustes(self) -> Ajustes:
        return self._ajustes if self._ajustes is not None else Ajustes()

    def salvar_ajustes(self, ajustes: Ajustes) -> None:
        self._ajustes = ajustes

    def obter_estado(self, chave: str) -> str | None:
        return self._estado.get(chave)

    def salvar_estado(self, chave: str, valor: str) -> None:
        self._estado[chave] = valor


class RepositorioExecucoesEmMemoria:
    def __init__(self) -> None:
        self.registradas: list[ExecucaoFonte] = []

    def registrar(self, execucao: ExecucaoFonte) -> None:
        self.registradas.append(execucao)

    def ultimas_por_fonte(self) -> list[ExecucaoFonte]:
        ultimas: dict[str, ExecucaoFonte] = {}
        for e in self.registradas:
            ultimas[e.fonte] = e
        return list(ultimas.values())


class RepositorioCotacoesEmMemoria:
    def __init__(self) -> None:
        self._por_moeda: dict[str, tuple[date, Decimal]] = {}

    def salvar(self, moeda: str, dia: date, valor: Decimal) -> None:
        atual = self._por_moeda.get(moeda)
        if atual is None or dia >= atual[0]:
            self._por_moeda[moeda] = (dia, valor)

    def mais_recentes(self) -> dict[str, Decimal]:
        return {m: v for m, (_, v) in self._por_moeda.items()}


class _Repositorios:
    """Os repositórios do fake; `uow.direto` os expõe aos testes fora de `with`."""

    def __init__(self) -> None:
        self.oportunidades = RepositorioOportunidadesEmMemoria()
        self.processos = RepositorioProcessosEmMemoria()
        self.lembretes = RepositorioLembretesEmMemoria()
        self.contatos = RepositorioContatosEmMemoria()
        self.configuracoes = RepositorioConfiguracoesEmMemoria()
        self.execucoes = RepositorioExecucoesEmMemoria()
        self.cotacoes = RepositorioCotacoesEmMemoria()


class UnidadeDeTrabalhoEmMemoria:
    """Como a SQL: os repositórios só existem dentro de `with`."""

    _REPOSITORIOS = (
        "oportunidades", "processos", "lembretes", "contatos",
        "configuracoes", "execucoes", "cotacoes",
    )

    def __init__(self) -> None:
        self.direto = _Repositorios()
        self.commits = 0
        self.rollbacks = 0
        self._dentro = False
        self._instantaneo = self._copiar()

    def __getattr__(self, nome: str):
        if nome in UnidadeDeTrabalhoEmMemoria._REPOSITORIOS:
            if not self._dentro:
                raise RuntimeError(f"repositório usado fora de with: {nome}")
            return getattr(self.direto, nome)
        raise AttributeError(nome)

    def _copiar(self) -> dict:
        return {n: deepcopy(vars(getattr(self.direto, n))) for n in self._REPOSITORIOS}

    def commit(self) -> None:
        self.commits += 1
        self._instantaneo = self._copiar()

    def rollback(self) -> None:
        """Como o banco: descarta o que não foi confirmado desde o último commit."""
        self.rollbacks += 1
        for nome, estado in self._instantaneo.items():
            vars(getattr(self.direto, nome)).update(deepcopy(estado))

    def __enter__(self):
        if self._dentro:
            raise RuntimeError("unidade de trabalho já aberta")
        self._dentro = True
        return self

    def __exit__(self, tipo, erro, traco) -> None:
        try:
            if tipo is not None:
                self.rollback()
        finally:
            self._dentro = False


class FonteFalsa:
    def __init__(self, nome: str, brutas: list[OportunidadeBruta], erro: Exception | None = None):
        self.nome = nome
        self.brutas = brutas
        self.erro = erro

    def buscar(self, desde: date) -> list[OportunidadeBruta]:
        if self.erro is not None:
            raise self.erro
        return list(self.brutas)


class ClassificadorFalso:
    def __init__(self, respostas: dict[str, Classificacao | Exception]):
        self.respostas = respostas
        self.chamadas: list[tuple[OportunidadeBruta, Perfil, list[DescarteRecente]]] = []

    def classificar(self, bruta, perfil, descartes) -> Classificacao:
        self.chamadas.append((bruta, perfil, descartes))
        resposta = self.respostas[bruta.id_externo]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


class NotificadorFalso:
    def __init__(self) -> None:
        self.enviadas: list[tuple[str, str, str]] = []

    def enviar(self, titulo: str, corpo: str, url: str) -> int:
        self.enviadas.append((titulo, corpo, url))
        return 1


class RelogioFixo:
    def __init__(self, agora: datetime):
        self._agora = agora

    def agora(self) -> datetime:
        return self._agora


class ArmazenamentoArquivosEmMemoria:
    def __init__(self) -> None:
        self.arquivos: dict[str, bytes] = {}

    def salvar(self, nome: str, conteudo: bytes) -> str:
        chave = f"{len(self.arquivos) + 1}-{nome}"
        self.arquivos[chave] = conteudo
        return chave

    def abrir(self, chave: str) -> bytes:
        return self.arquivos[chave]
