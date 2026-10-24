"""Formatos de entrada e saída da API. Datas saem em UTC ISO 8601; decimais saem como texto."""
from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from radar.application.painel import ItemParaFazer, PainelDoDia
from radar.application.portas import ExecucaoFonte
from radar.domain.dinheiro import Dinheiro, converter_para_brl
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import Oportunidade
from radar.domain.perfil import Ajustes, Perfil
from radar.domain.processo import Processo


def _utc(dt: datetime | None) -> datetime | None:
    return dt.astimezone(UTC) if dt else None


# ------------------------------------------------------------------- entrada

class LoginIn(BaseModel):
    senha: str


class DescartarIn(BaseModel):
    motivo: str | None = None


class PerfilDTO(BaseModel):
    texto: str
    faixa_min_brl: Decimal | None = None
    faixa_max_brl: Decimal | None = None


class AjustesDTO(BaseModel):
    limiar_alerta: int = Field(ge=0, le=100)
    horario_resumo: str
    avisos_prazo_dias: list[int]

    @field_validator("horario_resumo")
    @classmethod
    def _horario(cls, v: str) -> str:
        try:
            time.fromisoformat(v)
            if len(v) != 5:
                raise ValueError
        except ValueError:
            raise ValueError("horario_resumo deve estar no formato HH:MM")
        return v

    @field_validator("avisos_prazo_dias")
    @classmethod
    def _dias(cls, v: list[int]) -> list[int]:
        if any(d < 0 for d in v):
            raise ValueError("avisos_prazo_dias não aceita valores negativos")
        return v


# -------------------------------------------------------------------- saída

class TokenDTO(BaseModel):
    token: str


class ValorDTO(BaseModel):
    valor: Decimal
    moeda: str


def valor_dto(d: Dinheiro | None) -> ValorDTO | None:
    return ValorDTO(valor=d.valor, moeda=d.moeda) if d else None


class OportunidadeDTO(BaseModel):
    id: int
    titulo: str
    organizacao: str
    pais: str | None
    link: str
    prazo: datetime | None
    valor: ValorDTO | None
    valor_brl: Decimal | None
    nota: int | None
    resumo: str | None
    motivo: str | None
    pessoa_fisica: bool
    fonte: str
    status: str
    processo_id: int | None


class OportunidadeDetalheDTO(OportunidadeDTO):
    texto: str
    trecho_modalidade: str | None


def oportunidade_dto(op: Oportunidade, taxas: Mapping[str, Decimal]) -> OportunidadeDTO:
    return OportunidadeDTO(**_campos_oportunidade(op, taxas))


def oportunidade_detalhe_dto(
    op: Oportunidade, taxas: Mapping[str, Decimal]
) -> OportunidadeDetalheDTO:
    c = op.classificacao
    return OportunidadeDetalheDTO(
        **_campos_oportunidade(op, taxas),
        texto=op.bruta.texto, trecho_modalidade=c.trecho_modalidade if c else None,
    )


def _campos_oportunidade(op: Oportunidade, taxas: Mapping[str, Decimal]) -> dict:
    c = op.classificacao
    return dict(
        id=op.id, titulo=op.bruta.titulo, organizacao=op.bruta.organizacao,
        pais=op.bruta.pais, link=op.bruta.link, prazo=_utc(op.prazo),
        valor=valor_dto(op.valor),
        valor_brl=converter_para_brl(op.valor, taxas) if op.valor else None,
        nota=c.nota if c else None, resumo=c.resumo if c else None,
        motivo=c.motivo if c else None, pessoa_fisica=op.pessoa_fisica,
        fonte=op.bruta.fonte, status=op.status.value, processo_id=op.processo_id,
    )


class NotaDTO(BaseModel):
    texto: str
    criada_em: datetime


class ArquivoDTO(BaseModel):
    id: int
    nome: str
    tamanho: int
    enviado_em: datetime


class MudancaEtapaDTO(BaseModel):
    de: str | None
    para: str
    em: datetime


class LembreteDTO(BaseModel):
    id: int
    texto: str
    vence_em: datetime
    processo_id: int | None
    concluido: bool


def lembrete_dto(l: Lembrete) -> LembreteDTO:
    return LembreteDTO(
        id=l.id, texto=l.texto, vence_em=_utc(l.vence_em), processo_id=l.processo_id,
        concluido=l.concluido,
    )


