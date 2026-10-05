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
      setErro(err instanceof Error ? err.message : "Não foi possível entrar");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6">
      <img src="/icons/icon-192.png" alt="" width={64} height={64} className="mb-6 rounded-2xl" />
      <h1 className="text-2xl font-bold tracking-tight">Licita TI</h1>
      <p className="suave mb-8 mt-1 text-sm">Editais de desenvolvimento web e consultoria de TI, direto no seu celular.</p>
      <form onSubmit={entrar} className="space-y-3">
        <input
          type="password"
          className="campo"
          placeholder="Senha de acesso"
          autoComplete="current-password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoFocus
        />
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <button className="botao w-full" disabled={!senha || carregando}>
          {carregando ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}
