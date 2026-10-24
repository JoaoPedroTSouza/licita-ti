# Radar de Contratos: design

Data: 2026-10-23
Status: aprovado pelo dono em 2026-10-23

Reconstrução do app do repositório `licita-ti`. O app atual monitora licitações públicas
do PNCP. O dono não gostou da experiência ("não é intuitivo, não me atende") e não quer
mais licitações. A única coisa que ele quer manter do app atual é o fato de ser um **PWA**.

## 1. Intenção e o porquê

O dono é um consultor independente de desenvolvimento de software e está abrindo um CNPJ.
Até hoje todos os contratos chegaram por indicação. O último foi o backend de um CRM, de
R$ 120 mil, indicado pelo Ministério da Saúde/OPAS. Agora ele quer **buscar contratos
ativamente** para fechar mais negócios e ter mais receita.

O app é o **workspace pessoal** dele para três coisas: **buscar** oportunidades,
**receber lembretes** e **controlar os processos**, desde a primeira leitura até o contrato
fechado.

"Coisas menores", nas palavras dele, quer dizer **menos burocracia**, não contratos de
valor baixo. Projetos de dezenas a centenas de milhares de reais são exatamente o alvo.

## 2. Objetivos

1. Trazer automaticamente, todos os dias, chamadas de consultoria e desenvolvimento de
   software publicadas por **organismos internacionais**, no Brasil (OPAS, PNUD, UNESCO,
   UNOPS e outros, geralmente ligados a projetos de cooperação com ministérios) e no
   exterior. **Em ambos os casos, somente trabalho 100% remoto** (regra rígida, seção 6.2).
2. Mostrar cada oportunidade já resumida por IA, com uma **nota de encaixe (0–100)**
   calculada a partir do perfil que o dono escreve.
3. Permitir **triar em segundos** (interessa / descarta) e acompanhar cada processo por um
   **funil** até fechado ou perdido.
4. Manter uma pequena **rede de contatos** com lembretes de follow-up, porque indicação foi
   o único canal que funcionou até hoje.
5. Avisar no celular (push) o que importa, sem virar ruído.
6. Código limpo e **arquitetura limpa**. O dono pediu isso explicitamente.

## 3. Fora do escopo (não-objetivos)

- **Licitações públicas** (PNCP, portais estaduais e municipais, pregão). Toda a coleta do
  PNCP sai do app.
- **Sinais de empresas privadas** (empresas que receberam fomento da Finep/FAPs, startups
  que captaram investimento, vagas de backend abertas há muito tempo). Isso fica para uma
  **fase 2**. A arquitetura de fontes (seção 7.2) precisa permitir adicionar essas fontes
  depois, sem mexer no núcleo.
- **Quadro de "Ideias"** do app atual: sai.
- **Multiusuário ou equipe**: é um app de uma pessoa só.
- **Escrever propostas com IA**: não foi pedido.
- **Oportunidades em idiomas diferentes de português e inglês.**

## 4. Anti-objetivos (fracasso mesmo funcionando)

- Um app que **parece o atual**: telas cheias de números, filtros técnicos e jargão de
  edital. O dono precisa abrir e entender na hora o que fazer hoje.
- Uma **entrada lotada de lixo**: chamadas presenciais, de outra área, em espanhol ou
  francês, ou já vencidas. Na dúvida, é melhor mostrar menos e com qualidade.
- **Notificações demais.** Se o celular apitar o dia inteiro, ele desliga as notificações e
  o app morre.
- **Fontes acopladas ao núcleo.** Se um site muda de layout e isso quebra o resto do app ou
  exige mexer no domínio, a arquitetura falhou.

## 5. Restrições

- **PWA instalável no Android**, com push. Isso exige HTTPS, que a infraestrutura atual com
  Caddy já resolve.
- Funciona bem no **celular e no desktop**.
- **Interface em português.** O conteúdo das oportunidades pode estar em português ou
  inglês. O resumo da IA é sempre em português.
- **Um usuário**, com login por senha, como hoje.
- **Fontes sem API oficial.** O UNGM (portal de compras da ONU) não tem API nem RSS
  oficiais, mas a busca pública de avisos (`https://www.ungm.org/Public/Notice`) é aberta.
  Qualquer fonte pode mudar de formato sem aviso, então cada uma precisa falhar de forma
  isolada e visível (seção 7.4).
- Custo de IA baixo: usar um modelo pequeno e barato para classificar e resumir.

## 6. O que o dono decidiu

### 6.1 Telas e uso diário

O dono escolheu a opção **"Painel do dia"** entre os dois esboços mostrados. O app abre num
resumo do que fazer hoje, e não na caixa de entrada. A navegação tem quatro áreas:
**Hoje · Entrada · Funil · Rede**, além de Ajustes/Perfil. No desktop elas ficam num menu
lateral; no celular, numa barra inferior.

**Hoje (tela inicial)**
- *Para fazer*: lembretes vencendo hoje ou atrasados, prazos de chamadas que estão no funil
  e contatos da rede com follow-up atrasado.
