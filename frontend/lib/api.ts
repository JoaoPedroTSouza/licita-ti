const CHAVE_TOKEN = "licita_token";

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

export async function api<T = unknown>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const headers = new Headers(opcoes.headers);
  if (opcoes.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resp = await fetch(`/api${caminho}`, { ...opcoes, headers });

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
      msg = typeof j.detail === "string" ? j.detail : msg;
    } catch {}
    throw new ErroApi(resp.status, msg);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}
