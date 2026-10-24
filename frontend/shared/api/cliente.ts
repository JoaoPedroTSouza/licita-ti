/** Cliente HTTP da API do Radar. Componentes importam só as funções nomeadas por recurso. */
import type {
  Ajustes, Arquivo, Contato, EdicaoContato, EdicaoProcesso, Etapa, InscricaoPush, Lembrete,
  NovoContato, NovoLembrete, NovoProcesso, Oportunidade, OportunidadeDetalhe, Painel,
  Perfil, Processo, ProcessoResumo, Status,
} from "./tipos";

const CHAVE_TOKEN = "radar_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CHAVE_TOKEN);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(CHAVE_TOKEN, token);
  else localStorage.removeItem(CHAVE_TOKEN);
}

export class ErroApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

function cabecalhos(opcoes: RequestInit): Headers {
  const headers = new Headers(opcoes.headers);
  if (typeof opcoes.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return headers;
}

async function requisitar(caminho: string, opcoes: RequestInit): Promise<Response> {
  const resp = await fetch(`/api${caminho}`, { ...opcoes, headers: cabecalhos(opcoes) });
  if (resp.status === 401 && !caminho.startsWith("/auth/")) {
    setToken(null);
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new ErroApi(401, "Sessão expirada");
  }
  if (!resp.ok) {
    let msg = `Erro ${resp.status}`;
    try {
      const j = await resp.json();
      if (typeof j.detail === "string") msg = j.detail;
    } catch {}
    throw new ErroApi(resp.status, msg);
  }
  return resp;
}

export async function api<T = unknown>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const resp = await requisitar(caminho, opcoes);
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

const enviar = <T>(metodo: string, caminho: string, corpo?: unknown) =>
  api<T>(caminho, { method: metodo, body: corpo === undefined ? undefined : JSON.stringify(corpo) });

export const auth = {
  login: (senha: string) => enviar<{ token: string }>("POST", "/auth/login", { senha }),
};

export const painel = {
  obter: () => api<Painel>("/painel"),
};

export const oportunidades = {
  /** Novas, as que aparecem na Entrada. */
  listar: () => api<Oportunidade[]>("/oportunidades"),
  obter: (id: number) => api<OportunidadeDetalhe>(`/oportunidades/${id}`),
  interessa: (id: number) => enviar<Processo>("POST", `/oportunidades/${id}/interessa`),
  descartar: (id: number, motivo?: string) =>
    enviar<void>("POST", `/oportunidades/${id}/descartar`, { motivo: motivo ?? null }),
};

export const processos = {
  listar: () => api<ProcessoResumo[]>("/processos"),
  obter: (id: number) => api<Processo>(`/processos/${id}`),
  criar: (dados: NovoProcesso) => enviar<Processo>("POST", "/processos", dados),
  editar: (id: number, dados: EdicaoProcesso) => enviar<Processo>("PATCH", `/processos/${id}`, dados),
  mover: (id: number, etapa: Etapa) => enviar<Processo>("POST", `/processos/${id}/etapa`, { etapa }),
  anotar: (id: number, texto: string) => enviar<Processo>("POST", `/processos/${id}/notas`, { texto }),
  anexar: (id: number, arquivo: File) => {
    const corpo = new FormData();
    corpo.append("arquivo", arquivo);
    return api<Arquivo>(`/processos/${id}/arquivos`, { method: "POST", body: corpo });
  },
  /** Baixa o arquivo (a rota exige o token, então não vale um link direto). */
  baixarArquivo: async (id: number, arquivoId: number): Promise<Blob> => {
    const resp = await requisitar(`/processos/${id}/arquivos/${arquivoId}`, {});
    return resp.blob();
  },
  vincularContato: (id: number, contatoId: number) =>
    enviar<Processo>("POST", `/processos/${id}/contatos/${contatoId}`),
};

export const lembretes = {
  listar: () => api<Lembrete[]>("/lembretes"),
  criar: (dados: NovoLembrete) => enviar<Lembrete>("POST", "/lembretes", dados),
  concluir: (id: number) => enviar<Lembrete>("POST", `/lembretes/${id}/concluir`),
  remover: (id: number) => enviar<void>("DELETE", `/lembretes/${id}`),
};

export const contatos = {
  listar: () => api<Contato[]>("/contatos"),
  criar: (dados: NovoContato) => enviar<Contato>("POST", "/contatos", dados),
  editar: (id: number, dados: EdicaoContato) => enviar<Contato>("PATCH", `/contatos/${id}`, dados),
  registrarContato: (id: number) => enviar<Contato>("POST", `/contatos/${id}/registrar-contato`),
};

export const perfil = {
  obter: () => api<Perfil>("/perfil"),
  salvar: (dados: Perfil) => enviar<Perfil>("PUT", "/perfil", dados),
};

export const ajustes = {
  obter: () => api<Ajustes>("/ajustes"),
  salvar: (dados: Ajustes) => enviar<Ajustes>("PUT", "/ajustes", dados),
};

export const status = {
  obter: () => api<Status>("/status"),
};

export const push = {
  chavePublica: () => api<{ chave: string }>("/push/chave-publica"),
  inscrever: (inscricao: InscricaoPush) => enviar<void>("POST", "/push/inscrever", inscricao),
  testar: () => enviar<{ entregues: number }>("POST", "/push/teste"),
};