- *Funil*: contagem por etapa e o valor total em aberto.
- *Melhores novas*: as oportunidades não triadas com maior nota de encaixe.

**Entrada**
- Todas as oportunidades novas, cada uma com: título, organização, origem (Brasil ou
  internacional remota), prazo, valor quando informado, resumo da IA e nota de encaixe.
- Ações: **Interessa**, que cria um processo no funil na etapa "analisando", e **Descarta**,
  com motivo opcional. Os motivos de descarte servem para melhorar a nota no futuro.
- Chamadas que não sejam 100% remotas **não aparecem**, nem no Brasil nem no exterior
  (critério na seção 6.2). Chamadas em idioma diferente de português ou inglês **não
  aparecem**.
- Chamadas para **consultor individual (pessoa física)** aparecem normalmente, com uma
  **etiqueta "Pessoa física"** bem visível no cartão e no detalhe.

**Funil**
- Etapas fixas: **analisando → proposta enviada → negociação → fechado → perdido**.
- Cada processo tem: notas, arquivos (termo de referência, proposta), lembretes, histórico
  de mudanças de etapa e vínculo opcional com contatos da rede.
- É possível **criar um processo à mão**, sem oportunidade de origem, para indicações que
  chegam por fora (como foi o caso do CRM).

**Rede**
- Contatos com nome, organização, como se conheceram, data do último contato e
  **frequência desejada de contato**. Quando a frequência passa do prazo, o contato aparece
  em "Para fazer".
- Um contato pode estar ligado a vários processos.

**Notificações (push)**
- Um **resumo diário pela manhã** (ex.: "3 oportunidades novas, 2 tarefas para hoje").
- **Alerta imediato** apenas para oportunidades com nota muito alta.
- **Aviso antes do prazo** de chamadas que estão no funil.

**Perfil**
- Texto livre com especialidades, áreas de interesse (ex.: saúde pública) e faixa de valor
  desejada. A IA usa esse texto para calcular a nota de encaixe.

Os esboços de referência estão em
`C:\Users\jpsou\AppData\Local\Temp\claude\d--Muddok-licita-ti\88f93013-beba-4c47-a471-c8383a04a958\scratchpad\workspace-layout.html`
(opção B). Eles servem para a estrutura, não para o visual final.

### 6.2 Tipos de oportunidade

- Os dois perfis de cliente valem: **organismos internacionais/cooperação técnica**
  (fase 1) e **empresas privadas** (fase 2).
- **Somente 100% remotas, no Brasil e no exterior.** A regra é **rígida**: qualquer
  presença física exigida ou prevista desqualifica a chamada. Isso inclui "home-based com
  possível viagem de abertura", "uma missão presencial", "reuniões presenciais
  eventuais", exigência de residência ou de estar numa cidade específica, e formato
  híbrido. Na dúvida (texto ambíguo ou sem informação sobre o local de trabalho), a
  chamada é **descartada**.
- **Pessoa física ou empresa:** as duas aparecem. Chamadas para consultor individual
  levam a etiqueta "Pessoa física".
- **Idiomas: português e inglês.**

### 6.3 Como é feito

- O dono deixou a escolha de tecnologia comigo, com uma exigência: **clean code e
  arquitetura limpa**.
- **Manter**: PWA.

## 7. Decisões técnicas (minhas, não do dono)

### 7.1 Stack

Mantenho a base que já existe e funciona no repositório, mas **reescrevo o código do zero**:
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Postgres, APScheduler num processo worker
  separado, pywebpush (VAPID) e SDK da Anthropic.
- Frontend: Next.js (App Router) + React + TypeScript + Tailwind, como PWA com service
  worker e Web Push.
- Infraestrutura: Docker Compose (db, api, worker, web, caddy) e o fluxo de HTTPS do README
  atual.
- O código antigo de editais, PNCP, ideias e painel é **removido**. O banco começa vazio,
  sem migração de dados antigos.

### 7.2 Arquitetura do backend (camadas)

Dependências apontam só para dentro: `interfaces → application → domain`, e
`infrastructure` implementa as portas definidas em `application`/`domain`.

- **domain**: entidades e regras puras, sem FastAPI, SQLAlchemy ou HTTP.
  `Oportunidade`, `Processo` (com `Etapa` e histórico), `Lembrete`, `Contato`, `Perfil`,
  `Classificacao` (nota, resumo, remoto?, idioma, motivo). Regras como "que transições de
  etapa são válidas" e "quando um contato está atrasado" moram aqui.
- **application**: casos de uso, como `ColetarOportunidades`, `TriarOportunidade`,
  `MoverProcesso`, `CriarProcessoManual`, `MontarPainelDoDia`, `EnviarResumoDiario`,
  `VerificarPrazos`, `RegistrarContato`, além das **portas**: `FonteDeOportunidades`,
  `Classificador`, `Notificador`, repositórios e `Relogio`.
