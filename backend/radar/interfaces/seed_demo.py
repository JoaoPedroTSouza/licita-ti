"""Dados de demonstração para desenvolver o frontend (sem IA nem fontes externas).

Uso: python -m radar.interfaces.seed_demo
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import sessionmaker

from radar.config import get_settings
from radar.domain.contato import Contato
from radar.domain.dinheiro import Dinheiro
from radar.domain.lembrete import Lembrete
from radar.domain.oportunidade import (
    Classificacao, Modalidade, Oportunidade, OportunidadeBruta, StatusOportunidade,
    TipoContratacao,
)
from radar.domain.perfil import Perfil
from radar.domain.processo import Etapa, Processo
from radar.infrastructure.db.repositorios import (
    UnidadeDeTrabalhoSql, criar_engine, criar_tabelas,
)

PERFIL = (
    "Consultor sênior de engenharia de software, 12 anos de experiência. Backend em Python "
    "e APIs, integrações e CRM (Salesforce, HubSpot), com foco em sistemas de saúde: "
    "interoperabilidade HL7/FHIR, prontuário eletrônico e saúde pública. Atuação 100% remota, "
    "em português e inglês, para organismos internacionais, ONGs e empresas."
)

# (fonte, titulo, organizacao, pais, nota, resumo, tipo, valor, dias_prazo)
OPORTUNIDADES = [
    ("ungm", "Health information systems consultant", "OPAS/OMS", "Brasil", 92,
     "Consultoria remota para modernizar sistemas de informação em saúde, com FHIR.",
     TipoContratacao.EMPRESA, Dinheiro(Decimal("45000"), "USD"), 12),
    ("ungm", "CRM implementation specialist", "UNICEF", "Panamá", 88,
     "Implantação de CRM para gestão de doadores e parceiros regionais.",
     TipoContratacao.EMPRESA, Dinheiro(Decimal("38000"), "USD"), 20),
    ("opas", "Consultor(a) de desenvolvimento backend", "OPAS Brasil", "Brasil", 85,
     "Desenvolvimento de APIs para o painel nacional de vigilância em saúde.",
     TipoContratacao.PESSOA_FISICA, Dinheiro(Decimal("120000"), "BRL"), 9),
    ("bancomundial", "Digital health data platform advisor", "Banco Mundial", "Moçambique", 79,
     "Assessoria técnica para plataforma de dados de saúde digital.",
     TipoContratacao.EMPRESA, Dinheiro(Decimal("60000"), "USD"), 30),
    ("reliefweb", "Data integration engineer, health programs", "Médicos Sem Fronteiras", "Quênia",
     74, "Integração de dados entre sistemas de campo e o data warehouse global.",
     TipoContratacao.EMPRESA, None, 15),
    ("ungm", "API modernization for civil registry", "PNUD", "Peru", 68,
     "Modernização das APIs do registro civil, com migração de legado.",
     TipoContratacao.EMPRESA, Dinheiro(Decimal("52000"), "USD"), 25),
]

# (titulo, organizacao, etapa, valor, dias_prazo)
PROCESSOS = [
    ("Plataforma de vigilância epidemiológica", "OPAS Brasil", Etapa.ANALISANDO,
     Dinheiro(Decimal("90000"), "BRL"), 14),
    ("CRM para rede de hospitais", "Hospital Aurora", Etapa.PROPOSTA_ENVIADA,
     Dinheiro(Decimal("30000"), "USD"), 7),
    ("Integração FHIR com secretaria estadual", "SES-MG", Etapa.NEGOCIACAO,
     Dinheiro(Decimal("150000"), "BRL"), 5),
    ("Painel de indicadores de imunização", "Fiocruz", Etapa.FECHADO,
     Dinheiro(Decimal("75000"), "BRL"), None),
]


def main() -> None:
    settings = get_settings()
    engine = criar_engine(settings.database_url)
    criar_tabelas(engine)
    fabrica = sessionmaker(engine, expire_on_commit=False)
    agora = datetime.now(UTC)
    tz = ZoneInfo(settings.timezone)
    hoje = agora.astimezone(tz).date()

    with UnidadeDeTrabalhoSql(fabrica) as uow:
        if any(uow.oportunidades.listar(st, 1) for st in StatusOportunidade):
            print("Já existem oportunidades; seed ignorado.")
            return

        for i, (fonte, titulo, org, pais, nota, resumo, tipo, valor, dias) in enumerate(
            OPORTUNIDADES, start=1
        ):
            prazo = agora + timedelta(days=dias)
            bruta = OportunidadeBruta(
                fonte=fonte, id_externo=f"demo-{i}", titulo=titulo, organizacao=org,
                link=f"https://exemplo.org/demo/{i}", texto=resumo, pais=pais, prazo=prazo,
                valor=valor, publicada_em=agora - timedelta(days=1), idioma="en",
            )
            classificacao = Classificacao(
                relevante=True, nota=nota, resumo=resumo, modalidade=Modalidade.REMOTO_TOTAL,
                trecho_modalidade="Home-based / remote", idioma="en", tipo_contratacao=tipo,
                motivo="Combina com o perfil de backend, CRM e saúde.", prazo=prazo,
            )
            uow.oportunidades.adicionar(Oportunidade(
                id=None, bruta=bruta, coletada_em=agora - timedelta(hours=i),
                status=StatusOportunidade.NOVA, classificacao=classificacao,
            ))

        processos = []
        for titulo, org, etapa, valor, dias in PROCESSOS:
            p = Processo.novo(
                titulo, agora - timedelta(days=10), organizacao=org, valor=valor,
                prazo=agora + timedelta(days=dias) if dias is not None else None,
            )
            if etapa != Etapa.ANALISANDO:
                p.mover(etapa, agora - timedelta(days=3))
            p.anotar("Primeira conversa realizada; aguardando retorno.", agora - timedelta(days=2))
            processos.append(uow.processos.adicionar(p))

        fim_do_dia = datetime.combine(hoje, datetime.min.time(), tzinfo=tz).replace(hour=17)
        for texto, vence, processo in [
            ("Enviar proposta revisada", fim_do_dia, processos[1]),
            ("Reunião de alinhamento técnico", fim_do_dia + timedelta(days=2), processos[2]),
            ("Atualizar portfólio de casos de saúde", fim_do_dia + timedelta(days=6), None),
        ]:
            uow.lembretes.adicionar(Lembrete(
                id=None, texto=texto, vence_em=vence,
                processo_id=processo.id if processo else None,
            ))

        for nome, org, como, ultimo, freq in [
            ("Marina Duarte", "OPAS Brasil", "Congresso de saúde digital",
             hoje - timedelta(days=45), 30),
            ("Carlos Mendes", "Fiocruz", "Indicação de colega", hoje - timedelta(days=5), 30),
            ("Ana Whitfield", "UNICEF", "LinkedIn", hoje - timedelta(days=10), None),
        ]:
            uow.contatos.adicionar(Contato(
                id=None, nome=nome, organizacao=org, como_conheceu=como,
                ultimo_contato=ultimo, frequencia_dias=freq,
            ))

        uow.configuracoes.salvar_perfil(Perfil(
            texto=PERFIL, faixa_min_brl=Decimal("30000"), faixa_max_brl=Decimal("200000"),
        ))
        uow.cotacoes.salvar("USD", hoje, Decimal("5.40"))
        uow.cotacoes.salvar("EUR", hoje, Decimal("5.85"))
        uow.commit()
    print("Seed de demonstração criado.")


if __name__ == "__main__":
    main()
