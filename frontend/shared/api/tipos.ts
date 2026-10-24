/** Espelho dos DTOs da API (backend/radar/interfaces/http/dtos.py). Decimais chegam como texto;
 *  datas chegam em ISO 8601 com fuso. */

export type Etapa = "analisando" | "proposta_enviada" | "negociacao" | "fechado" | "perdido";

export interface Valor {
  valor: string;
  moeda: string;
}

export interface Oportunidade {
  id: number;
  titulo: string;
  organizacao: string;
  pais: string | null;
  link: string;
  prazo: string | null;
  valor: Valor | null;
  valor_brl: string | null;
  nota: number | null;
  resumo: string | null;
  motivo: string | null;
  pessoa_fisica: boolean;
  fonte: string;
  status: string;
  processo_id: number | null;
}

export interface OportunidadeDetalhe extends Oportunidade {
  texto: string;
  trecho_modalidade: string | null;
}

export interface Nota {
  texto: string;
  criada_em: string;
}

export interface Arquivo {
  id: number;
  nome: string;
  tamanho: number;
  enviado_em: string;
}

export interface MudancaEtapa {
  de: Etapa | null;
  para: Etapa;
  em: string;
}

export interface Lembrete {
  id: number;
  texto: string;
  vence_em: string;
  processo_id: number | null;
  concluido: boolean;
}

export interface ProcessoResumo {
  id: number;
  titulo: string;
  organizacao: string | null;
  etapa: Etapa;
  valor: Valor | null;
  valor_brl: string | null;
  prazo: string | null;
}

export interface Processo extends ProcessoResumo {
  link: string | null;
  oportunidade_id: number | null;
  criado_em: string;
  notas: Nota[];
  arquivos: Arquivo[];
  historico: MudancaEtapa[];
  contato_ids: number[];
  lembretes: Lembrete[];
}

export interface Contato {
  id: number;
  nome: string;
  organizacao: string | null;
  como_conheceu: string | null;
  ultimo_contato: string | null;
  frequencia_dias: number | null;
  atrasado: boolean;
  processo_ids: number[];
}

export interface ItemParaFazer {
  tipo: string;
  titulo: string;
  /** Data (AAAA-MM-DD) ou instante ISO com fuso. */
  quando: string | null;
  ref_id: number;
  processo_id: number | null;
}

export interface ResumoFunil {
  contagem: Partial<Record<Etapa, number>>;
  valor_aberto_brl: string;
  sem_conversao: number;
}

export interface Painel {
  dia: string;
  para_fazer: ItemParaFazer[];
  funil: ResumoFunil;
  melhores_novas: Oportunidade[];
}

export interface Perfil {
  texto: string;
  faixa_min_brl: string | null;
  faixa_max_brl: string | null;
}

export interface Ajustes {
  limiar_alerta: number;
  horario_resumo: string;
  avisos_prazo_dias: number[];
}

export interface ExecucaoFonte {
  fonte: string;
  finalizada_em: string;
  recebidas: number;
  novas: number;
  erro: string | null;
}

export interface Status {
  ia_configurada: boolean;
  push_configurado: boolean;
  fontes: ExecucaoFonte[];
}

export interface NovoProcesso {
  titulo: string;
  organizacao?: string | null;
  valor?: Valor | null;
  /** ISO 8601 com fuso: use `new Date(...).toISOString()`. */
  prazo?: string | null;
}

export type EdicaoProcesso = Partial<NovoProcesso> & { link?: string | null };

export interface NovoLembrete {
  texto: string;
  /** ISO 8601 com fuso: use `new Date(...).toISOString()`. */
  vence_em: string;
  processo_id?: number | null;
}

export interface NovoContato {
  nome: string;
  organizacao?: string | null;
  como_conheceu?: string | null;
  frequencia_dias?: number | null;
}

export type EdicaoContato = Partial<NovoContato>;

export interface InscricaoPush {
  endpoint: string;
  keys: { p256dh: string; auth: string };
}
