"""Container de teste: SQLite em memória, dublês das portas e configurações fixas."""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from radar.config import Settings
from radar.container import Container
from radar.domain.dinheiro import Dinheiro
from radar.domain.oportunidade import (
    Classificacao, Modalidade, Oportunidade, OportunidadeBruta, StatusOportunidade,
    TipoContratacao,
)
from radar.infrastructure.arquivos.disco import ArmazenamentoEmDisco
from radar.infrastructure.db.repositorios import criar_engine, criar_tabelas
from radar.infrastructure.push.webpush import NotificadorWebPush
from radar.interfaces.http.app import criar_app
from tests.fakes import RelogioFixo

SENHA = "senha-de-teste"
AGORA = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


class CotacoesFalsas:
    def cotacao(self, moeda, ate):
        return None


class ClassificadorMudo:
    def classificar(self, bruta, perfil, descartes):
        raise AssertionError("não deveria classificar")


def montar_container(tmp_path, *, com_ia: bool = True, enviar=None) -> Container:
    settings = Settings(
        _env_file=None, app_password=SENHA, jwt_secret="segredo-de-teste",
        database_url="sqlite+pysqlite:///:memory:", anthropic_api_key="x" if com_ia else "",
    )
    engine = criar_engine(settings.database_url)
    criar_tabelas(engine)
    fabrica = sessionmaker(engine, expire_on_commit=False)
    notificador = NotificadorWebPush(
        fabrica, "chave-vapid", "mailto:t@t.t", enviar=enviar or (lambda **kw: None)
    )
    return Container(
        settings=settings, fabrica_sessao=fabrica, relogio=RelogioFixo(AGORA),
        notificador=notificador, classificador=ClassificadorMudo() if com_ia else None,
        fontes=[], armazenamento=ArmazenamentoEmDisco(tmp_path), fonte_cotacoes=CotacoesFalsas(),
    )


def semear(container: Container, titulo: str, nota: int, *, status=StatusOportunidade.NOVA,
           pessoa_fisica: bool = False, valor: Dinheiro | None = None,
           prazo: datetime | None = None) -> int:
    bruta = OportunidadeBruta(
        fonte="teste", id_externo=titulo, titulo=titulo, organizacao="Org",
        link="https://x/" + titulo, texto=f"texto de {titulo}", pais="BR", prazo=prazo,
        valor=valor,
    )
    classificacao = Classificacao(
        relevante=True, nota=nota, resumo=f"resumo {titulo}", modalidade=Modalidade.REMOTO_TOTAL,
        trecho_modalidade="trabalho remoto", idioma="pt",
        tipo_contratacao=TipoContratacao.PESSOA_FISICA if pessoa_fisica else TipoContratacao.EMPRESA,
        motivo="encaixa no perfil",
    )
    with container.uow() as uow:
        op = uow.oportunidades.adicionar(
            Oportunidade(None, bruta, AGORA, status=status, classificacao=classificacao)
        )
        uow.commit()
        return op.id


def _logado(container) -> TestClient:
    c = TestClient(criar_app(container))
    token = c.post("/api/auth/login", json={"senha": SENHA}).json()["token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.container = container
    return c


@pytest.fixture
def container(tmp_path):
    return montar_container(tmp_path)


@pytest.fixture
def cliente(container):
    return TestClient(criar_app(container))


@pytest.fixture
def cliente_logado(container):
    return _logado(container)


@pytest.fixture
def cliente_logado_sem_classificador(tmp_path):
    return _logado(montar_container(tmp_path, com_ia=False))
