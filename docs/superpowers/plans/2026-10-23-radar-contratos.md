# Radar de Contratos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o monitor de licitações por um workspace pessoal ("Radar") que coleta chamadas 100% remotas de organismos internacionais, classifica com IA e acompanha cada processo num funil, com lembretes, rede de contatos e push.

**Architecture:** Backend Python em camadas (`domain` → `application` → `infrastructure`/`interfaces`), com portas como `typing.Protocol` em `application/portas.py` e adaptadores em `infrastructure`. Os casos de uso recebem uma `UnidadeDeTrabalho` e portas por injeção. A composição fica em `radar/container.py`, que é o único módulo que conhece todas as camadas. O frontend Next.js PWA é organizado por funcionalidade (`features/*`) sobre um cliente de API tipado em `shared/api`.

**Tech Stack:** Python 3.12, FastAPI 0.115, SQLAlchemy 2, Postgres 16 (SQLite nos testes), APScheduler 3.10, httpx 0.28, beautifulsoup4, anthropic SDK, pywebpush; Next.js 15, React 19, TypeScript 5, Tailwind 4, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-23-radar-contratos-design.md`

## Global Constraints

- Interface em **português**; o resumo da IA é sempre em português.
- Admissão na Entrada: somente `modalidade == remoto_total`, `idioma in {"pt", "en"}`, prazo não vencido e `relevante == True`. Qualquer outra coisa vira `DESCARTADA_AUTO` com motivo. **A regra mora no domínio, não no prompt.**
- "100% remoto" é rígido: viagem de abertura, uma missão presencial, reuniões presenciais eventuais, exigência de residência/cidade, híbrido **ou texto sem informação** → `com_presenca`/`indefinido` → descartada.
- Chamadas `pessoa_fisica` aparecem com a etiqueta **"Pessoa física"**.
- Etapas do funil, nesta ordem: `analisando`, `proposta_enviada`, `negociacao`, `fechado`, `perdido`. Abertas = as três primeiras.
- Sem `ANTHROPIC_API_KEY`: a coleta não classifica, **nada aparece na Entrada**, e `GET /api/status` devolve `ia_configurada: false` para o aviso em Ajustes.
- Ajustes padrão: `limiar_alerta = 85`, `horario_resumo = "07:30"`, `avisos_prazo_dias = [3, 1]`. Fuso `America/Sao_Paulo`.
- Valores: guardar moeda original; totais e faixa do Perfil em BRL via PTAX do Banco Central; usar a última cotação conhecida quando não houver a do dia.
- Um usuário só, login por senha (`APP_PASSWORD`) + JWT, como no app atual.
- `radar.domain` não importa nada de `fastapi`, `sqlalchemy`, `httpx`, `anthropic` nem de outras camadas do pacote. `radar.application` importa só `radar.domain`.
- Nomes de código em português, no estilo do app atual (`snake_case` em Python, `camelCase` em TS).

## Review Focus

1. **A mesma chamada publicada em duas fontes** (UNGM e página da OPAS): deve aparecer uma vez só na Entrada. Teste em Task 4 (`test_deduplica_entre_fontes`).
2. **A IA devolve JSON inválido ou cai**: a oportunidade fica `PENDENTE` e é reprocessada na próxima coleta; nunca vira `NOVA` sem classificação. Testes em Task 4 (`test_falha_do_classificador_mantem_pendente`) e Task 8 (`test_resposta_sem_json_levanta_erro`).
3. **Fronteira de dia no fuso de Brasília**: um lembrete que vence às 23:30 BRT de hoje (02:30 UTC de amanhã) precisa aparecer em "Para fazer" hoje. Teste em Task 6 (`test_lembrete_23h30_brt_aparece_hoje`).
4. **Upload com nome malicioso ou grande demais** (`../../etc/passwd`, arquivo > 20 MB): o nome é sanitizado e arquivos grandes são recusados com 413. Teste em Task 14 (`test_upload_nome_com_caminho_e_sanitizado`, `test_upload_maior_que_limite_413`).
5. **Inscrição de push expirada (404/410)**: é removida e o envio continua para os outros aparelhos. Teste em Task 9 (`test_inscricao_expirada_e_removida`).

---

## File Structure

```
backend/
  requirements.txt                    # + beautifulsoup4; − nada do PNCP
  Dockerfile                          # copia radar/ em vez de app/
  radar/
    __init__.py
    config.py                         # Settings (pydantic-settings)
    container.py                      # composição: monta casos de uso com adaptadores
    domain/
      dinheiro.py                     # Dinheiro, converter_para_brl
      oportunidade.py                 # OportunidadeBruta, Oportunidade, Classificacao, enums
      admissao.py                     # avaliar_admissao (regra rígida)
      processo.py                     # Processo, Etapa, Nota, Arquivo, MudancaEtapa
      lembrete.py                     # Lembrete
      contato.py                      # Contato
      perfil.py                       # Perfil, Ajustes
      erros.py                        # ErroDeDominio, NaoEncontrado, TransicaoInvalida
    application/
      portas.py                       # Protocols: fontes, classificador, notificador, repositórios, UoW, relógio
      coletar.py                      # ColetarOportunidades
      triar.py                        # TriarOportunidade
      funil.py                        # casos de uso do funil e lembretes
      rede.py                         # casos de uso de contatos
      painel.py                       # MontarPainelDoDia
      notificacoes.py                 # EnviarResumoDiario, VerificarPrazos
      cotacoes.py                     # AtualizarCotacoes
    infrastructure/
      db/tabelas.py                   # modelos ORM
      db/repositorios.py              # repositórios + UnidadeDeTrabalhoSql
      ia/claude.py                    # ClassificadorClaude
      push/webpush.py                 # NotificadorWebPush
      cotacoes/ptax.py                # FontePtax
      arquivos/disco.py               # ArmazenamentoEmDisco
      fontes/ungm.py, opas.py, reliefweb.py, banco_mundial.py
    interfaces/
      http/app.py                     # cria FastAPI, inclui routers
      http/auth.py
      http/dtos.py
      http/rotas_oportunidades.py, rotas_painel.py, rotas_ajustes.py,
      http/rotas_processos.py, rotas_lembretes.py, rotas_contatos.py, rotas_push.py
      worker.py                       # agendamentos
      seed_demo.py
  tests/
    fakes.py                          # UoW em memória, fontes/classificador/notificador falsos, RelogioFixo
    domain/, application/, infrastructure/, http/
    fixtures/fontes/<fonte>/...       # respostas reais gravadas
