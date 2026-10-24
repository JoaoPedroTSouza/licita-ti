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

    # Fontes (ReliefWeb exige appname aprovado; vazio = fonte desativada)
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