- **infrastructure**: adaptadores. Uma implementação de `FonteDeOportunidades` por fonte,
  `ClassificadorClaude`, `NotificadorWebPush`, repositórios SQLAlchemy e armazenamento de
  arquivos em disco/volume.
- **interfaces**: rotas FastAPI (DTOs Pydantic) e o worker agendado. Ambos só chamam casos
  de uso.

### 7.3 Arquitetura do frontend

- Pastas por funcionalidade: `features/hoje`, `features/entrada`, `features/funil`,
  `features/rede`, `features/perfil`, mais `shared/` (UI básica, cliente da API, formatação).
- Componentes de tela não chamam `fetch` diretamente. Passam por um cliente de API tipado.

### 7.4 Fontes (fase 1)

Cada fonte é um adaptador independente que devolve oportunidades num formato comum
(título, organização, país, link, prazo, valor, texto/termo de referência, idioma bruto).
A falha de uma fonte é registrada (última execução, erro, quantidade) e aparece em Ajustes,
sem derrubar as outras.

Fontes iniciais, em ordem de prioridade:
1. **UNGM**: busca pública de avisos. Concentra OPAS, PNUD, UNOPS, UNICEF e outras
   agências. Duas consultas: país Brasil, e global restrita a consultoria/serviços de TI
   (as globais passam depois pelo filtro de remoto).
2. **Página de oportunidades da OPAS no Brasil**: `https://www.paho.org/pt/licitacoes-opas`.
3. **ReliefWeb (API pública)**: consultorias internacionais, muitas marcadas como
   *home-based*.
4. **Banco Mundial**: avisos de aquisição (procurement notices).

Quem construir deve **verificar a viabilidade técnica de cada fonte antes de implementá-la**
(formato, paginação, limites de acesso, termos de uso). Se uma fonte se mostrar inviável,
documente o motivo e passe para a próxima, sem forçar.

ReliefWeb e boa parte do UNGM publicam principalmente consultorias individuais. Como elas
aparecem (com etiqueta), essas fontes valem a pena. Espera-se, porém, que o filtro rígido
de remoto descarte uma parte grande do volume bruto.

Editais de ministérios com UNESCO, publicados nas páginas de cooperação internacional do
gov.br, costumam ser para consultor individual. Ficam como fonte candidata para depois da
fase 1, por serem PDFs soltos e difíceis de coletar.

### 7.5 Classificação por IA

- Para cada oportunidade nova, a IA devolve em JSON: relevância, **nota de encaixe 0–100**
  com base no Perfil, resumo em português (2–3 frases), **modalidade de trabalho**
  (`remoto_total`, `com_presenca` ou `indefinido`) com o trecho do texto que justifica,
  **idioma**, **tipo de contratação** (`empresa` ou `pessoa_fisica`), prazo, valor e moeda
  quando estiverem no texto, e um motivo curto da nota.
- Filtros automáticos antes de entrar na Entrada, implementados como regra do domínio e
  não no prompt: modalidade diferente de `remoto_total` → descartada; idioma diferente de
  pt/en → descartada; prazo vencido → descartada. As descartadas automaticamente ficam
  registradas com o motivo, mas não aparecem.
- Os testes do classificador e da regra devem cobrir explicitamente casos limítrofes, como
  "home-based with one inception mission", "remote, occasional meetings in Brasília" e
  texto sem nenhuma menção ao local de trabalho. Todos esses devem ser descartados.
- Sem chave de API, não há como avaliar a modalidade com segurança. Nesse caso o app
  **não exibe nada** e mostra um aviso em Ajustes de que a IA é necessária. *(decisão
  minha, para respeitar a regra rígida de remoto)*

### 7.6 Valores e moedas *(decisão minha)*

- Valores são guardados com moeda original (BRL, USD, EUR etc.).
- Totais (funil, "valor em aberto") e a comparação com a faixa de valor do Perfil usam
  **conversão para BRL** pela cotação PTAX do Banco Central (API pública de dados abertos),
  atualizada uma vez por dia pelo worker. Se a cotação não estiver disponível, usa-se a
  última conhecida.
- Na tela, mostra-se o valor original e, ao lado, o aproximado em reais.
## 8. O que fica a cargo de quem construir

- Nomes exatos de módulos, tabelas e rotas, e a forma dos DTOs.
- Biblioteca de scraping/HTML e a estratégia de repetição de tentativas.
- Limiar exato da "nota muito alta" para alerta imediato (sugestão: ≥ 85, ajustável em
  Ajustes) e o horário do resumo diário (sugestão: 7h30, horário de Brasília).
- Antecedência do aviso de prazo (sugestão: 3 dias e 1 dia antes).
- Visual final (cores, tipografia), desde que seja limpo, legível e siga a estrutura do
  esboço B. Tema claro e escuro.
- Estratégia de testes, com testes de unidade no domínio e nos casos de uso e testes de
  contrato nos adaptadores de fonte usando respostas gravadas.
- Atualizar o README e o CI para refletir o novo app.
- Nome do produto na interface: sugiro **"Radar"**. O repositório pode continuar se chamando
  `licita-ti`.
