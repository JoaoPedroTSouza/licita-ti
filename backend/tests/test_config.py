import pytest

from radar.config import Settings, validar_segredos
from radar.container import Container

SEGREDO = "s" * 32


def _settings(**kw) -> Settings:
    base = dict(_env_file=None, app_password="minha-senha", jwt_secret=SEGREDO,
                database_url="sqlite+pysqlite:///:memory:")
    return Settings(**{**base, **kw})


def test_segredos_validos_passam():
    validar_segredos(_settings())


@pytest.mark.parametrize("senha", ["", "troque-esta-senha"])
def test_senha_vazia_ou_padrao_impede_a_inicializacao(senha):
    with pytest.raises(ValueError, match="APP_PASSWORD"):
        validar_segredos(_settings(app_password=senha))


@pytest.mark.parametrize("segredo", ["", "troque-este-segredo", "s" * 31])
def test_jwt_secret_vazio_padrao_ou_curto_impede_a_inicializacao(segredo):
    with pytest.raises(ValueError, match="JWT_SECRET"):
        validar_segredos(_settings(jwt_secret=segredo))


def test_container_de_settings_valida_antes_de_montar():
    with pytest.raises(ValueError, match="APP_PASSWORD"):
        Container.de_settings(_settings(app_password="troque-esta-senha"))
