from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


STATUS_VALIDOS = ("novo", "analisando", "participando", "descartado")


class Edital(Base):
    __tablename__ = "editais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_controle_pncp: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    # Identificação no PNCP
    cnpj: Mapped[str] = mapped_column(String(20))
    ano: Mapped[int] = mapped_column(Integer)
    sequencial: Mapped[int] = mapped_column(Integer)
    numero_compra: Mapped[str | None] = mapped_column(String(80))
    processo: Mapped[str | None] = mapped_column(String(120))

    # Conteúdo
    objeto: Mapped[str] = mapped_column(Text)
    informacao_complementar: Mapped[str | None] = mapped_column(Text)
    orgao: Mapped[str | None] = mapped_column(String(300))
    unidade: Mapped[str | None] = mapped_column(String(300))
    uf: Mapped[str | None] = mapped_column(String(2), index=True)
    municipio: Mapped[str | None] = mapped_column(String(120))
    modalidade_id: Mapped[int | None] = mapped_column(Integer)
    modalidade_nome: Mapped[str | None] = mapped_column(String(80))
    modo_disputa: Mapped[str | None] = mapped_column(String(80))
    situacao: Mapped[str | None] = mapped_column(String(80))
    srp: Mapped[bool | None] = mapped_column(Boolean)
    valor_estimado: Mapped[float | None] = mapped_column(Float)

    data_publicacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    data_abertura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_encerramento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    link_origem: Mapped[str | None] = mapped_column(Text)
    link_pncp: Mapped[str | None] = mapped_column(Text)

    # Filtro por palavras-chave
    keyword_score: Mapped[int] = mapped_column(Integer, default=0)
    keywords_encontradas: Mapped[list] = mapped_column(JSON, default=list)

    # Classificação por IA
    ia_processado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ia_relevante: Mapped[bool | None] = mapped_column(Boolean, index=True)
    ia_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    ia_categoria: Mapped[str | None] = mapped_column(String(80))
    ia_resumo: Mapped[str | None] = mapped_column(Text)
    ia_motivo: Mapped[str | None] = mapped_column(Text)
    ia_exigencias: Mapped[list] = mapped_column(JSON, default=list)

    # Acompanhamento (uso pessoal → status direto no edital)
    status: Mapped[str] = mapped_column(String(20), default="novo", index=True)
    favorito: Mapped[bool] = mapped_column(Boolean, default=False)
    notas: Mapped[str | None] = mapped_column(Text)

    # Controle de notificações
    notificado: Mapped[bool] = mapped_column(Boolean, default=False)
    lembrete_enviado: Mapped[bool] = mapped_column(Boolean, default=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(String(200))
    auth: Mapped[str] = mapped_column(String(100))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Configuracao(Base):
    """Preferências editáveis pelo app (chave → valor JSON)."""

    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[dict | list | str | int | None] = mapped_column(JSON)


class ExecucaoColeta(Base):
    __tablename__ = "execucoes_coleta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_referencia: Mapped[str | None] = mapped_column(String(10))
    recebidos: Mapped[int] = mapped_column(Integer, default=0)
    novos: Mapped[int] = mapped_column(Integer, default=0)
    candidatos: Mapped[int] = mapped_column(Integer, default=0)
    relevantes: Mapped[int] = mapped_column(Integer, default=0)
    notificados: Mapped[int] = mapped_column(Integer, default=0)
    erro: Mapped[str | None] = mapped_column(Text)
