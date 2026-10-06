"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    try {
      const { token } = await api<{ token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ senha }) });
      setToken(token);
      router.replace("/");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível entrar.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <img src="/icons/icon-192.png" alt="" width={56} height={56} className="mb-6 rounded-2xl" />
        <h1 className="text-[28px] font-bold leading-tight tracking-tight">Licita TI</h1>
        <p className="suave mb-8 mt-2 text-[15px] leading-relaxed">
          Editais de desenvolvimento web e consultoria de TI, prazos e ideias num só lugar.
        </p>
        <form onSubmit={entrar} className="space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium">Senha de acesso</span>
            <input
              type="password"
              className="campo"
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoFocus
            />
          </label>
          {erro && <p className="rounded-lg bg-vermelho-suave px-3 py-2 text-sm text-vermelho-texto">{erro}</p>}
          <button className="botao w-full" disabled={!senha || carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
}