class ProcessoDTO(BaseModel):
    id: int
    titulo: str
    organizacao: str | None
    etapa: str
    valor: ValorDTO | None
    valor_brl: Decimal | None
    prazo: datetime | None
    link: str | None
    oportunidade_id: int | None
    criado_em: datetime
    notas: list[NotaDTO]
    arquivos: list[ArquivoDTO]
    historico: list[MudancaEtapaDTO]
    contato_ids: list[int]
    lembretes: list[LembreteDTO]


def processo_dto(
    p: Processo, taxas: Mapping[str, Decimal], lembretes: list[Lembrete]
) -> ProcessoDTO:
    return ProcessoDTO(
        id=p.id, titulo=p.titulo, organizacao=p.organizacao, etapa=p.etapa.value,
        valor=valor_dto(p.valor),
        valor_brl=converter_para_brl(p.valor, taxas) if p.valor else None,
        prazo=_utc(p.prazo), link=p.link, oportunidade_id=p.oportunidade_id,
        criado_em=_utc(p.criado_em),
        notas=[NotaDTO(texto=n.texto, criada_em=_utc(n.criada_em)) for n in p.notas],
        arquivos=[
            ArquivoDTO(id=a.id, nome=a.nome, tamanho=a.tamanho, enviado_em=_utc(a.enviado_em))
            for a in p.arquivos
        ],
        historico=[
            MudancaEtapaDTO(de=m.de.value if m.de else None, para=m.para.value, em=_utc(m.em))
            for m in p.historico
        ],
        contato_ids=sorted(p.contato_ids),
        lembretes=[lembrete_dto(l) for l in lembretes],
    )


class ItemParaFazerDTO(BaseModel):
    tipo: str
    titulo: str
    quando: datetime | date | None
    ref_id: int
    processo_id: int | None


class ResumoFunilDTO(BaseModel):
    contagem: dict[str, int]
    valor_aberto_brl: Decimal
    sem_conversao: int


class PainelDTO(BaseModel):
    dia: date
    para_fazer: list[ItemParaFazerDTO]
    funil: ResumoFunilDTO
    melhores_novas: list[OportunidadeDTO]


def _item_dto(i: ItemParaFazer) -> ItemParaFazerDTO:
    quando = _utc(i.quando) if isinstance(i.quando, datetime) else i.quando
    return ItemParaFazerDTO(
        tipo=i.tipo, titulo=i.titulo, quando=quando, ref_id=i.ref_id, processo_id=i.processo_id
    )


def painel_dto(p: PainelDoDia, taxas: Mapping[str, Decimal]) -> PainelDTO:
    return PainelDTO(
        dia=p.dia,
        para_fazer=[_item_dto(i) for i in p.para_fazer],
        funil=ResumoFunilDTO(
            contagem={e.value: n for e, n in p.funil.contagem.items()},
            valor_aberto_brl=p.funil.valor_aberto_brl, sem_conversao=p.funil.sem_conversao,
        ),
        melhores_novas=[oportunidade_dto(o, taxas) for o in p.melhores_novas],
    )


def perfil_dto(p: Perfil) -> PerfilDTO:
    return PerfilDTO(texto=p.texto, faixa_min_brl=p.faixa_min_brl, faixa_max_brl=p.faixa_max_brl)


def ajustes_dto(a: Ajustes) -> AjustesDTO:
    return AjustesDTO(
        limiar_alerta=a.limiar_alerta, horario_resumo=a.horario_resumo.strftime("%H:%M"),
        avisos_prazo_dias=list(a.avisos_prazo_dias),
    )


class ExecucaoFonteDTO(BaseModel):
    fonte: str
    finalizada_em: datetime
    recebidas: int
    novas: int
    erro: str | None


class StatusDTO(BaseModel):
    ia_configurada: bool
    push_configurado: bool
    fontes: list[ExecucaoFonteDTO]


def execucao_dto(e: ExecucaoFonte) -> ExecucaoFonteDTO:
    return ExecucaoFonteDTO(
        fonte=e.fonte, finalizada_em=_utc(e.finalizada_em), recebidas=e.recebidas,
        novas=e.novas, erro=e.erro,
    )
