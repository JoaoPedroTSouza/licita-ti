"""Esquema relacional do Radar e tipos de coluna que preservam o domínio."""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON, Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, MetaData,
    Numeric, String, Table, Text, TypeDecorator,
)


class DataHoraUtc(TypeDecorator):
    """Datetime sempre aware: grava em UTC e devolve com UTC (SQLite perde o fuso)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=UTC)
        return valor.astimezone(UTC)

    def process_result_value(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        if valor.tzinfo is None:
            return valor.replace(tzinfo=UTC)
        return valor.astimezone(UTC)


class NumericoExato(TypeDecorator):
    """Numeric(p, e); no SQLite vira texto para não perder precisão nem gerar avisos."""

    impl = Numeric
    cache_ok = True

    def __init__(self, precisao: int = 14, escala: int = 2) -> None:
        super().__init__()
        self.precisao, self.escala = precisao, escala

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(40))
        return dialect.type_descriptor(Numeric(self.precisao, self.escala))

    def process_bind_param(self, valor: Decimal | None, dialect):
        if valor is None:
            return None
        return str(valor) if dialect.name == "sqlite" else valor

    def process_result_value(self, valor, dialect):
        return None if valor is None else Decimal(str(valor))


metadata = MetaData()

oportunidades = Table(
    "oportunidades", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chave", String(64), nullable=False, unique=True, index=True),
    Column("status", String(30), nullable=False, index=True),
    Column("coletada_em", DataHoraUtc, nullable=False),
    Column("fonte", String(100), nullable=False),
    Column("id_externo", String(300), nullable=False),
    Column("titulo", Text, nullable=False),
    Column("organizacao", Text, nullable=False),
    Column("link", Text, nullable=False),
    Column("texto", Text, nullable=False),
    Column("pais", String(100)),
    Column("prazo", DataHoraUtc),
    Column("valor_valor", NumericoExato(14, 2)),
    Column("valor_moeda", String(3)),
    Column("publicada_em", DataHoraUtc),
    Column("idioma", String(20)),
    Column("cls_relevante", Boolean),
    Column("cls_nota", Integer),
    Column("cls_resumo", Text),
    Column("cls_modalidade", String(30)),
    Column("cls_trecho_modalidade", Text),
    Column("cls_idioma", String(20)),
    Column("cls_tipo_contratacao", String(30)),
    Column("cls_motivo", Text),
    Column("cls_prazo", DataHoraUtc),
    Column("cls_valor_valor", NumericoExato(14, 2)),
    Column("cls_valor_moeda", String(3)),
    Column("motivo_auto", String(30)),
    Column("motivo_usuario", Text),
    Column("processo_id", Integer),
)

processos = Table(
    "processos", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("titulo", Text, nullable=False),
    Column("organizacao", Text),
    Column("etapa", String(30), nullable=False),
    Column("criado_em", DataHoraUtc, nullable=False),
    Column("oportunidade_id", Integer),
    Column("valor_valor", NumericoExato(14, 2)),
    Column("valor_moeda", String(3)),
    Column("prazo", DataHoraUtc),
    Column("link", Text),
    Column("avisos_prazo_enviados", JSON, nullable=False, default=list),
)

processo_notas = Table(
    "processo_notas", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("processo_id", ForeignKey("processos.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("texto", Text, nullable=False),
    Column("criada_em", DataHoraUtc, nullable=False),
)

processo_arquivos = Table(
    "processo_arquivos", metadata,
    Column("processo_id", ForeignKey("processos.id", ondelete="CASCADE"), primary_key=True),
    Column("id", Integer, primary_key=True, autoincrement=False),  # id local ao processo
    Column("nome", Text, nullable=False),
    Column("chave", Text, nullable=False),
    Column("tamanho", Integer, nullable=False),
    Column("enviado_em", DataHoraUtc, nullable=False),
)

processo_historico = Table(
    "processo_historico", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("processo_id", ForeignKey("processos.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("de", String(30)),
    Column("para", String(30), nullable=False),
    Column("em", DataHoraUtc, nullable=False),
)

processo_contatos = Table(
    "processo_contatos", metadata,
    Column("processo_id", Integer, primary_key=True),
    Column("contato_id", Integer, primary_key=True),
    Index("ix_processo_contatos_contato", "contato_id"),
)

lembretes = Table(
    "lembretes", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("texto", Text, nullable=False),
    Column("vence_em", DataHoraUtc, nullable=False),
    Column("processo_id", Integer, index=True),
    Column("concluido", Boolean, nullable=False, default=False),
)

contatos = Table(
    "contatos", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nome", Text, nullable=False),
    Column("organizacao", Text),
    Column("como_conheceu", Text),
    Column("ultimo_contato", Date),
    Column("frequencia_dias", Integer),
)

configuracoes = Table(
    "configuracoes", metadata,
    Column("chave", String(200), primary_key=True),
    Column("valor", JSON, nullable=False),
)

execucoes_fonte = Table(
    "execucoes_fonte", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fonte", String(100), nullable=False, index=True),
    Column("iniciada_em", DataHoraUtc, nullable=False),
    Column("finalizada_em", DataHoraUtc, nullable=False),
    Column("recebidas", Integer, nullable=False),
    Column("novas", Integer, nullable=False),
    Column("erro", Text),
)

cotacoes = Table(
    "cotacoes", metadata,
    Column("moeda", String(3), primary_key=True),
    Column("dia", Date, primary_key=True),
    Column("valor", NumericoExato(18, 6), nullable=False),
)

inscricoes_push = Table(
    "inscricoes_push", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("endpoint", String(1000), nullable=False, unique=True),
    Column("p256dh", Text, nullable=False),
    Column("auth", Text, nullable=False),
    Column("user_agent", Text),
    Column("criado_em", DataHoraUtc, nullable=False),
)
