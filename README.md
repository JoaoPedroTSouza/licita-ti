# Radar

[![CI](https://github.com/JoaoPedroTSouza/licita-ti/actions/workflows/ci.yml/badge.svg)](https://github.com/JoaoPedroTSouza/licita-ti/actions/workflows/ci.yml)

Workspace pessoal, em formato PWA, para encontrar e acompanhar **oportunidades de consultoria remotas** (organismos internacionais e bancos multilaterais). O Radar coleta oportunidades de fontes públicas, uma IA avalia cada uma contra o seu perfil e só o que vale a pena chega até você.

## O que o Radar faz

A tela tem três áreas de trabalho, mais os ajustes:

- **Hoje**: o que fazer agora. Lembretes e prazos do dia, as melhores oportunidades novas e um resumo do funil.
- **Entrada**: oportunidades novas já avaliadas pela IA, com nota, resumo e motivos. Você decide: **Me interessa** (vira um processo no funil) ou **Descartar** (com motivo opcional).
- **Funil**: quadro por etapa dos processos em andamento, com detalhe de cada um (notas, arquivos anexados, contatos e lembretes).
- **Rede**: contatos, com o lembrete de quando falar de novo com cada pessoa.
- **Ajustes**: perfil profissional (texto e faixa de valor), limiar do alerta imediato, horário do resumo diário, dias de aviso de prazo, notificações push e o estado de cada fonte.

Sem `ANTHROPIC_API_KEY` nenhuma oportunidade é avaliada e, portanto, nenhuma aparece na Entrada.

## Arquitetura

Backend em camadas (`backend/radar`), com dependências sempre apontando para dentro:

```
interfaces ──► application ──► domain
 (HTTP, worker,    (casos de uso,    (entidades e regras,
  scripts)          portas)           sem I/O)
      │                 ▲
      └─► infrastructure┘   (banco, fontes, IA, push, arquivos)
          implementa as portas da application
```

- `domain`: entidades (oportunidade, processo, contato, lembrete, perfil) e regras de negócio.
- `application`: casos de uso e as portas (interfaces) que eles precisam.
- `infrastructure`: SQLAlchemy, adaptadores das fontes, cliente da IA, Web Push e armazenamento de arquivos.
- `interfaces`: API FastAPI (`/api/...`), worker agendado e scripts (`seed_demo`, `gen_vapid`).

Frontend em Next.js (`frontend/`): `app/` só compõe as rotas, `features/<área>/` tem os componentes de cada área e `shared/` o cliente da API, a interface comum e os helpers de PWA.

## Fontes

| Fonte | Situação |
| --- | --- |
| UNGM (ONU) | ativa |
| OPAS Brasil | ativa |
| Banco Mundial | ativa |
| ReliefWeb | **desativada**: a API v2 exige um `appname` aprovado pela ReliefWeb. Detalhes e como ativar em [docs/fontes/reliefweb.md](docs/fontes/reliefweb.md) |

O worker coleta ao subir e depois nos horários de `COLETA_HORARIOS` (horário de Brasília). Em **Ajustes → Fontes** você vê a última execução de cada uma, quantas oportunidades recebeu e o erro, se houve.

## 1. Rodar localmente (Docker)

```bash
cp .env.example .env
# edite APP_PASSWORD, JWT_SECRET e, para a IA, ANTHROPIC_API_KEY

docker compose build
docker compose run --rm api python -m radar.interfaces.gen_vapid   # cole as 2 linhas no .env
docker compose up -d
```

- App: http://localhost:3000 (entre com `APP_PASSWORD`)
- API e documentação: http://localhost:8000/docs

Para ver tudo funcionando antes da primeira coleta, carregue os dados de demonstração:

```bash
docker compose run --rm api python -m radar.interfaces.seed_demo
```

## 2. Rodar sem Docker (desenvolvimento)

```bash
# Postgres local rodando (ou use SQLite, veja abaixo), depois:
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # ajuste DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/radar

python -m radar.interfaces.seed_demo        # opcional: dados de demonstração
python -m radar.interfaces.gen_vapid        # gera VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY
uvicorn radar.interfaces.http.app:criar_app --factory --reload   # terminal 1
python -m radar.interfaces.worker                                # terminal 2

cd ../frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev                    # terminal 3 -> http://localhost:3000
```

Para um banco descartável de teste, use `DATABASE_URL=sqlite:///./demo.db`.

## 3. Testes

```bash
cd backend && pytest -q                                  # usam SQLite, não precisam do Postgres
cd frontend && npm test && npx tsc --noEmit && npm run build
```

O CI (`.github/workflows/ci.yml`) roda os mesmos passos e valida o `docker-compose.yml`.

## 4. Instalar no Android

Push e instalação de PWA **exigem HTTPS** (exceto em `localhost`). Duas opções:

**Para testar no celular hoje**: túnel gratuito da Cloudflare:
```bash
cloudflared tunnel --url http://localhost:3000
```
Abra a URL `https://….trycloudflare.com` no Chrome do Android.

**Para uso contínuo**: um VPS barato (Hetzner, Contabo, Oracle Free Tier...) com um domínio:
```bash
# no .env: DOMAIN=radar.seudominio.com.br  (DNS tipo A apontando para o VPS)
docker compose --profile https up -d
```
O Caddy emite o certificado automaticamente. Feche a porta 8000 no firewall; o app acessa a API pelo próprio domínio (`/api`).

No Chrome do Android: abra o site, toque em **Instalar** (banner no app ou menu ⋮, *Instalar app*), depois vá em **Ajustes → Notificações**, toque em **Ativar neste aparelho** e em **Enviar notificação de teste**.

## 5. Variáveis do `.env`

| Variável | Para que serve | Padrão |
| --- | --- | --- |
| `APP_PASSWORD` | Senha que você digita no app (um único usuário) | `troque-esta-senha` |
| `JWT_SECRET` | Segredo que assina a sessão. Gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` | `troque-este-segredo` |
| `POSTGRES_PASSWORD` | Senha do Postgres do Docker Compose | `licita` |
| `DATABASE_URL` | Conexão com o banco (o Compose já define a sua) | Postgres local |
| `ANTHROPIC_API_KEY` | Chave da IA que avalia as oportunidades. Sem ela, nada aparece na Entrada | vazio |
| `LLM_MODEL` | Modelo usado na avaliação | `claude-haiku-5-5` |
| `LLM_MAX_POR_EXECUCAO` | Teto de avaliações por coleta (controle de custo) | `60` |
| `RELIEFWEB_APPNAME` | `appname` aprovado da ReliefWeb; vazio mantém a fonte desativada | vazio |
| `ARQUIVOS_DIR` | Pasta dos arquivos anexados aos processos | `/data/arquivos` |
| `ARQUIVO_MAX_MB` | Tamanho máximo de cada anexo | `20` |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` | Chaves do Web Push, geradas por `python -m radar.interfaces.gen_vapid` | vazio |
| `VAPID_SUBJECT` | Contato exigido pelo Web Push (`mailto:...`) | `mailto:voce@exemplo.com` |
| `COLETA_HORARIOS` | Horas do dia (Brasília) em que o worker coleta | `7,12,18` |
| `DOMAIN` | Domínio do servidor, usado pelo Caddy para emitir o HTTPS | `localhost` |
| `APP_URL` | URL pública do app (links das notificações) | `http://localhost:3000` |
