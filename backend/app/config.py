from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco
    database_url: str = "postgresql+psycopg://licita:licita@localhost:5432/licita"

    # Autenticação (uso pessoal: um único usuário)
    app_password: str = "troque-esta-senha"
    jwt_secret: str = "troque-este-segredo"
    jwt_expire_days: int = 30

    # CORS (apenas se o front não usar o proxy do Next)
    cors_origins: str = "http://localhost:3000"

    # PNCP
    pncp_base_url: str = "https://pncp.gov.br/api/consulta"
    pncp_page_size: int = 50  # máximo aceito pelo endpoint de contratações

    # IA
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_max_por_execucao: int = 60  # teto de chamadas por coleta (controle de custo)

    # Web Push (gere com: python -m app.scripts.gen_vapid)
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:voce@exemplo.com"

    # Agendamento (fuso de Brasília)
    timezone: str = "America/Sao_Paulo"
    coleta_horarios: str = "7,12,18"  # horas do dia
    lembrete_horas_antes: int = 48

    # URL pública do PWA (usada nos links das notificações)
    app_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
