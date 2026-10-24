"""Repositórios SQL e unidade de trabalho; convertem linhas em entidades do domínio."""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Engine, case, create_engine, delete, func, insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from radar.application.portas import DescarteRecente, ExecucaoFonte
from radar.domain.contato import Contato
from radar.domain.dinheiro import Dinheiro
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import (
    Classificacao, Modalidade, MotivoDescarteAuto, Oportunidade, OportunidadeBruta,
    StatusOportunidade, TipoContratacao,
)
from radar.domain.perfil import Ajustes, Perfil
from radar.domain.processo import Arquivo, Etapa, MudancaEtapa, Nota, Processo
from radar.infrastructure.db import tabelas as t


def criar_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        opcoes: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url or url.endswith("://"):
            opcoes["poolclass"] = StaticPool
        return create_engine(url, **opcoes)
    return create_engine(url, pool_pre_ping=True)


def criar_tabelas(engine: Engine) -> None:
    t.metadata.create_all(engine)


def _dinheiro(valor: Decimal | None, moeda: str | None) -> Dinheiro | None:
    return Dinheiro(valor, moeda) if valor is not None and moeda else None


def _par(d: Dinheiro | None) -> tuple[Decimal | None, str | None]:
    return (d.valor, d.moeda) if d else (None, None)


# ---------------------------------------------------------------- oportunidades

def _oportunidade_para_linha(op: Oportunidade) -> dict:
    b, c = op.bruta, op.classificacao
    valor, moeda = _par(b.valor)
    linha = {
        "chave": b.chave_deduplicacao(), "status": op.status.value, "coletada_em": op.coletada_em,
        "fonte": b.fonte, "id_externo": b.id_externo, "titulo": b.titulo,
        "organizacao": b.organizacao, "link": b.link, "texto": b.texto, "pais": b.pais,
        "prazo": b.prazo, "valor_valor": valor, "valor_moeda": moeda,
        "publicada_em": b.publicada_em, "idioma": b.idioma,
        "motivo_auto": op.motivo_auto.value if op.motivo_auto else None,
        "motivo_usuario": op.motivo_usuario, "processo_id": op.processo_id,
        "cls_relevante": None, "cls_nota": None, "cls_resumo": None, "cls_modalidade": None,
        "cls_trecho_modalidade": None, "cls_idioma": None, "cls_tipo_contratacao": None,
        "cls_motivo": None, "cls_prazo": None, "cls_valor_valor": None, "cls_valor_moeda": None,
    }
    if c is not None:
        cv, cm = _par(c.valor)
        linha.update(
            cls_relevante=c.relevante, cls_nota=c.nota, cls_resumo=c.resumo,
            cls_modalidade=c.modalidade.value, cls_trecho_modalidade=c.trecho_modalidade,
            cls_idioma=c.idioma, cls_tipo_contratacao=c.tipo_contratacao.value,
            cls_motivo=c.motivo, cls_prazo=c.prazo, cls_valor_valor=cv, cls_valor_moeda=cm,
        )
    return linha


def _oportunidade_para_dominio(r: RowMapping) -> Oportunidade:
    bruta = OportunidadeBruta(
        fonte=r["fonte"], id_externo=r["id_externo"], titulo=r["titulo"],
        organizacao=r["organizacao"], link=r["link"], texto=r["texto"], pais=r["pais"],
        prazo=r["prazo"], valor=_dinheiro(r["valor_valor"], r["valor_moeda"]),
        publicada_em=r["publicada_em"], idioma=r["idioma"],
    )
    classificacao = None
    if r["cls_relevante"] is not None:
        classificacao = Classificacao(
            relevante=r["cls_relevante"], nota=r["cls_nota"], resumo=r["cls_resumo"],
            modalidade=Modalidade(r["cls_modalidade"]),
            trecho_modalidade=r["cls_trecho_modalidade"], idioma=r["cls_idioma"],
            tipo_contratacao=TipoContratacao(r["cls_tipo_contratacao"]), motivo=r["cls_motivo"],
            prazo=r["cls_prazo"], valor=_dinheiro(r["cls_valor_valor"], r["cls_valor_moeda"]),
        )
    return Oportunidade(
        id=r["id"], bruta=bruta, coletada_em=r["coletada_em"],
        status=StatusOportunidade(r["status"]), classificacao=classificacao,
        motivo_auto=MotivoDescarteAuto(r["motivo_auto"]) if r["motivo_auto"] else None,
        motivo_usuario=r["motivo_usuario"], processo_id=r["processo_id"],
    )


class RepositorioOportunidadesSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def adicionar(self, op: Oportunidade) -> Oportunidade:
        op.id = self._s.execute(
            insert(t.oportunidades).values(**_oportunidade_para_linha(op))
        ).inserted_primary_key[0]
        return op

    def obter(self, id: int) -> Oportunidade | None:
        r = self._s.execute(select(t.oportunidades).where(t.oportunidades.c.id == id)).mappings().first()
        return _oportunidade_para_dominio(r) if r else None

    def salvar(self, op: Oportunidade) -> None:
        self._s.execute(
            update(t.oportunidades).where(t.oportunidades.c.id == op.id)
            .values(**_oportunidade_para_linha(op))
        )

    def existe_chave(self, chave: str) -> bool:
        return self._s.execute(
            select(t.oportunidades.c.id).where(t.oportunidades.c.chave == chave).limit(1)
        ).first() is not None

    def pendentes(self, limite: int) -> list[Oportunidade]:
        q = (select(t.oportunidades).where(t.oportunidades.c.status == StatusOportunidade.PENDENTE.value)
             .order_by(t.oportunidades.c.id).limit(limite))
        return [_oportunidade_para_dominio(r) for r in self._s.execute(q).mappings()]

    def listar(self, status: StatusOportunidade, limite: int | None = None) -> list[Oportunidade]:
        o = t.oportunidades.c
        prazo = func.coalesce(o.cls_prazo, o.prazo)
        q = (select(t.oportunidades).where(o.status == status.value)
             .order_by(func.coalesce(o.cls_nota, 0).desc(), case((prazo.is_(None), 1), else_=0), prazo, o.id))
        if limite is not None:
            q = q.limit(limite)
        return [_oportunidade_para_dominio(r) for r in self._s.execute(q).mappings()]

    def contar_novas_desde(self, desde: datetime) -> int:
        o = t.oportunidades.c
        return self._s.execute(
            select(func.count()).select_from(t.oportunidades)
            .where(o.status == StatusOportunidade.NOVA.value, o.coletada_em >= desde)
        ).scalar_one()

    def descartes_recentes(self, limite: int = 20) -> list[DescarteRecente]:
        o = t.oportunidades.c
        q = (select(o.titulo, o.motivo_usuario)
             .where(o.status == StatusOportunidade.DESCARTADA.value,
                    o.motivo_usuario.is_not(None), o.motivo_usuario != "")
             .order_by(o.id.desc()).limit(limite))
        return [DescarteRecente(titulo, motivo) for titulo, motivo in self._s.execute(q)]


# -------------------------------------------------------------------- processos

class RepositorioProcessosSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    @staticmethod
    def _linha(p: Processo) -> dict:
        valor, moeda = _par(p.valor)
        return {
            "titulo": p.titulo, "organizacao": p.organizacao, "etapa": p.etapa.value,
            "criado_em": p.criado_em, "oportunidade_id": p.oportunidade_id,
            "valor_valor": valor, "valor_moeda": moeda, "prazo": p.prazo, "link": p.link,
            "avisos_prazo_enviados": sorted(p.avisos_prazo_enviados),
        }

    def _gravar_filhos(self, p: Processo) -> None:
        s, pid = self._s, p.id
        for tabela in (t.processo_notas, t.processo_historico, t.processo_arquivos):
            s.execute(delete(tabela).where(tabela.c.processo_id == pid))
        s.execute(delete(t.processo_contatos).where(t.processo_contatos.c.processo_id == pid))
        if p.notas:
            s.execute(insert(t.processo_notas), [
                {"processo_id": pid, "texto": n.texto, "criada_em": n.criada_em} for n in p.notas])
        if p.historico:
            s.execute(insert(t.processo_historico), [
                {"processo_id": pid, "de": m.de.value if m.de else None,
                 "para": m.para.value, "em": m.em} for m in p.historico])
        proximo = max((a.id or 0 for a in p.arquivos), default=0) + 1
        for a in p.arquivos:
            if a.id is None:
                a.id, proximo = proximo, proximo + 1
        if p.arquivos:
            s.execute(insert(t.processo_arquivos), [
                {"processo_id": pid, "id": a.id, "nome": a.nome, "chave": a.chave,
                 "tamanho": a.tamanho, "enviado_em": a.enviado_em} for a in p.arquivos])
        if p.contato_ids:
            s.execute(insert(t.processo_contatos), [
                {"processo_id": pid, "contato_id": c} for c in sorted(p.contato_ids)])

    def _para_dominio(self, r: RowMapping) -> Processo:
        s, pid = self._s, r["id"]
        notas = [Nota(x["texto"], x["criada_em"]) for x in s.execute(
            select(t.processo_notas).where(t.processo_notas.c.processo_id == pid)
            .order_by(t.processo_notas.c.id)).mappings()]
        arquivos = [Arquivo(x["id"], x["nome"], x["chave"], x["tamanho"], x["enviado_em"])
                    for x in s.execute(
                        select(t.processo_arquivos).where(t.processo_arquivos.c.processo_id == pid)
                        .order_by(t.processo_arquivos.c.id)).mappings()]
        historico = [MudancaEtapa(Etapa(x["de"]) if x["de"] else None, Etapa(x["para"]), x["em"])
                     for x in s.execute(
                         select(t.processo_historico).where(t.processo_historico.c.processo_id == pid)
                         .order_by(t.processo_historico.c.id)).mappings()]
        contatos = set(s.execute(
            select(t.processo_contatos.c.contato_id).where(t.processo_contatos.c.processo_id == pid)
        ).scalars())
        return Processo(
            id=pid, titulo=r["titulo"], organizacao=r["organizacao"], etapa=Etapa(r["etapa"]),
            criado_em=r["criado_em"], oportunidade_id=r["oportunidade_id"],
            valor=_dinheiro(r["valor_valor"], r["valor_moeda"]), prazo=r["prazo"], link=r["link"],
            notas=notas, arquivos=arquivos, historico=historico, contato_ids=contatos,
            avisos_prazo_enviados=set(r["avisos_prazo_enviados"] or []),
        )

    def adicionar(self, processo: Processo) -> Processo:
        processo.id = self._s.execute(
            insert(t.processos).values(**self._linha(processo))).inserted_primary_key[0]
        self._gravar_filhos(processo)
        return processo

    def obter(self, id: int) -> Processo | None:
        r = self._s.execute(select(t.processos).where(t.processos.c.id == id)).mappings().first()
        return self._para_dominio(r) if r else None

    def salvar(self, processo: Processo) -> None:
        self._s.execute(
            update(t.processos).where(t.processos.c.id == processo.id).values(**self._linha(processo)))
        self._gravar_filhos(processo)

    def listar(self) -> list[Processo]:
        rows = self._s.execute(select(t.processos).order_by(t.processos.c.id)).mappings().all()
        return [self._para_dominio(r) for r in rows]


# -------------------------------------------------------------------- lembretes

def _lembrete_para_dominio(r: RowMapping) -> Lembrete:
    return Lembrete(r["id"], r["texto"], r["vence_em"], r["processo_id"], r["concluido"])


class RepositorioLembretesSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    @staticmethod
    def _linha(x: Lembrete) -> dict:
        return {"texto": x.texto, "vence_em": x.vence_em, "processo_id": x.processo_id,
                "concluido": x.concluido}

    def adicionar(self, lembrete: Lembrete) -> Lembrete:
        lembrete.id = self._s.execute(
            insert(t.lembretes).values(**self._linha(lembrete))).inserted_primary_key[0]
        return lembrete

    def obter(self, id: int) -> Lembrete | None:
        r = self._s.execute(select(t.lembretes).where(t.lembretes.c.id == id)).mappings().first()
        return _lembrete_para_dominio(r) if r else None

    def salvar(self, lembrete: Lembrete) -> None:
        self._s.execute(
            update(t.lembretes).where(t.lembretes.c.id == lembrete.id).values(**self._linha(lembrete)))

    def remover(self, id: int) -> None:
        self._s.execute(delete(t.lembretes).where(t.lembretes.c.id == id))

    def nao_concluidos(self) -> list[Lembrete]:
        q = select(t.lembretes).where(t.lembretes.c.concluido.is_(False)).order_by(t.lembretes.c.id)
        return [_lembrete_para_dominio(r) for r in self._s.execute(q).mappings()]

    def do_processo(self, processo_id: int) -> list[Lembrete]:
        q = select(t.lembretes).where(t.lembretes.c.processo_id == processo_id).order_by(t.lembretes.c.id)
        return [_lembrete_para_dominio(r) for r in self._s.execute(q).mappings()]


# --------------------------------------------------------------------- contatos

class RepositorioContatosSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    @staticmethod
    def _linha(c: Contato) -> dict:
        return {"nome": c.nome, "organizacao": c.organizacao, "como_conheceu": c.como_conheceu,
                "ultimo_contato": c.ultimo_contato, "frequencia_dias": c.frequencia_dias}

    def _gravar_vinculos(self, c: Contato) -> None:
        pc = t.processo_contatos
        self._s.execute(delete(pc).where(pc.c.contato_id == c.id))
        if c.processo_ids:
            self._s.execute(insert(pc), [
                {"processo_id": p, "contato_id": c.id} for p in sorted(c.processo_ids)])

    def _para_dominio(self, r: RowMapping) -> Contato:
        pc = t.processo_contatos
        vinculos = set(self._s.execute(select(pc.c.processo_id).where(pc.c.contato_id == r["id"])).scalars())
        return Contato(r["id"], r["nome"], r["organizacao"], r["como_conheceu"],
                       r["ultimo_contato"], r["frequencia_dias"], vinculos)

    def adicionar(self, contato: Contato) -> Contato:
        contato.id = self._s.execute(
            insert(t.contatos).values(**self._linha(contato))).inserted_primary_key[0]
        self._gravar_vinculos(contato)
        return contato

    def obter(self, id: int) -> Contato | None:
        r = self._s.execute(select(t.contatos).where(t.contatos.c.id == id)).mappings().first()
        return self._para_dominio(r) if r else None

    def salvar(self, contato: Contato) -> None:
        self._s.execute(
            update(t.contatos).where(t.contatos.c.id == contato.id).values(**self._linha(contato)))
        self._gravar_vinculos(contato)

    def listar(self) -> list[Contato]:
        rows = self._s.execute(select(t.contatos).order_by(t.contatos.c.id)).mappings().all()
        return [self._para_dominio(r) for r in rows]


# ---------------------------------------------------------------- configurações

_PREFIXO_ESTADO = "estado:"


def _decimal_json(d: Decimal | None) -> str | None:
    return None if d is None else str(d)


def _decimal_ou_none(texto: str | None) -> Decimal | None:
    return None if texto is None else Decimal(texto)


class RepositorioConfiguracoesSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def _ler(self, chave: str):
        return self._s.execute(
            select(t.configuracoes.c.valor).where(t.configuracoes.c.chave == chave)
        ).scalar_one_or_none()

    def _gravar(self, chave: str, valor) -> None:
        c = t.configuracoes.c
        if self._s.execute(select(c.chave).where(c.chave == chave)).first():
            self._s.execute(update(t.configuracoes).where(c.chave == chave).values(valor=valor))
        else:
            self._s.execute(insert(t.configuracoes).values(chave=chave, valor=valor))

    def perfil(self) -> Perfil:
        d = self._ler("perfil")
        if d is None:
            return Perfil()
        return Perfil(d["texto"], _decimal_ou_none(d["faixa_min_brl"]), _decimal_ou_none(d["faixa_max_brl"]))

    def salvar_perfil(self, perfil: Perfil) -> None:
        self._gravar("perfil", {
            "texto": perfil.texto, "faixa_min_brl": _decimal_json(perfil.faixa_min_brl),
            "faixa_max_brl": _decimal_json(perfil.faixa_max_brl)})

    def ajustes(self) -> Ajustes:
        d = self._ler("ajustes")
        if d is None:
            return Ajustes()
        return Ajustes(d["limiar_alerta"], time.fromisoformat(d["horario_resumo"]),
                       tuple(d["avisos_prazo_dias"]))

    def salvar_ajustes(self, ajustes: Ajustes) -> None:
        self._gravar("ajustes", {
            "limiar_alerta": ajustes.limiar_alerta,
            "horario_resumo": ajustes.horario_resumo.isoformat(),
            "avisos_prazo_dias": list(ajustes.avisos_prazo_dias)})

    def obter_estado(self, chave: str) -> str | None:
        return self._ler(_PREFIXO_ESTADO + chave)

    def salvar_estado(self, chave: str, valor: str) -> None:
        self._gravar(_PREFIXO_ESTADO + chave, valor)


# ------------------------------------------------------------ execuções, cotações

class RepositorioExecucoesSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def registrar(self, execucao: ExecucaoFonte) -> None:
        self._s.execute(insert(t.execucoes_fonte).values(
            fonte=execucao.fonte, iniciada_em=execucao.iniciada_em,
            finalizada_em=execucao.finalizada_em, recebidas=execucao.recebidas,
            novas=execucao.novas, erro=execucao.erro))

    def ultimas_por_fonte(self) -> list[ExecucaoFonte]:
        e = t.execucoes_fonte.c
        ids = (select(func.max(e.id).label("ultima"), func.min(e.id).label("primeira"))
               .group_by(e.fonte).subquery())
        q = select(t.execucoes_fonte).join(ids, e.id == ids.c.ultima).order_by(ids.c.primeira)
        return [ExecucaoFonte(r["fonte"], r["iniciada_em"], r["finalizada_em"],
                              r["recebidas"], r["novas"], r["erro"])
                for r in self._s.execute(q).mappings()]


class RepositorioCotacoesSql:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def salvar(self, moeda: str, dia: date, valor: Decimal) -> None:
        c = t.cotacoes.c
        if self._s.execute(select(c.moeda).where(c.moeda == moeda, c.dia == dia)).first():
            self._s.execute(update(t.cotacoes).where(c.moeda == moeda, c.dia == dia).values(valor=valor))
        else:
            self._s.execute(insert(t.cotacoes).values(moeda=moeda, dia=dia, valor=valor))

    def mais_recentes(self) -> dict[str, Decimal]:
        c = t.cotacoes.c
        ultimo = select(c.moeda, func.max(c.dia).label("dia")).group_by(c.moeda).subquery()
        q = select(c.moeda, c.valor).join(ultimo, (c.moeda == ultimo.c.moeda) & (c.dia == ultimo.c.dia))
        return {moeda: valor for moeda, valor in self._s.execute(q)}


# ------------------------------------------------------------ unidade de trabalho

class UnidadeDeTrabalhoSql:
    """Abre uma sessão nova a cada `with`; commit pode ser chamado várias vezes dentro dele."""

    def __init__(self, fabrica_sessao: sessionmaker) -> None:
        self._fabrica = fabrica_sessao
        self._sessao: Session | None = None

    def __enter__(self):
        self._sessao = s = self._fabrica()
        self.oportunidades = RepositorioOportunidadesSql(s)
        self.processos = RepositorioProcessosSql(s)
        self.lembretes = RepositorioLembretesSql(s)
        self.contatos = RepositorioContatosSql(s)
        self.configuracoes = RepositorioConfiguracoesSql(s)
        self.execucoes = RepositorioExecucoesSql(s)
        self.cotacoes = RepositorioCotacoesSql(s)
        return self

    def __exit__(self, tipo, erro, traco) -> None:
        try:
            if tipo is not None:
                self._sessao.rollback()
        finally:
            self._sessao.close()
            self._sessao = None

    def commit(self) -> None:
        self._sessao.commit()

    def rollback(self) -> None:
        self._sessao.rollback()
