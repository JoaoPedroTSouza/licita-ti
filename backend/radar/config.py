"""Configuração do Radar, lida do ambiente (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco
    database_url: str = "postgresql+psycopg://radar:radar@localhost:5432/radar"

    # Autenticação (uso pessoal: um único usuário)
    app_password: str = "troque-esta-senha"
    jwt_secret: str = "troque-este-segredo"
    jwt_expire_days: int = 30

    # IA
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-5-5"
    llm_max_por_execucao: int = 60  # teto de chamadas por coleta (controle de custo)

    # Fontes (ReliefWeb: não implementado; ver docs/fontes/reliefweb.md)
    reliefweb_appname: str = ""

    # Web Push
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:voce@exemplo.com"

    # Agendamento (fuso de Brasília)
    timezone: str = "America/Sao_Paulo"
    coleta_horarios: str = "7,12,18"  # horas do dia

    # URL pública do PWA (links das notificações)
    app_url: str = "http://localhost:3000"

    # Arquivos anexados
    arquivos_dir: str = "/data/arquivos"
    arquivo_max_mb: int = 20


SENHA_PADRAO = "troque-esta-senha"
SEGREDO_PADRAO = "troque-este-segredo"
MIN_JWT_SECRET = 32


def validar_segredos(settings: Settings) -> None:
    """Impede subir a API ou o worker com senha/segredo vazios, de exemplo ou fracos."""
    if not settings.app_password or settings.app_password == SENHA_PADRAO:
        raise ValueError("APP_PASSWORD vazio ou com o valor de exemplo: defina uma senha no .env")
    s = settings.jwt_secret
    if not s or s == SEGREDO_PADRAO or len(s) < MIN_JWT_SECRET:
        raise ValueError(
            f"JWT_SECRET vazio, de exemplo ou com menos de {MIN_JWT_SECRET} caracteres: gere com "
            '`python -c "import secrets; print(secrets.token_urlsafe(48))"`'
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