frontend/
  app/(workspace)/layout.tsx, hoje/page.tsx, entrada/page.tsx, entrada/[id]/page.tsx,
      funil/page.tsx, rede/page.tsx, ajustes/page.tsx
  app/login/page.tsx, app/layout.tsx, app/page.tsx (redireciona para /hoje), app/manifest.ts
  features/hoje/, entrada/, funil/, rede/, ajustes/  # componentes + hooks de cada área
  shared/api/cliente.ts, shared/api/tipos.ts, shared/formato.ts, shared/ui/*, shared/pwa/*
  public/sw.js
```

O que é apagado: `backend/app/`, `backend/tests/*` antigos, `frontend/app/{editais,ideias,acompanhamento}`, `frontend/components/*`, `frontend/lib/*`, `frontend/scripts/capturas.mjs`.

---

### Task 1: Esqueleto do backend novo

**Files:**
- Delete: `backend/app/`, `backend/tests/` (todo o conteúdo antigo)
- Create: `backend/radar/__init__.py`, `backend/radar/config.py`, `backend/radar/domain/__init__.py`, `backend/radar/application/__init__.py`, `backend/radar/infrastructure/__init__.py`, `backend/radar/interfaces/__init__.py`, `backend/tests/__init__.py`, `backend/tests/test_arquitetura.py`, `backend/pytest.ini`
- Modify: `backend/requirements.txt`, `backend/Dockerfile`, `.github/workflows/ci.yml` (job backend: `compileall -q radar tests`; remova o job `capturas`)

**Interfaces:**
- Produces: `radar.config.Settings` com `database_url`, `app_password`, `jwt_secret`, `jwt_expire_days=30`, `anthropic_api_key=""`, `llm_model="claude-haiku-4-5-20251001"`, `llm_max_por_execucao=60`, `vapid_public_key`, `vapid_private_key`, `vapid_subject`, `timezone="America/Sao_Paulo"`, `coleta_horarios="7,12,18"`, `app_url`, `arquivos_dir="/data/arquivos"`, `arquivo_max_mb=20`; `get_settings()` com `lru_cache`.

- [ ] **Step 1: Escreva o teste de arquitetura**

`tests/test_arquitetura.py`: percorre os `.py` de `radar/domain` e `radar/application` com `ast` e coleta os imports.

```python
PROIBIDOS_NO_DOMINIO = ("fastapi", "sqlalchemy", "httpx", "anthropic", "pywebpush", "radar.application", "radar.infrastructure", "radar.interfaces")
PROIBIDOS_NA_APLICACAO = PROIBIDOS_NO_DOMINIO[:5] + ("radar.infrastructure", "radar.interfaces")

def test_dominio_nao_depende_de_frameworks_nem_de_outras_camadas(): ...
def test_aplicacao_depende_so_do_dominio(): ...
```

- [ ] **Step 2: Rode e veja falhar** — `cd backend && pytest -q tests/test_arquitetura.py` → FAIL (pacote `radar` ausente).
- [ ] **Step 3: Crie o pacote, `config.py` e `pytest.ini`** (`testpaths = tests`). Em `requirements.txt` adicione `beautifulsoup4==4.12.*` e `python-multipart==0.0.*` (upload). Remova o Dockerfile antigo `COPY app` → `COPY radar ./radar`; `CMD ["uvicorn", "radar.interfaces.http.app:criar_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]`.
- [ ] **Step 4: Rode** — `pytest -q` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Esqueleto do backend Radar em camadas; remove app de licitações"`

---

### Task 2: Domínio de oportunidades e a regra de admissão

**Files:**
- Create: `radar/domain/dinheiro.py`, `radar/domain/oportunidade.py`, `radar/domain/admissao.py`, `radar/domain/erros.py`
- Test: `tests/domain/test_dinheiro.py`, `tests/domain/test_admissao.py`

**Interfaces:**
- Produces:
  - `Dinheiro(valor: Decimal, moeda: str)` — dataclass frozen; `moeda` em ISO 4217 maiúsculo.
  - `converter_para_brl(d: Dinheiro, taxas: Mapping[str, Decimal]) -> Decimal | None` — BRL devolve o próprio valor; moeda sem taxa → `None`; resultado arredondado a 2 casas.
  - `enum Modalidade(str)`: `REMOTO_TOTAL="remoto_total"`, `COM_PRESENCA="com_presenca"`, `INDEFINIDO="indefinido"`.
  - `enum TipoContratacao(str)`: `EMPRESA="empresa"`, `PESSOA_FISICA="pessoa_fisica"`.
  - `enum StatusOportunidade(str)`: `PENDENTE`, `NOVA`, `INTERESSA`, `DESCARTADA`, `DESCARTADA_AUTO` (valores em minúsculo).
  - `enum MotivoDescarteAuto(str)`: `NAO_REMOTA`, `IDIOMA`, `PRAZO_VENCIDO`, `IRRELEVANTE`.
  - `OportunidadeBruta(fonte: str, id_externo: str, titulo: str, organizacao: str, link: str, texto: str, pais: str | None = None, prazo: datetime | None = None, valor: Dinheiro | None = None, publicada_em: datetime | None = None, idioma: str | None = None)` — frozen. Método `chave_deduplicacao() -> str`: título e organização normalizados (minúsculas, sem acento, sem pontuação, espaços colapsados) + `prazo.date().isoformat()` ou `"-"`, unidos por `"|"`.
  - `Classificacao(relevante: bool, nota: int, resumo: str, modalidade: Modalidade, trecho_modalidade: str, idioma: str, tipo_contratacao: TipoContratacao, motivo: str, prazo: datetime | None = None, valor: Dinheiro | None = None)` — `nota` fora de 0..100 → `ValueError`.
  - `Oportunidade` (mutável): `id: int | None`, `bruta: OportunidadeBruta`, `coletada_em: datetime`, `status: StatusOportunidade = PENDENTE`, `classificacao: Classificacao | None = None`, `motivo_auto: MotivoDescarteAuto | None = None`, `motivo_usuario: str | None = None`, `processo_id: int | None = None`. Propriedades: `prazo` (classificação, senão bruta), `valor` (bruta, senão classificação), `pessoa_fisica: bool`.
  - `avaliar_admissao(c: Classificacao, prazo: datetime | None, agora: datetime) -> MotivoDescarteAuto | None` — checa nesta ordem: modalidade ≠ `REMOTO_TOTAL` → `NAO_REMOTA`; idioma ∉ `{"pt","en"}` → `IDIOMA`; `prazo` não nulo e `< agora` → `PRAZO_VENCIDO`; `not relevante` → `IRRELEVANTE`; senão `None`.
  - `erros.py`: `ErroDeDominio(Exception)`, `NaoEncontrado(ErroDeDominio)`, `TransicaoInvalida(ErroDeDominio)`.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_converte_usd_pela_taxa():
    assert converter_para_brl(Dinheiro(Decimal("1000"), "USD"), {"USD": Decimal("5.4321")}) == Decimal("5432.10")
def test_brl_nao_precisa_de_taxa(): ...           # == Decimal("120000")
def test_moeda_sem_taxa_devolve_none(): ...        # "CHF" → None

def test_remoto_total_em_ingles_relevante_e_admitida():
    assert avaliar_admissao(classif(modalidade=REMOTO_TOTAL, idioma="en"), prazo=None, agora=AGORA) is None
@pytest.mark.parametrize("modalidade", [Modalidade.COM_PRESENCA, Modalidade.INDEFINIDO])
def test_qualquer_presenca_ou_duvida_descarta(modalidade): ...   # == NAO_REMOTA
def test_espanhol_descarta(): ...                 # idioma="es" → IDIOMA
def test_prazo_vencido_descarta(): ...            # prazo = AGORA - 1min → PRAZO_VENCIDO
def test_sem_prazo_nao_descarta_por_prazo(): ...
def test_presenca_tem_precedencia_sobre_idioma(): ...  # com_presenca + "fr" → NAO_REMOTA
def test_irrelevante_descarta(): ...
def test_nota_fora_do_intervalo_levanta(): ...    # nota=101 → ValueError
def test_chave_ignora_acento_caixa_e_pontuacao():
    a = bruta(titulo="Sistema de Vigilância — Saúde", organizacao="OPAS")
    b = bruta(titulo="sistema de vigilancia saude", organizacao="opas.")
    assert a.chave_deduplicacao() == b.chave_deduplicacao()
```

- [ ] **Step 2: Rode** — `pytest -q tests/domain` → FAIL (imports).
- [ ] **Step 3: Implemente** os módulos acima com `dataclasses` e `enum`. Normalização com `unicodedata.normalize("NFKD")` + remoção de combinantes.
- [ ] **Step 4: Rode** — `pytest -q tests/domain` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Domínio: oportunidade, dinheiro e regra rígida de admissão"`

---

### Task 3: Domínio do funil, lembretes, contatos e perfil

**Files:**
- Create: `radar/domain/processo.py`, `radar/domain/lembrete.py`, `radar/domain/contato.py`, `radar/domain/perfil.py`
- Test: `tests/domain/test_processo.py`, `tests/domain/test_contato.py`, `tests/domain/test_lembrete.py`

**Interfaces:**
- Produces:
  - `enum Etapa(str)`: `ANALISANDO="analisando"`, `PROPOSTA_ENVIADA="proposta_enviada"`, `NEGOCIACAO="negociacao"`, `FECHADO="fechado"`, `PERDIDO="perdido"`. `ETAPAS_ABERTAS = frozenset({ANALISANDO, PROPOSTA_ENVIADA, NEGOCIACAO})`.
  - `Nota(texto: str, criada_em: datetime)`, `Arquivo(id: int | None, nome: str, chave: str, tamanho: int, enviado_em: datetime)`, `MudancaEtapa(de: Etapa | None, para: Etapa, em: datetime)`.
  - `Processo`: `id`, `titulo`, `organizacao: str | None`, `etapa: Etapa`, `criado_em`, `oportunidade_id: int | None = None`, `valor: Dinheiro | None = None`, `prazo: datetime | None = None`, `link: str | None = None`, `notas: list[Nota]`, `arquivos: list[Arquivo]`, `historico: list[MudancaEtapa]`, `contato_ids: set[int]`, `avisos_prazo_enviados: set[int]`.
    - `Processo.novo(titulo, agora, *, organizacao=None, oportunidade_id=None, valor=None, prazo=None, link=None) -> Processo` — etapa `ANALISANDO`, histórico com `MudancaEtapa(None, ANALISANDO, agora)`. Título vazio/só espaços → `ErroDeDominio`.
    - `mover(para: Etapa, agora: datetime) -> None` — mesma etapa → `TransicaoInvalida`; qualquer outra mudança é permitida (inclusive reabrir um fechado/perdido; *decisão do plano: o dono não pediu restrições*); registra histórico.
    - `aberto: bool`, `anotar(texto, agora)`, `anexar(arquivo)`, `vincular_contato(id)`.
  - `Lembrete(id, texto: str, vence_em: datetime, processo_id: int | None = None, concluido: bool = False)`; `pendente_ate(dia: date, tz: ZoneInfo) -> bool` — `not concluido and vence_em.astimezone(tz).date() <= dia`.
  - `Contato(id, nome, organizacao: str | None = None, como_conheceu: str | None = None, ultimo_contato: date | None = None, frequencia_dias: int | None = None, processo_ids: set[int])`; `atrasado(hoje: date) -> bool` — `frequencia_dias` definido e (`ultimo_contato is None` ou `hoje >= ultimo_contato + frequencia_dias`); `registrar_contato(dia: date)`.
  - `Perfil(texto: str = "", faixa_min_brl: Decimal | None = None, faixa_max_brl: Decimal | None = None)`.
  - `Ajustes(limiar_alerta: int = 85, horario_resumo: time = time(7, 30), avisos_prazo_dias: tuple[int, ...] = (3, 1))` — `limiar_alerta` fora de 0..100 → `ValueError`.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_novo_processo_comeca_analisando_com_historico(): ...
def test_mover_registra_historico():
    p = Processo.novo("CRM", T0); p.mover(Etapa.PROPOSTA_ENVIADA, T1)
    assert p.historico[-1] == MudancaEtapa(Etapa.ANALISANDO, Etapa.PROPOSTA_ENVIADA, T1)
def test_mover_para_mesma_etapa_levanta(): ...
def test_fechado_pode_ser_reaberto(): ...
def test_aberto_somente_nas_tres_primeiras_etapas(): ...
def test_titulo_vazio_levanta(): ...
def test_contato_sem_frequencia_nunca_atrasa(): ...
def test_contato_atrasa_no_dia_em_que_vence():
    c = Contato(None, "Ana", ultimo_contato=date(2026, 9, 23), frequencia_dias=30)
    assert not c.atrasado(date(2026, 10, 22)) and c.atrasado(date(2026, 10, 23))
def test_contato_nunca_contatado_com_frequencia_esta_atrasado(): ...
def test_lembrete_concluido_nao_e_pendente(): ...
```

- [ ] **Step 2: Rode** — `pytest -q tests/domain` → FAIL.
- [ ] **Step 3: Implemente** os quatro módulos.
- [ ] **Step 4: Rode** — `pytest -q tests/domain` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Domínio: processo e etapas, lembrete, contato, perfil e ajustes"`

---

### Task 4: Portas, fakes e o caso de uso ColetarOportunidades

**Files:**
- Create: `radar/application/portas.py`, `radar/application/coletar.py`, `tests/fakes.py`
- Test: `tests/application/test_coletar.py`

**Interfaces:**
- Produces (`portas.py`, todos `Protocol`):
  - `Relogio.agora() -> datetime` (aware, UTC).
  - `FonteDeOportunidades`: atributo `nome: str`; `buscar(desde: date) -> list[OportunidadeBruta]`.
  - `DescarteRecente(titulo: str, motivo: str)` (dataclass aqui mesmo).
  - `Classificador.classificar(bruta: OportunidadeBruta, perfil: Perfil, descartes: list[DescarteRecente]) -> Classificacao` — falha levanta `ClassificacaoIndisponivel` (exceção definida em `portas.py`).
  - `Notificador.enviar(titulo: str, corpo: str, url: str) -> int`.
  - `ExecucaoFonte(fonte: str, iniciada_em: datetime, finalizada_em: datetime, recebidas: int, novas: int, erro: str | None)`.
  - Repositórios:
    - `RepositorioOportunidades`: `adicionar(op) -> Oportunidade`, `obter(id) -> Oportunidade | None`, `salvar(op)`, `existe_chave(chave: str) -> bool`, `pendentes(limite: int) -> list[Oportunidade]`, `listar(status: StatusOportunidade, limite: int | None = None) -> list[Oportunidade]` (ordem: nota desc, prazo asc com nulos no fim), `contar_novas_desde(desde: datetime) -> int`, `descartes_recentes(limite: int = 20) -> list[DescarteRecente]` (só `DESCARTADA` com `motivo_usuario`).
    - `RepositorioProcessos`: `adicionar`, `obter`, `salvar`, `listar() -> list[Processo]`.
    - `RepositorioLembretes`: `adicionar`, `obter`, `salvar`, `remover(id)`, `nao_concluidos() -> list[Lembrete]`, `do_processo(processo_id) -> list[Lembrete]`.
    - `RepositorioContatos`: `adicionar`, `obter`, `salvar`, `listar()`.
    - `RepositorioConfiguracoes`: `perfil() -> Perfil`, `salvar_perfil(p)`, `ajustes() -> Ajustes`, `salvar_ajustes(a)`, `obter_estado(chave: str) -> str | None`, `salvar_estado(chave: str, valor: str)`.
    - `RepositorioExecucoes`: `registrar(e: ExecucaoFonte)`, `ultimas_por_fonte() -> list[ExecucaoFonte]`.
    - `RepositorioCotacoes`: `salvar(moeda: str, dia: date, valor: Decimal)`, `mais_recentes() -> dict[str, Decimal]`.
  - `UnidadeDeTrabalho`: atributos `oportunidades`, `processos`, `lembretes`, `contatos`, `configuracoes`, `execucoes`, `cotacoes`; `commit()`, `rollback()`; usável como context manager (`__enter__/__exit__` faz rollback em exceção).
- Produces (`coletar.py`):
  - `ResumoColeta(novas: int, admitidas: int, descartadas_auto: int, pendentes: int, alertas: int, erros: dict[str, str])`.
  - `ColetarOportunidades(uow, fontes: list[FonteDeOportunidades], classificador: Classificador | None, notificador: Notificador, relogio: Relogio, app_url: str, max_classificacoes: int = 60)`; `executar(desde: date) -> ResumoColeta`.
    1. Para cada fonte: `buscar(desde)` dentro de `try`; exceção → registra `ExecucaoFonte` com `erro=str(e)` e segue. Brutas com `chave_deduplicacao()` já existente são ignoradas (inclusive repetidas no mesmo lote). As novas são salvas como `PENDENTE`. Registra execução com `recebidas`/`novas`. Commit por fonte.
    2. Se `classificador is None`: para aqui (pendentes ficam pendentes).
    3. Classifica até `max_classificacoes` pendentes com `perfil()` e `descartes_recentes()`. `ClassificacaoIndisponivel` → continua pendente. Senão aplica `avaliar_admissao(c, op.prazo, agora)` → `NOVA` ou `DESCARTADA_AUTO` + `motivo_auto`.
    4. Admitida com `nota >= ajustes().limiar_alerta` → `notificador.enviar(f"Oportunidade com nota {nota}", f"{titulo} — {organizacao}", f"{app_url}/entrada/{id}")`.
  - `tests/fakes.py`: `UnidadeDeTrabalhoEmMemoria` (implementa todos os repositórios com dicts e ids sequenciais; `commits: int`), `FonteFalsa(nome, brutas, erro=None)`, `ClassificadorFalso(respostas: dict[str id_externo, Classificacao | Exception])`, `NotificadorFalso` (guarda `enviadas: list[tuple]`), `RelogioFixo(agora)`.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_admite_remota_e_descarta_presencial(): ...      # 2 brutas → 1 NOVA, 1 DESCARTADA_AUTO(NAO_REMOTA)
def test_nao_duplica_na_segunda_coleta(): ...             # executar 2x → resumo.novas == 0 na segunda
def test_deduplica_entre_fontes(): ...                     # mesma chave em FonteFalsa("ungm") e FonteFalsa("opas") → 1 oportunidade
def test_falha_de_uma_fonte_nao_interrompe_as_outras():
    r = coletar(fontes=[FonteFalsa("ruim", [], erro=RuntimeError("layout mudou")), FonteFalsa("boa", [bruta()])])
    assert r.erros == {"ruim": "layout mudou"} and r.novas == 1
    assert {e.fonte: e.erro for e in uow.execucoes.ultimas_por_fonte()}["ruim"] == "layout mudou"
def test_falha_do_classificador_mantem_pendente(): ...    # ClassificacaoIndisponivel → status PENDENTE; próxima execução com resposta válida → NOVA
def test_sem_classificador_nada_entra_na_entrada(): ...   # classificador=None → listar(NOVA) == []
def test_respeita_teto_de_classificacoes(): ...           # 5 pendentes, max=2 → 2 classificadas, 3 pendentes
def test_alerta_quando_nota_atinge_limiar(): ...          # nota 85 → 1 envio; nota 84 → nenhum; url termina com "/entrada/<id>"
def test_descarte_automatico_nunca_alerta(): ...          # nota 99 presencial → nenhum envio
def test_classificador_recebe_descartes_recentes(): ...
```

- [ ] **Step 2: Rode** — `pytest -q tests/application/test_coletar.py` → FAIL.
- [ ] **Step 3: Implemente** `portas.py`, `fakes.py` e `coletar.py`.
- [ ] **Step 4: Rode** — `pytest -q` → PASS (incluindo o teste de arquitetura).
- [ ] **Step 5: Commit** — `git commit -m "Aplicação: portas e coleta com deduplicação, classificação e alerta"`

---

### Task 5: Triagem, funil, lembretes e rede

**Files:**
- Create: `radar/application/triar.py`, `radar/application/funil.py`, `radar/application/rede.py`
- Modify: `radar/application/portas.py` (adicione a porta `ArmazenamentoArquivos`)
- Test: `tests/application/test_triar.py`, `tests/application/test_funil.py`, `tests/application/test_rede.py`

**Interfaces:**
- Consumes: Task 3 e Task 4.
- Produces:
  - `ArmazenamentoArquivos.salvar(nome: str, conteudo: bytes) -> str` (chave) e `abrir(chave: str) -> bytes`.
  - `triar.py`: `TriarOportunidade(uow, relogio)` com `interessa(oportunidade_id: int) -> Processo` (cria `Processo.novo` com título, organização, valor, prazo, link e `oportunidade_id`; marca `INTERESSA` e `processo_id`) e `descartar(oportunidade_id: int, motivo: str | None) -> None` (motivo vazio vira `None`). Só `NOVA` pode ser triada → senão `TransicaoInvalida`; id inexistente → `NaoEncontrado`.
  - `funil.py`, classe `Funil(uow, relogio, armazenamento: ArmazenamentoArquivos)`:
    - `criar_manual(titulo: str, organizacao: str | None, valor: Dinheiro | None, prazo: datetime | None) -> Processo`
    - `editar(processo_id, *, titulo=None, organizacao=None, valor=None, prazo=None, link=None) -> Processo` (mudar `prazo` limpa `avisos_prazo_enviados`)
    - `mover(processo_id, etapa: Etapa) -> Processo`
    - `anotar(processo_id, texto: str) -> Processo`
    - `anexar(processo_id, nome: str, conteudo: bytes) -> Arquivo`
    - `abrir_arquivo(processo_id, arquivo_id) -> tuple[Arquivo, bytes]`
    - `vincular_contato(processo_id, contato_id) -> None` (atualiza os dois lados)
    - `criar_lembrete(texto: str, vence_em: datetime, processo_id: int | None) -> Lembrete`, `concluir_lembrete(id) -> Lembrete`, `remover_lembrete(id)`.
  - `rede.py`, classe `Rede(uow, relogio, tz: ZoneInfo)`: `criar(nome, organizacao=None, como_conheceu=None, frequencia_dias=None) -> Contato`, `editar(id, **campos) -> Contato`, `registrar_contato(id) -> Contato` (usa `hoje` no fuso), `listar() -> list[Contato]` (atrasados primeiro, depois por nome).

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_interessa_cria_processo_analisando_com_dados_da_oportunidade(): ...
def test_triar_duas_vezes_levanta_transicao_invalida(): ...
def test_descartar_guarda_motivo_e_entra_nos_descartes_recentes(): ...
def test_descartar_com_motivo_em_branco_guarda_none(): ...
def test_criar_manual_sem_oportunidade(): ...
def test_mudar_prazo_reinicia_avisos(): ...
def test_anexar_salva_no_armazenamento_e_reabre(): ...
def test_vincular_contato_atualiza_os_dois_lados(): ...
def test_processo_inexistente_levanta_nao_encontrado(): ...
def test_rede_lista_atrasados_primeiro(): ...
def test_registrar_contato_usa_dia_de_brasilia(): ...   # agora = 2026-10-24T01:00Z → ultimo_contato == date(2026,10,23)
```

- [ ] **Step 2: Rode** → FAIL.
- [ ] **Step 3: Implemente**; cada método abre `with uow:`, faz a operação e dá `commit()`.
- [ ] **Step 4: Rode** — `pytest -q` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Aplicação: triagem, funil, lembretes e rede"`

---

### Task 6: Painel do dia, resumo diário, avisos de prazo e cotações

**Files:**
- Create: `radar/application/painel.py`, `radar/application/notificacoes.py`, `radar/application/cotacoes.py`
- Modify: `radar/application/portas.py` (adicione `FonteDeCotacoes.cotacao(moeda: str, ate: date) -> tuple[date, Decimal] | None`)
- Test: `tests/application/test_painel.py`, `tests/application/test_notificacoes.py`, `tests/application/test_cotacoes.py`

**Interfaces:**
- Produces:
  - `ItemParaFazer(tipo: Literal["lembrete", "prazo", "contato"], titulo: str, quando: datetime | date | None, ref_id: int, processo_id: int | None)`.
  - `ResumoFunil(contagem: dict[Etapa, int], valor_aberto_brl: Decimal, sem_conversao: int)` — `sem_conversao` conta processos abertos com valor numa moeda sem taxa.
  - `PainelDoDia(dia: date, para_fazer: list[ItemParaFazer], funil: ResumoFunil, melhores_novas: list[Oportunidade])`.
  - `MontarPainelDoDia(uow, relogio, tz).executar() -> PainelDoDia`:
    - lembretes `pendente_ate(hoje)`, ordenados por `vence_em`;
    - processos abertos com `prazo` entre agora e `hoje + max(avisos_prazo_dias)` dias (título `f"Prazo: {p.titulo}"`);
    - contatos `atrasado(hoje)` (título `f"Falar com {nome}"`);
    - ordem final: lembretes, prazos, contatos;
    - `melhores_novas`: `listar(NOVA, limite=5)`.
  - `notificacoes.py`:
    - `textos_resumo(novas: int, tarefas: int) -> str` — exatamente `"{n} oportunidade(s) nova(s), {m} tarefa(s) para hoje"` com singular/plural: `1 oportunidade nova`, `2 oportunidades novas`, `1 tarefa para hoje`, `0 tarefas para hoje`.
    - `EnviarResumoDiario(uow, notificador, relogio, tz, app_url).executar() -> bool` — envia no máximo uma vez por dia, só quando a hora local `>= ajustes().horario_resumo`. Guarda o dia em `salvar_estado("ultimo_resumo", iso)`. Novas = `contar_novas_desde(agora - 24h)`. Tarefas = `len(painel.para_fazer)`. Se ambos forem 0, não envia, mas marca o dia. Título `"Radar · bom dia"`, url `f"{app_url}/hoje"`.
    - `VerificarPrazos(uow, notificador, relogio, tz, app_url).executar() -> int` — para cada processo aberto com prazo e cada `d` em `avisos_prazo_dias` com `d not in avisos_prazo_enviados` e `(prazo_local.date() - hoje).days <= d`, envia `f"Prazo em {dias} dia(s): {titulo}"` (texto do corpo: data local `dd/mm HH:MM`), adiciona `d` e salva. Prazo já passado não avisa.
  - `AtualizarCotacoes(uow, fonte: FonteDeCotacoes, relogio, moedas=("USD", "EUR")).executar() -> int` — salva o que vier; `None` mantém a anterior.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_lembrete_23h30_brt_aparece_hoje():
    agora = datetime(2026, 10, 23, 15, 0, tzinfo=UTC)
    lembrete(vence_em=datetime(2026, 10, 24, 2, 30, tzinfo=UTC))   # 23:30 BRT de 23/10
    assert [i.tipo for i in painel(agora).para_fazer] == ["lembrete"]
def test_lembrete_de_amanha_nao_aparece(): ...
def test_ordem_lembretes_prazos_contatos(): ...
def test_valor_aberto_converte_e_ignora_fechados():
    # aberto 120000 BRL + aberto 1000 USD @5.00 + fechado 999 BRL → 125000.00; sem_conversao == 0
def test_moeda_sem_taxa_conta_em_sem_conversao(): ...
def test_melhores_novas_no_maximo_cinco_por_nota(): ...
@pytest.mark.parametrize("n,m,esperado", [(1, 1, "1 oportunidade nova, 1 tarefa para hoje"), (3, 0, "3 oportunidades novas, 0 tarefas para hoje")])
def test_textos_resumo(n, m, esperado): ...
def test_resumo_antes_do_horario_nao_envia(): ...   # 07:29 BRT → False
def test_resumo_envia_uma_vez_por_dia(): ...        # 07:30 e 09:00 → 1 envio
def test_resumo_vazio_nao_envia(): ...
def test_aviso_de_prazo_3_e_1_dia_sem_repetir(): ...  # prazo em 2,5 dias → avisa "3"; mesma hora de novo → nada; a 0,9 dia → avisa "1"
def test_prazo_passado_nao_avisa(): ...
def test_cotacao_indisponivel_mantem_anterior(): ...
```

- [ ] **Step 2: Rode** → FAIL.
- [ ] **Step 3: Implemente** os três módulos.
- [ ] **Step 4: Rode** — `pytest -q` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Aplicação: painel do dia, resumo diário, avisos de prazo e cotações"`

---

### Task 7: Persistência SQLAlchemy

**Files:**
- Create: `radar/infrastructure/db/__init__.py`, `radar/infrastructure/db/tabelas.py`, `radar/infrastructure/db/repositorios.py`
- Test: `tests/infrastructure/test_repositorios_sql.py`

**Interfaces:**
- Consumes: todas as portas de repositório e `UnidadeDeTrabalho` da Task 4 (+ `ArmazenamentoArquivos` não entra aqui).
- Produces:
  - `criar_engine(url: str) -> Engine` (SQLite com `check_same_thread=False`), `criar_tabelas(engine)` (usa `metadata.create_all`; sem Alembic, já que o banco começa vazio).
  - `UnidadeDeTrabalhoSql(fabrica_sessao: sessionmaker)`, que implementa o protocolo e abre uma sessão nova a cada `__enter__`.
  - Tabelas: `oportunidades` (com coluna `chave` única e indexada, classificação em colunas próprias, `valor_valor Numeric(14,2)`/`valor_moeda`), `processos`, `processo_notas`, `processo_arquivos`, `processo_historico`, `processo_contatos`, `lembretes`, `contatos`, `configuracoes` (chave → JSON), `execucoes_fonte`, `cotacoes` (moeda, dia, valor; PK moeda+dia), `inscricoes_push` (endpoint único, p256dh, auth, user_agent, criado_em).
  - Os repositórios convertem ORM ↔ domínio em funções `_para_dominio`/`_para_linha` privadas. Nenhuma linha ORM sai da infraestrutura.

- [ ] **Step 1: Escreva os testes** com SQLite em memória (`sqlite+pysqlite:///:memory:` com `StaticPool`). Rode **a mesma bateria de comportamento** contra `UnidadeDeTrabalhoEmMemoria` e `UnidadeDeTrabalhoSql` via `@pytest.fixture(params=["memoria", "sql"])`. Isso garante que os fakes das Tasks 4 a 6 se comportam igual ao banco.

```python
def test_oportunidade_ida_e_volta_preserva_classificacao_e_dinheiro(uow): ...
def test_existe_chave(uow): ...
def test_listar_ordena_por_nota_desc_e_prazo_nulo_no_fim(uow): ...
def test_descartes_recentes_so_com_motivo_do_usuario(uow): ...
def test_processo_ida_e_volta_com_notas_arquivos_historico_contatos_e_avisos(uow): ...
def test_ajustes_padrao_quando_vazio(uow):  assert uow.configuracoes.ajustes() == Ajustes()
def test_cotacoes_mais_recentes_por_moeda(uow): ...
def test_rollback_em_excecao(uow): ...
```

- [ ] **Step 2: Rode** → FAIL (fixture `sql`).
- [ ] **Step 3: Implemente** tabelas e repositórios.
- [ ] **Step 4: Rode** — `pytest -q` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Infra: persistência SQLAlchemy com bateria compartilhada com os fakes"`

---

### Task 8: Classificador Claude

**Files:**
- Create: `radar/infrastructure/ia/__init__.py`, `radar/infrastructure/ia/claude.py`
- Test: `tests/infrastructure/test_classificador_claude.py`

**Interfaces:**
- Consumes: `Classificador`, `ClassificacaoIndisponivel`, `DescarteRecente` (Task 4).
- Produces: `ClassificadorClaude(cliente, modelo: str)` — `cliente` é qualquer objeto com `messages.create(...)` (o SDK `anthropic.Anthropic` em produção, um falso nos testes). `criar_classificador(settings) -> ClassificadorClaude | None` devolve `None` quando a chave está vazia.
  - Prompt de sistema em português, com estas instruções fixas:
    - responda só JSON com as chaves `relevante, nota, resumo, modalidade, trecho_modalidade, idioma, tipo_contratacao, prazo, valor, moeda, motivo`;
    - `modalidade = "remoto_total"` **somente** se o texto disser explicitamente que todo o trabalho é remoto e não houver nenhuma viagem, missão, reunião presencial, exigência de residência ou de local, nem formato híbrido. Se houver qualquer um desses, `"com_presenca"`. Se o texto não disser nada, `"indefinido"`;
    - `idioma` é o código ISO 639-1 do texto da chamada;
    - `resumo` em português, 2–3 frases;
    - `nota` 0–100 considerando o Perfil, a faixa de valor e os descartes recentes;
    - `tipo_contratacao`: `"pessoa_fisica"` quando a chamada for para consultor individual, senão `"empresa"`.
  - A mensagem do usuário contém o Perfil, até 20 descartes recentes (`- título: motivo`) e a chamada (título, organização, país, prazo, valor, texto truncado em 12.000 caracteres).
  - `max_tokens=700`. O parse aceita cercas ```json, valida enums e converte `prazo` (ISO 8601; sem fuso → UTC) e `valor`+`moeda` em `Dinheiro`. Qualquer erro de API, JSON ou validação levanta `ClassificacaoIndisponivel`.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_converte_resposta_valida_em_classificacao(): ...
def test_aceita_resposta_dentro_de_cerca_json(): ...
def test_resposta_sem_json_levanta_erro(): ...                  # "Desculpe..." → ClassificacaoIndisponivel
def test_modalidade_desconhecida_levanta_erro(): ...            # "hibrido" → ClassificacaoIndisponivel
def test_erro_da_api_levanta_classificacao_indisponivel(): ...
def test_prompt_contem_regra_rigida_e_descartes(): ...          # system contém "remoto_total" e "missão"; user contém "- Portal X: muito pequeno"
def test_texto_longo_e_truncado(): ...
def test_sem_chave_nao_cria_classificador(): ...
```

- [ ] **Step 2: Rode** → FAIL.
- [ ] **Step 3: Implemente.**
- [ ] **Step 4: Rode** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Infra: classificador Claude com regra rígida de remoto"`

---

### Task 9: Web Push, PTAX e armazenamento de arquivos

**Files:**
- Create: `radar/infrastructure/push/webpush.py`, `radar/infrastructure/cotacoes/ptax.py`, `radar/infrastructure/arquivos/disco.py` (+ `__init__.py` de cada pasta)
- Test: `tests/infrastructure/test_webpush.py`, `tests/infrastructure/test_ptax.py`, `tests/infrastructure/test_disco.py`, `tests/fixtures/ptax/usd.json`

**Interfaces:**
- Produces:
  - `NotificadorWebPush(fabrica_sessao, vapid_private_key, vapid_subject, enviar=pywebpush.webpush)` implementa `Notificador`. Sem VAPID, devolve 0 e registra log. Também expõe `inscrever(endpoint, p256dh, auth, user_agent)`, com upsert por endpoint.
  - `FontePtax(http: httpx.Client)` implementa `FonteDeCotacoes`. Consulta `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='MM-DD-YYYY'&$format=json`, usa `cotacaoVenda` do último boletim do dia e recua até 7 dias para trás quando a lista vem vazia (fim de semana/feriado). Erro HTTP → `None`.
  - `ArmazenamentoEmDisco(raiz: Path)` implementa `ArmazenamentoArquivos`. A chave é `uuid4().hex`, e o nome original não é usado no caminho.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_inscricao_expirada_e_removida():
    # 2 inscrições; enviar falso levanta WebPushException com response.status_code=410 para a primeira
    assert notificador.enviar("t", "c", "/") == 1 and contar_inscricoes() == 1
def test_sem_vapid_nao_envia(): ...
def test_inscrever_duas_vezes_mesmo_endpoint_nao_duplica(): ...
def test_ptax_usa_ultimo_boletim(): ...            # fixture com 5 boletins → valor do último
def test_ptax_recua_no_fim_de_semana(): ...        # httpx.MockTransport: sábado e sexta vazios, quinta com valor
def test_ptax_erro_http_devolve_none(): ...
def test_disco_salva_e_abre_sem_usar_nome_original(tmp_path): ...
```

Grave `tests/fixtures/ptax/usd.json` a partir de uma chamada real: `curl "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='USD'&@dataCotacao='10-22-2026'&\$format=json"`.

- [ ] **Step 2: Rode** → FAIL.
- [ ] **Step 3: Implemente.**
- [ ] **Step 4: Rode** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "Infra: web push, cotação PTAX e arquivos em disco"`

---

### Tasks 10–12: Fontes de oportunidade

Mesmo roteiro nas três tarefas. Cada adaptador recebe `http: httpx.Client`, expõe `nome` e implementa `buscar(desde: date) -> list[OportunidadeBruta]`. Ele levanta exceção quando o formato não é reconhecido (por exemplo, nenhuma linha ou chave esperada encontrada numa resposta 200), para que a falha apareça em Ajustes e não vire uma lista vazia silenciosa. Os testes usam `httpx.MockTransport` servindo respostas reais gravadas em `tests/fixtures/fontes/<nome>/`.

**Passo 0, em todas: viabilidade.** Antes de escrever o adaptador, consulte a fonte de verdade (curl ou o navegador, inspecionando as requisições XHR da página), leia os termos de uso e grave 1–2 respostas reais como fixtures. Se a fonte for inviável (bloqueio, CAPTCHA, termos que proíbem coleta automática, exigência de cadastro que o dono não tem), **não implemente**. Escreva `docs/fontes/<nome>.md` com o motivo e as evidências, faça o commit e passe para a próxima tarefa. Isso conta como tarefa concluída.

#### Task 10: UNGM

**Files:** Create `radar/infrastructure/fontes/__init__.py`, `radar/infrastructure/fontes/ungm.py`; Test `tests/infrastructure/fontes/test_ungm.py`, `tests/fixtures/fontes/ungm/*`

**Interfaces:** `FonteUngm(http, consultas: list[ConsultaUngm])`, `nome = "ungm"`; `ConsultaUngm(pais: str | None, palavras: tuple[str, ...])`. Configuração padrão em `container.py`: `ConsultaUngm(pais="Brazil", palavras=())` e `ConsultaUngm(pais=None, palavras=("software", "information technology", "digital platform", "web development", "database"))`.

A busca pública fica em `https://www.ungm.org/Public/Notice`. Reproduza a requisição de busca da página (POST que devolve HTML parcial) com filtro de prazo ainda aberto e publicação `>= desde`. `id_externo` = id numérico do aviso; `link = f"https://www.ungm.org/Public/Notice/{id}"`; `texto` = título + descrição + tipo de aviso + país, e, se a página de detalhe estiver acessível, o texto dela (no máximo 1 requisição de detalhe por aviso novo, com pausa de 1 s entre requisições).

- [ ] **Step 1: Viabilidade e fixtures** (passo 0).
- [ ] **Step 2: Testes que falham:** `test_extrai_avisos_da_lista`, que confere id, título, organização (agência), país e prazo convertido para UTC; `test_link_aponta_para_o_aviso`; `test_html_sem_tabela_levanta_erro`; `test_aplica_as_duas_consultas_e_junta_resultados`.
- [ ] **Step 3: Rode** → FAIL. **Step 4: Implemente** com `bs4`. **Step 5: Rode** → PASS.
- [ ] **Step 6: Commit** — `git commit -m "Fonte UNGM"`

#### Task 11: Página de oportunidades da OPAS no Brasil

**Files:** Create `radar/infrastructure/fontes/opas.py`; Test `tests/infrastructure/fontes/test_opas.py`, `tests/fixtures/fontes/opas/*`

**Interfaces:** `FonteOpas(http)`, `nome = "opas"`. Lê `https://www.paho.org/pt/licitacoes-opas`: cada item com título, prazo de propostas e link (geralmente para o UNGM ou um PDF). `organizacao = "OPAS/OMS Brasil"`, `pais = "Brasil"`, `idioma = "pt"`. `id_externo` = o link absoluto. Quando o mesmo aviso também vier do UNGM, a deduplicação por chave da Task 4 resolve.

- [ ] **Step 1: Viabilidade e fixtures.**
- [ ] **Step 2: Testes que falham:** `test_extrai_itens_com_prazo_em_formato_brasileiro` (`"08/10/2026"` → datetime 23:59 BRT em UTC), `test_ignora_itens_com_prazo_passado_em_relacao_a_desde`, `test_pagina_sem_lista_levanta_erro`.
- [ ] **Step 3–5: Rode/implemente/rode.**
- [ ] **Step 6: Commit** — `git commit -m "Fonte OPAS Brasil"`

#### Task 12: ReliefWeb e Banco Mundial

**Files:** Create `radar/infrastructure/fontes/reliefweb.py`, `radar/infrastructure/fontes/banco_mundial.py`; Test `tests/infrastructure/fontes/test_reliefweb.py`, `tests/infrastructure/fontes/test_banco_mundial.py`, fixtures

**Interfaces:**
- `FonteReliefWeb(http, appname: str)`, `nome = "reliefweb"`. API `https://api.reliefweb.int/v2/jobs`. Filtre por `type: Consultancy`, temas/carreira de TI (`career_categories: Information and Communications Technology`) e `date.created >= desde`, pedindo os campos `title, body, source, country, date.closing, url, language`. Verifique se o `appname` precisa ser pré-aprovado; se precisar e não houver um, registre em `docs/fontes/reliefweb.md` e pare (passo 0). Adicione `reliefweb_appname: str = ""` em `Settings`; vazio → fonte não registrada no container.
- `FonteBancoMundial(http)`, `nome = "banco_mundial"`. API de avisos de aquisição `https://search.worldbank.org/api/v2/procnotices?format=json`. Filtre por `notice_type` de consultoria (Request for Expression of Interest) e data `>= desde`. `organizacao = "Banco Mundial — " + project_name`.

- [ ] **Step 1: Viabilidade e fixtures das duas.**
- [ ] **Step 2: Testes que falham:** para cada uma, `test_converte_itens_em_oportunidades_brutas`, `test_resposta_com_formato_inesperado_levanta_erro`; e, para ReliefWeb, `test_body_html_vira_texto_plano`.
- [ ] **Step 3–5: Rode/implemente/rode.**
- [ ] **Step 6: Commit** — `git commit -m "Fontes ReliefWeb e Banco Mundial"`

---

### Task 13: API HTTP, parte 1 (app, login, entrada, painel, perfil, ajustes e status)

**Files:**
- Create: `radar/container.py`, `radar/interfaces/http/__init__.py`, `app.py`, `auth.py`, `dtos.py`, `rotas_oportunidades.py`, `rotas_painel.py`, `rotas_ajustes.py`
- Test: `tests/http/conftest.py`, `tests/http/test_oportunidades.py`, `tests/http/test_painel_ajustes.py`

**Interfaces:**
- Consumes: casos de uso das Tasks 4–6 e adaptadores das Tasks 7–12.
- Produces:
  - `Container(settings, fabrica_sessao, relogio, notificador, classificador, fontes, armazenamento)` com métodos-fábrica `uow()`, `triar()`, `funil()`, `rede()`, `painel()`, `coletar()`, `resumo_diario()`, `verificar_prazos()`, `atualizar_cotacoes()`. `Container.de_settings(settings) -> Container` monta tudo de verdade. Os testes montam com fakes e SQLite.
  - `criar_app(container: Container | None = None) -> FastAPI`. Handlers globais: `NaoEncontrado` → 404, `TransicaoInvalida`/`ErroDeDominio`/`ValueError` → 422 `{"detail": msg}`.
  - Rotas (todas sob `/api` e protegidas por JWT, exceto login e health):
    - `GET /api/health` → `{"ok": true}`
    - `POST /api/auth/login {senha}` → `{token}`; senha errada → 401.
    - `GET /api/oportunidades?status=nova` → `list[OportunidadeDTO]`. `OportunidadeDTO`: `id, titulo, organizacao, pais, link, prazo, valor: {valor, moeda} | null, valor_brl, nota, resumo, motivo, pessoa_fisica, fonte, status, processo_id`.
    - `GET /api/oportunidades/{id}` → DTO + `texto` e `trecho_modalidade`.
    - `POST /api/oportunidades/{id}/interessa` → `ProcessoDTO` (formato definido na Task 14, declarado em `dtos.py` já agora).
    - `POST /api/oportunidades/{id}/descartar {motivo?}` → 204.
    - `GET /api/painel` → `{dia, para_fazer: [{tipo, titulo, quando, ref_id, processo_id}], funil: {contagem: {etapa: n}, valor_aberto_brl, sem_conversao}, melhores_novas: [OportunidadeDTO]}`.
    - `GET/PUT /api/perfil` → `{texto, faixa_min_brl, faixa_max_brl}`.
    - `GET/PUT /api/ajustes` → `{limiar_alerta, horario_resumo: "HH:MM", avisos_prazo_dias: [int]}`.
    - `GET /api/status` → `{ia_configurada, push_configurado, fontes: [{fonte, finalizada_em, recebidas, novas, erro}]}`.
  - `valor_brl` usa `converter_para_brl` com `cotacoes.mais_recentes()`.

- [ ] **Step 1: Escreva os testes que falham** (TestClient + container com SQLite e fakes)

```python
def test_sem_token_401(cliente): ...
def test_login_errado_401(cliente): ...
def test_lista_so_novas_ordenadas_por_nota(cliente_logado): ...
def test_pessoa_fisica_vem_marcada(cliente_logado): ...
def test_interessa_devolve_processo_e_some_da_entrada(cliente_logado): ...
def test_triar_duas_vezes_422(cliente_logado): ...
def test_oportunidade_inexistente_404(cliente_logado): ...
def test_painel_formato(cliente_logado): ...
def test_ajustes_limiar_invalido_422(cliente_logado): ...       # 101
def test_status_sem_ia(cliente_logado_sem_classificador):  assert r.json()["ia_configurada"] is False
```

- [ ] **Step 2: Rode** → FAIL. **Step 3: Implemente.** **Step 4: Rode** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "API: login, entrada, painel, perfil, ajustes e status"`

---

### Task 14: API HTTP, parte 2 (funil, lembretes, rede, arquivos e push)

**Files:**
- Create: `radar/interfaces/http/rotas_processos.py`, `rotas_lembretes.py`, `rotas_contatos.py`, `rotas_push.py`
- Test: `tests/http/test_processos.py`, `tests/http/test_lembretes_contatos.py`, `tests/http/test_push.py`

**Interfaces:**
- `ProcessoDTO`: `id, titulo, organizacao, etapa, valor, valor_brl, prazo, link, oportunidade_id, criado_em, notas: [{texto, criada_em}], arquivos: [{id, nome, tamanho, enviado_em}], historico: [{de, para, em}], contato_ids, lembretes: [LembreteDTO]`. `LembreteDTO`: `id, texto, vence_em, processo_id, concluido`. `ContatoDTO`: `id, nome, organizacao, como_conheceu, ultimo_contato, frequencia_dias, atrasado, processo_ids`.
- Rotas:
  - `GET /api/processos` (sem notas/arquivos/histórico: `ProcessoResumoDTO` = id, titulo, organizacao, etapa, valor, valor_brl, prazo) · `POST /api/processos {titulo, organizacao?, valor?, prazo?}` · `GET /api/processos/{id}` · `PATCH /api/processos/{id}` · `POST /api/processos/{id}/etapa {etapa}` · `POST /api/processos/{id}/notas {texto}` · `POST /api/processos/{id}/arquivos` (multipart `arquivo`) · `GET /api/processos/{id}/arquivos/{arquivo_id}` (download com `Content-Disposition` usando o nome sanitizado) · `POST /api/processos/{id}/contatos/{contato_id}`
  - `GET /api/lembretes?pendentes=true` · `POST /api/lembretes {texto, vence_em, processo_id?}` · `POST /api/lembretes/{id}/concluir` · `DELETE /api/lembretes/{id}`
  - `GET /api/contatos` · `POST /api/contatos` · `PATCH /api/contatos/{id}` · `POST /api/contatos/{id}/registrar-contato`
  - `GET /api/push/chave-publica` → `{chave}` · `POST /api/push/inscrever {endpoint, keys: {p256dh, auth}}` · `POST /api/push/teste` → `{entregues}`
- Upload: lê no máximo `arquivo_max_mb * 1024 * 1024 + 1` bytes; acima disso → 413. O nome é sanitizado com `Path(nome).name`, troca de caracteres fora de `[\w.\- ]` por `_` e corte em 120 caracteres; vazio vira `"arquivo"`.

- [ ] **Step 1: Escreva os testes que falham**

```python
def test_criar_manual_mover_e_ver_historico(cliente_logado): ...
def test_etapa_invalida_422(cliente_logado): ...                       # "ganho"
def test_upload_e_download(cliente_logado): ...
def test_upload_nome_com_caminho_e_sanitizado(cliente_logado):
    r = enviar(nome="../../etc/passwd")
    assert r.json()["nome"] == "passwd"
def test_upload_maior_que_limite_413(cliente_logado_limite_1mb): ...
def test_lembrete_concluir_some_dos_pendentes(cliente_logado): ...
def test_contato_registrar_contato_zera_atraso(cliente_logado): ...
def test_vincular_contato_aparece_nos_dois_lados(cliente_logado): ...
def test_push_inscrever_e_testar(cliente_logado): ...
```

- [ ] **Step 2: Rode** → FAIL. **Step 3: Implemente.** **Step 4: Rode** → PASS.
- [ ] **Step 5: Commit** — `git commit -m "API: funil, lembretes, rede, arquivos e push"`

---

### Task 15: Worker, seed de demonstração e infraestrutura

**Files:**
- Create: `radar/interfaces/worker.py`, `radar/interfaces/seed_demo.py`, `radar/interfaces/gen_vapid.py`
- Modify: `docker-compose.yml` (worker: `python -m radar.interfaces.worker`; volume `arquivos:/data/arquivos` em `api`), `.env.example` (remova as variáveis do PNCP e `LEMBRETE_HORAS_ANTES`; adicione `ARQUIVOS_DIR`, `ARQUIVO_MAX_MB`, `RELIEFWEB_APPNAME`; `DOMAIN=radar.seudominio.com.br`)
- Test: `tests/interfaces/test_worker.py`

**Interfaces:**
- `registrar_jobs(agendador, container) -> None`:
  - `coleta`: cron nas horas de `coleta_horarios`, minuto 5, `desde = hoje - 2 dias`;
  - `resumo`: a cada 15 min;
  - `prazos`: a cada hora, minuto 30;
  - `cotacoes`: diário às 14:00.
  - Todos com `max_instances=1, coalesce=True`, no fuso de `settings.timezone`.
- `main()` cria tabelas, roda `atualizar_cotacoes` e `coletar` uma vez ao subir e inicia o `BlockingScheduler`. Exceção num job é logada e não derruba o worker.
- `seed_demo.main()` cria dados de demonstração plausíveis para desenvolver o frontend: 6 oportunidades NOVA (1 pessoa física, valores em USD e BRL), 4 processos em etapas diferentes, 3 lembretes (1 hoje), 3 contatos (1 atrasado) e cotação USD/EUR. Ele **não** chama a IA nem fontes externas.

- [ ] **Step 1: Teste que falha:** `test_registra_os_quatro_jobs_com_ids` (agendador falso, que registra as chamadas a `add_job`), `test_falha_no_job_e_logada_e_nao_propaga`.
- [ ] **Step 2: Rode** → FAIL. **Step 3: Implemente.** **Step 4: Rode** `pytest -q` → PASS e `docker compose config --quiet` → sem saída.
- [ ] **Step 5: Verificação manual:** `DATABASE_URL=sqlite:///./demo.db APP_PASSWORD=demo JWT_SECRET=x python -m radar.interfaces.seed_demo && uvicorn radar.interfaces.http.app:criar_app --factory` → `curl /api/health` devolve `{"ok":true}`.
- [ ] **Step 6: Commit** — `git commit -m "Worker, seed de demonstração e compose do Radar"`

---

### Task 16: Base do frontend (casca, login, cliente de API e PWA)

**Files:**
- Delete: `frontend/app/{editais,ideias,acompanhamento}/`, `frontend/app/page.tsx` (recriado), `frontend/components/`, `frontend/lib/`, `frontend/scripts/`
- Create: `frontend/shared/api/cliente.ts`, `shared/api/tipos.ts`, `shared/formato.ts`, `shared/formato.test.ts`, `shared/ui/{Botao,Cartao,Etiqueta,Vazio,Carregando}.tsx`, `shared/pwa/{RegistrarSW,InstalarApp,push}.ts(x)`, `app/(workspace)/layout.tsx`, `app/(workspace)/Navegacao.tsx`, `app/page.tsx`, `app/login/page.tsx`, `vitest.config.ts`
- Modify: `app/layout.tsx`, `app/manifest.ts` (nome "Radar", descrição "Oportunidades remotas, funil e lembretes", atalhos Hoje e Entrada), `app/globals.css` (tokens claro/escuro), `public/sw.js` (SHELL = `/hoje`, `/entrada`, `/funil`, `/rede`, `/ajustes`, `/login`, mantendo o resto da lógica de cache e push), `package.json` (+ `vitest`, script `test`), `.github/workflows/ci.yml` (job frontend roda `npm test`)

**Interfaces:**
- `tipos.ts` espelha exatamente os DTOs das Tasks 13–14 (`Oportunidade`, `OportunidadeDetalhe`, `Processo`, `ProcessoResumo`, `Lembrete`, `Contato`, `Painel`, `Perfil`, `Ajustes`, `Status`, `Etapa` como união de strings literais).
- `cliente.ts`: `api<T>(caminho, opcoes)`, mesmo comportamento do `lib/api.ts` atual (token em `localStorage` com chave `radar_token`; 401 → limpa o token e vai para `/login`), mais funções nomeadas por recurso: `painel.obter()`, `oportunidades.listar()`, `oportunidades.obter(id)`, `oportunidades.interessa(id)`, `oportunidades.descartar(id, motivo?)`, `processos.{listar, obter, criar, editar, mover, anotar, anexar, vincularContato}`, `lembretes.{listar, criar, concluir, remover}`, `contatos.{listar, criar, editar, registrarContato}`, `perfil.{obter, salvar}`, `ajustes.{obter, salvar}`, `status.obter()`, `push.{chavePublica, inscrever, testar}`, `auth.login(senha)`. Componentes só importam essas funções.
- `formato.ts`: `formatarDinheiro(v: {valor: string; moeda: string} | null): string` (`"R$ 120.000,00"`, `"US$ 40.000,00"`, `null` → `"—"`), `formatarAproxBrl(brl: string | null): string` (`"≈ R$ 216 mil"`; < 1000 → valor inteiro), `formatarPrazo(iso: string | null, agora: Date): string` (`"hoje 18:00"`, `"amanhã"`, `"em 5 dias"`, `"12/nov"`, `"vencido"`), `ETAPAS: {id: Etapa; rotulo: string}[]` na ordem do Global Constraints, com rótulos `Analisando`, `Proposta enviada`, `Negociação`, `Fechado`, `Perdido`.
- Navegação: no desktop (≥ 1024 px), menu lateral com **Hoje · Entrada · Funil · Rede** e Ajustes no rodapé; abaixo disso, barra inferior com os mesmos quatro itens e Ajustes no topo. Entrada mostra a contagem de novas.

- [ ] **Step 1: Escreva os testes Vitest que falham** em `shared/formato.test.ts`, cobrindo os exemplos acima e `formatarPrazo` com `agora` fixo, inclusive um prazo em UTC que cai "hoje" no horário de Brasília.
- [ ] **Step 2: Rode** — `cd frontend && npm install && npm test` → FAIL.
- [ ] **Step 3: Implemente** formato, cliente, casca e login.
- [ ] **Step 4: Rode** `npm test` → PASS, `npx tsc --noEmit` → sem erros, `npm run build` → sucesso.
- [ ] **Step 5: Commit** — `git commit -m "Frontend: casca do Radar, login, cliente de API e PWA"`

---

### Task 17: Tela Hoje

**Files:** Create `frontend/features/hoje/{PainelDoDia,ListaParaFazer,ResumoFunil,MelhoresNovas}.tsx`, `app/(workspace)/hoje/page.tsx`

**Interfaces:** Consome `painel.obter()`. Estrutura do esboço B:
- cabeçalho com a data por extenso ("Quinta, 23 de outubro");
- **Para fazer**: cada item com o rótulo de quando (`formatarPrazo`) em destaque se for hoje ou atrasado. Lembrete tem botão "Concluir" (`lembretes.concluir`); contato tem "Falei hoje" (`contatos.registrarContato`); prazo leva ao processo;
- **Funil**: 4 contadores (Analisando, Proposta, Negociação, Fechado) e "Em aberto: ≈ R$ …", mais "(+N sem conversão)" quando `sem_conversao > 0`;
- **Melhores novas**: nota, título, organização, prazo e etiqueta "Pessoa física" quando for o caso; o clique leva a `/entrada/{id}`.
- Estados vazios com texto curto: "Nada para hoje." e "Nenhuma oportunidade nova."

- [ ] **Step 1:** Implemente.
- [ ] **Step 2: Verificação:** `npx tsc --noEmit` e `npm run build` passam; com o backend em seed demo, abra `/hoje` em 1440 px e em 390 px e confira as três seções, as duas ações e a navegação (skill `run` ou Chrome).
- [ ] **Step 3: Commit** — `git commit -m "Frontend: tela Hoje"`

---

### Task 18: Entrada e detalhe da oportunidade

**Files:** Create `frontend/features/entrada/{ListaEntrada,CartaoOportunidade,DetalheOportunidade,DialogoDescarte}.tsx`, `app/(workspace)/entrada/page.tsx`, `app/(workspace)/entrada/[id]/page.tsx`

**Interfaces:**
- Lista de `oportunidades.listar()`. Cada cartão mostra nota (verde ≥ 80, neutra abaixo), título, organização · país, prazo, valor original + aproximado em reais, resumo (3 linhas), etiqueta **"Pessoa física"** e os botões **Interessa** e **Descartar**.
- **Interessa** remove o cartão e mostra um aviso com o link "Ver no funil" (`/funil?processo={id}`).
- **Descartar** abre um diálogo com um campo opcional "Por quê? (ajuda a melhorar as próximas notas)"; enviar sem texto também vale.
- O detalhe mostra o resumo, o motivo da nota, o trecho que comprova o trabalho remoto (`trecho_modalidade`), o texto completo recolhível, o link "Abrir chamada original" e as mesmas ações.
- Se `status.obter().ia_configurada === false`, a Entrada mostra "A IA não está configurada, então nenhuma oportunidade pode ser avaliada. Veja Ajustes." no lugar da lista.

- [ ] **Step 1:** Implemente.
- [ ] **Step 2: Verificação:** `tsc` e `build` passam; com o seed, triar um item de cada jeito em desktop e celular e confirmar que ele some, que o processo aparece em `/api/processos` e que o descarte com motivo aparece no banco.
- [ ] **Step 3: Commit** — `git commit -m "Frontend: Entrada e detalhe da oportunidade"`

---

### Task 19: Funil

**Files:** Create `frontend/features/funil/{QuadroFunil,ColunaEtapa,CartaoProcesso,DetalheProcesso,FormProcesso,SecaoNotas,SecaoArquivos,SecaoLembretes,SecaoContatos}.tsx`, `app/(workspace)/funil/page.tsx`

**Interfaces:**
- Quadro com 5 colunas (`ETAPAS`); cada coluna mostra a contagem. No desktop há arrastar e soltar entre colunas (HTML5 drag events, sem biblioteca) e, nos dois tamanhos, um seletor "Mover para…" no detalhe, porque no celular é a única forma.
- `?processo={id}` abre o detalhe: painel lateral de 360 px no desktop e tela cheia com "Voltar" no celular. O detalhe tem campos editáveis (título, organização, valor + moeda, prazo, link), histórico de etapas, notas (adicionar), arquivos (enviar e baixar; erro 413 mostra "Arquivo maior que 20 MB"), lembretes do processo (criar com data e hora, concluir, remover) e contatos vinculados (vincular a partir da lista da Rede).
- Botão **"Novo processo"** abre um formulário com título obrigatório, organização, valor/moeda e prazo, para indicações que chegam por fora do app.

- [ ] **Step 1:** Implemente.
- [ ] **Step 2: Verificação:** `tsc` e `build` passam; com o seed: criar um processo manual, movê-lo por arraste (desktop) e pelo seletor (390 px), anotar, anexar um PDF e baixá-lo, criar um lembrete para hoje e vê-lo em `/hoje`.
- [ ] **Step 3: Commit** — `git commit -m "Frontend: Funil com detalhe do processo"`

---

### Task 20: Rede

**Files:** Create `frontend/features/rede/{ListaContatos,FormContato}.tsx`, `app/(workspace)/rede/page.tsx`

**Interfaces:** `contatos.listar()`, já com os atrasados primeiro. Cada linha mostra nome, organização, "último contato há N dias" ou "nunca", a frequência ("a cada 30 dias") e a etiqueta "Atrasado". Ações: "Falei hoje", editar, ver os processos vinculados (links para `/funil?processo=`). O formulário tem nome (obrigatório), organização, como se conheceram e frequência em dias (opcional; vazio = sem lembrete).

- [ ] **Step 1:** Implemente.
- [ ] **Step 2: Verificação:** `tsc` e `build` passam; com o seed, o contato atrasado aparece primeiro, e "Falei hoje" tira a etiqueta e o remove de `/hoje`.
- [ ] **Step 3: Commit** — `git commit -m "Frontend: Rede de contatos"`

---

### Task 21: Ajustes, README e CI final

**Files:** Create `frontend/features/ajustes/{FormPerfil,FormAjustes,StatusFontes,AtivarNotificacoes}.tsx`, `app/(workspace)/ajustes/page.tsx`; Modify `README.md`, `.github/workflows/ci.yml`

**Interfaces:**
- **Perfil**: área de texto ("Descreva suas especialidades, áreas de interesse e o tipo de projeto que você quer") e faixa de valor mínima/máxima em reais.
- **Ajustes**: limiar do alerta imediato (0–100), horário do resumo diário e dias de aviso de prazo (lista separada por vírgula).
- **Notificações**: ativar push neste aparelho e enviar um teste.
- **Fontes**: para cada fonte, última execução, quantas recebidas/novas e o erro em vermelho, quando houver. No topo, aviso se `ia_configurada` ou `push_configurado` for falso, com o que configurar no `.env`.
- README reescrito para o Radar: o que é, arquitetura em camadas (diagrama ASCII curto), como rodar (Docker e sem Docker, com `seed_demo`), instalação no Android e variáveis do `.env`. Mantenha as seções de HTTPS/Caddy, que continuam válidas.
- CI: jobs backend (`compileall -q radar tests` + `pytest -q`), frontend (`npm test`, `tsc`, `build`) e docker (`compose config`). Sem o job `capturas`.

- [ ] **Step 1:** Implemente.
- [ ] **Step 2: Verificação:** `cd backend && pytest -q` → PASS; `cd frontend && npm test && npx tsc --noEmit && npm run build` → sucesso; `docker compose config --quiet` → sem saída. Com o seed, salvar perfil e ajustes, recarregar e ver os valores mantidos; o limiar 150 mostra o erro da API.
- [ ] **Step 3: Commit** — `git commit -m "Frontend: Ajustes; README e CI do Radar"`
