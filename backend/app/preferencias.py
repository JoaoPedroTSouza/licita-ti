"""Preferências padrão do monitoramento. Podem ser editadas pelo app (tela Ajustes)."""

from sqlalchemy.orm import Session

from app.models import Configuracao

# Códigos de modalidade do PNCP (tabela de domínio do Manual de Integração)
MODALIDADES = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa de Licitação",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
}

PADRAO = {
    # Termos que indicam o tipo de serviço desejado (peso 2 cada)
    "palavras_chave": [
        "desenvolvimento de sistema",
        "desenvolvimento de software",
        "fabrica de software",
        "desenvolvimento web",
        "website",
        "sitio eletronico",
        "portal institucional",
        "portal da transparencia",
        "aplicativo",
        "app mobile",
        "sustentacao de sistema",
        "manutencao evolutiva",
        "manutencao corretiva de sistema",
        "consultoria em tecnologia da informacao",
        "consultoria em ti",
        "servicos de ti",
        "servicos tecnicos de tecnologia da informacao",
        "ponto de funcao",
        "ust",
        "integracao de sistemas",
        "e-commerce",
        "hospedagem de site",
        "chatbot",
        "inteligencia artificial",
        "business intelligence",
        "ux",
        "ui",
    ],
    # Termos de contexto que reforçam (peso 1 cada)
    "palavras_reforco": ["software", "sistema", "tecnologia da informacao", "digital", "web", "plataforma"],
    # Termos que indicam que NÃO é serviço de desenvolvimento/consultoria
    "palavras_exclusao": [
        "aquisicao de computadores",
        "aquisicao de notebooks",
        "aquisicao de equipamentos",
        "toner",
        "impressora",
        "outsourcing de impressao",
        "material de expediente",
        "licenca de uso de software de prateleira",
        "telefonia",
        "link de internet",
        "cabeamento",
        "nobreak",
        "veiculo",
        "medicamento",
        "merenda",
        "combustivel",
    ],
    "ufs": [],  # vazio = todas
    "modalidades": [4, 5, 6, 7, 8, 12],
    "valor_minimo": 0,
    "valor_maximo": 0,  # 0 = sem limite
    "score_minimo_keywords": 2,
    "score_minimo_ia_push": 60,
    "perfil": (
        "Desenvolvedor freelancer/pequena empresa (ME) que presta serviços de desenvolvimento web, "
        "sistemas sob medida, aplicativos e consultoria em TI. Equipe pequena, atende remotamente."
    ),
}


def carregar(db: Session) -> dict:
    prefs = dict(PADRAO)
    for row in db.query(Configuracao).all():
        prefs[row.chave] = row.valor
    return prefs


def salvar(db: Session, novos: dict) -> dict:
    for chave, valor in novos.items():
        if chave not in PADRAO:
            continue
        row = db.get(Configuracao, chave)
        if row is None:
            db.add(Configuracao(chave=chave, valor=valor))
        else:
            row.valor = valor
    db.commit()
    return carregar(db)
