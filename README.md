# Licita TI

[![CI](https://github.com/JoaoPedroTSouza/licita-ti/actions/workflows/ci.yml/badge.svg)](https://github.com/JoaoPedroTSouza/licita-ti/actions/workflows/ci.yml)

Monitor pessoal de editais públicos de **desenvolvimento web e consultoria de TI**, com app PWA para Android.

```
[worker] ─► PNCP (API pública) ─► filtro por palavras-chave ─► Postgres
                                                      │
                                         IA classifica e resume
                                                      │
                                  Web Push ◄──────────┘
                                     │
[PWA Next.js no Android] ◄── /api ──► [FastAPI]
```

- **Coletor** (`backend/app/coletor`): consulta `GET /v1/contratacoes/publicacao` do PNCP para cada modalidade escolhida, guarda só os candidatos que passam no filtro e atualiza retificações sem duplicar.
- **IA**: classifica relevância (0–100), categoria, resumo e exigências prováveis. Sem chave de API, o sistema funciona só com palavras-chave.
- **Notificações**: push quando surgem editais relevantes e lembrete antes do prazo dos editais que você marcou como *Analisando* ou *Participando*.
- **App**: feed com busca e filtros, detalhe com análise da IA, funil de acompanhamento, notas, e ajustes (palavras-chave, UFs, modalidades, faixa de valor, perfil).
- **Workspace**:
  - **Painel** de monitoramento: números principais, régua de prazos dos próximos 14 dias, editais relevantes por dia, distribuição por estado e saúde das coletas.
  - **Ideias**: quadro por situação (novas, validando, em execução, concluídas), com arrastar e soltar no desktop, prioridade, etiquetas, potencial mensal e vínculo opcional a um edital.
- **Layout**: desktop de 1440px com menu lateral; abaixo de 1024px vira barra inferior. Tema claro e escuro.

> Quer ver tudo funcionando antes da primeira coleta? Rode `python -m app.scripts.seed_demo` no backend para criar dados de demonstração. As capturas de tela geradas pelo CI ficam no branch [`capturas`](../../tree/capturas).

## 1. Rodar localmente (Docker)

```bash
cp .env.example .env
# edite APP_PASSWORD, JWT_SECRET e, se quiser IA, ANTHROPIC_API_KEY

docker compose build
docker compose run --rm api python -m app.scripts.gen_vapid   # cole as 2 linhas no .env
docker compose up -d
```

- App: http://localhost:3000 (entre com `APP_PASSWORD`)
- API e documentação: http://localhost:8000/docs
- O worker faz uma coleta ao subir e depois às 7h, 12h e 18h (Brasília). Para popular rápido, use **Ajustes → Últimos 7 dias**.

## 2. Rodar sem Docker (desenvolvimento)

```bash
# Postgres local rodando, depois:
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # ajuste DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/licita
uvicorn app.main:app --reload          # terminal 1
python -m app.worker                   # terminal 2
pytest -q                              # testes (usam SQLite, não precisam do Postgres)

cd ../frontend
npm install
npm run dev                            # terminal 3 → http://localhost:3000
```

## 3. Instalar no Android

Push e instalação de PWA **exigem HTTPS** (exceto em `localhost`). Duas opções:

**Para testar no celular hoje** — túnel gratuito da Cloudflare:
```bash
cloudflared tunnel --url http://localhost:3000
```
Abra a URL `https://….trycloudflare.com` no Chrome do Android.

**Para uso contínuo** — um VPS barato (Hetzner, Contabo, Oracle Free Tier…) com um domínio:
```bash
# no .env: DOMAIN=licita.seudominio.com.br  (DNS tipo A apontando para o VPS)
docker compose --profile https up -d
```
O Caddy emite o certificado automaticamente. Feche a porta 8000 no firewall; o app acessa a API pelo próprio domínio (`/api`).

No Chrome do Android: abra o site → toque em **Instalar** (banner no app ou menu ⋮ → *Instalar app*) → em **Ajustes**, ative **Alertas de novos editais** → **Enviar notificação de teste**.

## 4. Ajustando a pontaria

- **Palavras-chave** valem 2 pontos; **reforço** (ex.: "software", "sistema") vale 1. O padrão exige 2 pontos para virar candidato.
- **Exclusões** descartam o edital mesmo que tenha palavras-chave (ex.: "aquisição de computadores").
- **Perfil** é o texto que a IA usa para julgar viabilidade. Descreva porte, especialidades e se atende remoto.
- **Nota mínima para notificar** controla quantos pushes você recebe. Comece em 60 e ajuste.
- Custo de IA: com o modelo Haiku e o teto de 60 classificações por coleta, o gasto costuma ficar em poucos dólares por mês.

## 5. Estrutura

```
backend/
  app/main.py              rotas FastAPI (/api/...)
  app/models.py            editais, inscrições push, preferências, execuções
  app/preferencias.py      palavras-chave e modalidades padrão
  app/coletor/pncp.py      cliente da API do PNCP (paginação, retentativas)
  app/coletor/filtro.py    pontuação sem acento/caixa, com limite de palavra e plural
  app/coletor/ia.py        classificação e resumo com LLM
  app/coletor/executar.py  orquestração + notificações + lembretes de prazo
  app/worker.py            agendador (APScheduler)
  app/push.py              envio Web Push (VAPID)
  tests/                   teste ponta a ponta com PNCP e IA simulados
frontend/
  app/                     telas: editais, detalhe, acompanhamento, ajustes, login
  app/manifest.ts          manifest do PWA
  public/sw.js             service worker (cache offline + push)
  lib/                     cliente da API, push, formatação, tipos
```

## 6. Próximos passos sugeridos

1. **Ler os anexos**: a API principal do PNCP lista os arquivos de cada compra (`/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos`). Baixar o termo de referência em PDF e mandar para a IA melhora muito o resumo e as exigências.
2. **Querido Diário**: adicionar avisos de diários oficiais municipais que não chegam ao PNCP.
3. **Itens da compra**: consultar os itens/CATSER para filtrar por código de serviço, não só por texto.
4. **Migrações** com Alembic quando o modelo de dados começar a mudar (hoje as tabelas são criadas automaticamente).
5. **Multiusuário e planos** se quiser vender como SaaS para outros freelancers de TI.
