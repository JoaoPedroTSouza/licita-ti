export type Status = "novo" | "analisando" | "participando" | "descartado";

export const STATUS_INFO: Record<Status, { rotulo: string; cor: string }> = {
  novo: { rotulo: "Novo", cor: "bg-azul-suave text-azul-texto" },
  analisando: { rotulo: "Analisando", cor: "bg-ambar-suave text-ambar-texto" },
  participando: { rotulo: "Participando", cor: "bg-ok-suave text-ok-texto" },
  descartado: { rotulo: "Descartado", cor: "bg-superficie-2 text-texto-suave" },
};

export interface EditalResumo {
  id: number;
  numero_controle_pncp: string;
  objeto: string;
  orgao: string | null;
  uf: string | null;
  municipio: string | null;
  modalidade_nome: string | null;
  valor_estimado: number | null;
  data_publicacao: string | null;
  data_encerramento: string | null;
  ia_relevante: boolean | null;
  ia_score: number | null;
  ia_categoria: string | null;
  keyword_score: number;
  status: Status;
  favorito: boolean;
}

export interface EditalDetalhe extends EditalResumo {
  cnpj: string;
  ano: number;
  sequencial: number;
  numero_compra: string | null;
  processo: string | null;
  informacao_complementar: string | null;
  unidade: string | null;
  modo_disputa: string | null;
  situacao: string | null;
  srp: boolean | null;
  data_abertura: string | null;
  link_origem: string | null;
  link_pncp: string | null;
  keywords_encontradas: string[];
  ia_resumo: string | null;
  ia_motivo: string | null;
  ia_exigencias: string[];
  notas: string | null;
}

export interface Pagina {
  itens: EditalResumo[];
  total: number;
  pagina: number;
  por_pagina: number;
}

export interface Resumo {
  novos_hoje: number;
  relevantes_abertos: number;
  por_status: Record<Status, number>;
  encerrando_em_48h: number;
  ultima_coleta: string | null;
}

export interface Preferencias {
  palavras_chave: string[];
  palavras_reforco: string[];
  palavras_exclusao: string[];
  ufs: string[];
  modalidades: number[];
  valor_minimo: number;
  valor_maximo: number;
  score_minimo_keywords: number;
  score_minimo_ia_push: number;
  perfil: string;
}

/* ---------- Ideias ---------- */
export type StatusIdeia = "nova" | "validando" | "executando" | "concluida" | "descartada";
export type TipoIdeia = "produto" | "servico" | "conteudo" | "melhoria" | "proposta";
export type Prioridade = "baixa" | "media" | "alta";

export const STATUS_IDEIA: Record<StatusIdeia, { rotulo: string; singular: string; dica: string }> = {
  nova: { rotulo: "Novas", singular: "Nova", dica: "Anote sem filtrar" },
  validando: { rotulo: "Validando", singular: "Validando", dica: "Conversando com clientes, testando demanda" },
  executando: { rotulo: "Em execução", singular: "Em execução", dica: "Construindo ou vendendo" },
  concluida: { rotulo: "Concluídas", singular: "Concluída", dica: "Lançadas ou entregues" },
  descartada: { rotulo: "Descartadas", singular: "Descartada", dica: "Não seguiram adiante" },
};

export const TIPOS_IDEIA: Record<TipoIdeia, string> = {
  produto: "Produto / SaaS",
  servico: "Serviço",
  conteudo: "Conteúdo / redes",
  melhoria: "Melhoria no Licita TI",
  proposta: "Proposta para edital",
};

export const PRIORIDADES: Record<Prioridade, { rotulo: string; cor: string }> = {
  alta: { rotulo: "Alta", cor: "bg-vermelho-suave text-vermelho-texto" },
  media: { rotulo: "Média", cor: "bg-roxo-suave text-roxo-texto" },
  baixa: { rotulo: "Baixa", cor: "bg-superficie-2 text-texto-suave" },
};

export interface Ideia {
  id: number;
  titulo: string;
  descricao: string | null;
  tipo: TipoIdeia;
  status: StatusIdeia;
  prioridade: Prioridade;
  tags: string[];
  potencial_mensal: number | null;
  edital_id: number | null;
  edital: { id: number; objeto: string; orgao: string | null; uf: string | null; data_encerramento: string | null } | null;
  criado_em: string;
  atualizado_em: string;
}

/* ---------- Painel ---------- */
export interface Painel {
  gerado_em: string;
  kpis: {
    relevantes_abertos: number;
    novos_7d: number;
    analisando: number;
    participando: number;
    encerrando_48h: number;
    valor_em_aberto: number;
    ideias_ativas: number;
  };
  serie: { data: string; candidatos: number; relevantes: number }[];
  prazos: {
    id: number;
    objeto: string;
    orgao: string | null;
    uf: string | null;
    status: Status;
    ia_score: number | null;
    valor_estimado: number | null;
    data_encerramento: string;
  }[];
  por_uf: { uf: string; total: number }[];
  por_categoria: { categoria: string; total: number }[];
  funil: Record<Status, number>;
  ideias: Record<StatusIdeia, number>;
  coletas: {
    id: number;
    finalizado_em: string | null;
    recebidos: number;
    novos: number;
    relevantes: number;
    notificados: number;
    erro: string | null;
  }[];
}
