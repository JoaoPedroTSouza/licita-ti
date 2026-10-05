export type Status = "novo" | "analisando" | "participando" | "descartado";

export const STATUS_INFO: Record<Status, { rotulo: string; cor: string }> = {
  novo: { rotulo: "Novo", cor: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200" },
  analisando: { rotulo: "Analisando", cor: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200" },
  participando: { rotulo: "Participando", cor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200" },
  descartado: { rotulo: "Descartado", cor: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300" },
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
