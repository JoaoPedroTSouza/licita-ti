"""Popula o banco com dados de demonstração (editais, ideias e coletas).

Uso: python -m app.scripts.seed_demo
Útil para ver o painel funcionando antes da primeira coleta real.
"""

import random
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal, init_db
from app.models import Edital, ExecucaoColeta, Ideia

OBJETOS = [
    ("Contratação de empresa para desenvolvimento de portal institucional responsivo com gestão de conteúdo", "desenvolvimento web", "SP"),
    ("Desenvolvimento de sistema web de ouvidoria com integração ao e-SIC", "sistema sob medida", "MG"),
    ("Fábrica de software para manutenção evolutiva e corretiva de sistemas legados, medição por ponto de função", "fábrica de software", "DF"),
    ("Aplicativo móvel para agendamento de consultas na rede municipal de saúde", "aplicativo", "PR"),
    ("Consultoria em tecnologia da informação para modernização da infraestrutura de sistemas", "consultoria TI", "RJ"),
    ("Sustentação de sistemas web da Secretaria de Educação, com suporte de 2º nível", "sustentação", "BA"),
    ("Desenvolvimento de plataforma de transparência e dados abertos", "desenvolvimento web", "SC"),
    ("Contratação de serviços de UX/UI para redesenho do portal de serviços ao cidadão", "desenvolvimento web", "RS"),
    ("Sistema de gestão de protocolos e processos eletrônicos sob medida", "sistema sob medida", "GO"),
    ("Chatbot com inteligência artificial para atendimento no portal da prefeitura", "outro TI", "PE"),
    ("Integração de sistemas de arrecadação com API do banco oficial", "sistema sob medida", "CE"),
    ("Website e hospedagem para câmara municipal, com manutenção mensal", "desenvolvimento web", "MG"),
    ("Business intelligence para painéis de gestão da Secretaria de Fazenda", "consultoria TI", "SP"),
    ("Aplicativo de turismo com mapa interativo e agenda cultural", "aplicativo", "ES"),
    ("Desenvolvimento de e-commerce institucional para venda de publicações", "desenvolvimento web", "PA"),
]
ORGAOS = ["Prefeitura Municipal de Campinas", "Câmara Municipal de Uberlândia", "Secretaria de Estado da Fazenda",
          "Universidade Federal", "Consórcio Intermunicipal de Saúde", "Tribunal de Contas do Estado"]
MUNICIPIOS = {"SP": "Campinas", "MG": "Uberlândia", "DF": "Brasília", "PR": "Londrina", "RJ": "Niterói", "BA": "Salvador",
              "SC": "Joinville", "RS": "Caxias do Sul", "GO": "Anápolis", "PE": "Recife", "CE": "Fortaleza",
              "ES": "Vitória", "PA": "Belém"}


def main() -> None:
    init_db()
    db = SessionLocal()
    rnd = random.Random(42)
    agora = datetime.now(timezone.utc)
    if db.query(Edital).filter(Edital.numero_controle_pncp.like("DEMO-%")).count():
        print("Dados de demonstração já existem.")
        return

    editais = []
    for i in range(32):
        objeto, cat, uf = OBJETOS[i % len(OBJETOS)]
        pub = agora - timedelta(days=rnd.randint(0, 13), hours=rnd.randint(0, 10))
        enc = agora + timedelta(days=rnd.choice([0, 1, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13, 20]), hours=rnd.randint(1, 9))
        relevante = i % 6 != 5
        status = ["novo"] * 6 + ["analisando", "analisando", "participando", "descartado"]
        e = Edital(
            numero_controle_pncp=f"DEMO-{i:04d}",
            cnpj="00000000000191", ano=2026, sequencial=i + 1, numero_compra=f"{90 + i}/2026",
            objeto=objeto, orgao=rnd.choice(ORGAOS), unidade="Departamento de Compras",
            uf=uf, municipio=MUNICIPIOS[uf], modalidade_id=6, modalidade_nome="Pregão - Eletrônico",
            modo_disputa="Aberto", situacao="Divulgada no PNCP", srp=bool(i % 3 == 0),
            valor_estimado=rnd.choice([48000, 85000, 120000, 240000, 380000, 760000, 1250000]),
            data_publicacao=pub, data_abertura=enc - timedelta(days=1), data_encerramento=enc,
            link_pncp="https://pncp.gov.br/app/editais", keyword_score=rnd.randint(3, 8),
            keywords_encontradas=["desenvolvimento de sistema", "web"],
            ia_processado=True, ia_relevante=relevante, ia_score=rnd.randint(68, 94) if relevante else rnd.randint(15, 40),
            ia_categoria=cat if relevante else "não TI",
            ia_resumo="O órgão quer contratar uma empresa para construir e manter a solução descrita, com entregas mensais "
                      "e suporte durante 12 meses. O escopo é compatível com uma equipe pequena trabalhando remotamente.",
            ia_motivo="Escopo bem definido e valor adequado ao porte; exige atestado de capacidade técnica.",
            ia_exigencias=["Atestado de capacidade técnica", "Certidões negativas", "Cadastro no SICAF"],
            status=rnd.choice(status), notificado=True,
        )
        db.add(e)
        editais.append(e)
    db.commit()

    ideias = [
        ("Micro-SaaS de orçamento para prestadores de serviço", "produto", "validando", "alta", ["saas", "nicho"], 4000),
        ("Pacote fixo de site + manutenção para câmaras municipais", "servico", "executando", "alta", ["licitação", "recorrente"], 6000),
        ("Série no YouTube: como ganhar sua primeira licitação de TI", "conteudo", "nova", "media", ["youtube"], 1500),
        ("Ler PDF do termo de referência com IA", "melhoria", "nova", "alta", ["ia", "pdf"], None),
        ("Vender o Licita TI como assinatura para freelancers", "produto", "nova", "media", ["saas"], 8000),
        ("Template de proposta técnica reutilizável", "melhoria", "concluida", "baixa", ["produtividade"], None),
        ("Chatbot de WhatsApp para clínicas", "servico", "validando", "media", ["whatsapp", "ia"], 3000),
        ("Proposta para o portal de transparência", "proposta", "executando", "alta", ["pregão"], None),
        ("Curso de Next.js para PWAs", "conteudo", "descartada", "baixa", ["curso"], 2000),
    ]
    for j, (t, tipo, st, pr, tags, pot) in enumerate(ideias):
        db.add(Ideia(
            titulo=t, tipo=tipo, status=st, prioridade=pr, tags=tags, potencial_mensal=pot,
            descricao="Validar com três clientes antes de construir. Começar pelo nicho que já conheço.",
            edital_id=editais[6].id if tipo == "proposta" else None,
            atualizado_em=agora - timedelta(hours=j * 5),
        ))

    for k in reversed(range(6)):  # mais antiga primeiro, como numa sequência real
        fim = agora - timedelta(hours=6 * k + 1)
        db.add(ExecucaoColeta(
            iniciado_em=fim - timedelta(minutes=3), finalizado_em=fim, data_referencia=fim.date().isoformat(),
            recebidos=rnd.randint(380, 900), novos=rnd.randint(3, 14), candidatos=0, relevantes=rnd.randint(1, 6),
            notificados=rnd.randint(0, 3), erro="Timeout no PNCP" if k == 4 else None,
        ))
    db.commit()
    db.close()
    print("Dados de demonstração criados.")


if __name__ == "__main__":
    main()
