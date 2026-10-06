"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import EditalCard from "@/components/EditalCard";
import InstalarApp from "@/components/InstalarApp";
import { api } from "@/lib/api";
import type { EditalResumo, Pagina } from "@/lib/types";

const FILTROS = [
  { id: "relevantes", rotulo: "Relevantes" },
  { id: "todos", rotulo: "Todos" },
  { id: "favoritos", rotulo: "Favoritos" },
] as const;

export default function Page() {
  return (
    <Suspense>
      <Editais />
    </Suspense>
  );
}

function Editais() {
  const router = useRouter();
  const params = useSearchParams();
  const filtro = params.get("filtro") ?? "relevantes";

  const [itens, setItens] = useState<EditalResumo[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [busca, setBusca] = useState("");
  const [buscaAplicada, setBuscaAplicada] = useState("");
  const [abertos, setAbertos] = useState(true);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  const carregar = useCallback(
    async (pag: number) => {
      setCarregando(true);
      setErro("");
      const qs = new URLSearchParams({ filtro, pagina: String(pag), por_pagina: "24", abertos: String(abertos) });
      if (buscaAplicada) qs.set("q", buscaAplicada);
      try {
        const r = await api<Pagina>(`/editais?${qs}`);
        setItens((ant) => (pag === 1 ? r.itens : [...ant, ...r.itens]));
        setTotal(r.total);
        setPagina(pag);
      } catch (e) {
        setErro(e instanceof Error ? e.message : "Não foi possível carregar os editais.");
      } finally {
        setCarregando(false);
      }
    },
    [filtro, buscaAplicada, abertos]
  );

  useEffect(() => {
    carregar(1);
  }, [carregar]);

  return (
    <Shell titulo="Editais" subtitulo={carregando && itens.length === 0 ? " " : `${total} encontrados`}>
      <InstalarApp />

      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setBuscaAplicada(busca.trim());
          }}
          className="lg:w-[420px]"
        >
          <input
            type="search"
            className="campo"
            placeholder="Buscar por objeto, órgão ou cidade"
            value={busca}
            onChange={(e) => {
              setBusca(e.target.value);
              if (!e.target.value) setBuscaAplicada("");
            }}
          />
        </form>

        <div className="flex items-center gap-2 overflow-x-auto">
          {FILTROS.map((f) => (
            <button
              key={f.id}
              onClick={() => router.replace(f.id === "relevantes" ? "/editais" : `/editais?filtro=${f.id}`)}
              className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium ${
                filtro === f.id ? "bg-azul-suave text-azul-texto" : "suave hover:bg-superficie-2"
              }`}
            >
              {f.rotulo}
            </button>
          ))}
        </div>
        <span className="hidden flex-1 lg:block" />
        <label className="suave flex shrink-0 items-center gap-2 text-sm">
          <input type="checkbox" checked={abertos} onChange={(e) => setAbertos(e.target.checked)} className="h-4 w-4 accent-[var(--azul)]" />
          Só com propostas abertas
        </label>
      </div>

      {erro && <p className="mb-4 rounded-xl bg-vermelho-suave p-3 text-sm text-vermelho-texto">{erro}</p>}

      <div className="grid gap-3 md:grid-cols-2 lg:gap-4 xl:grid-cols-3">
        {itens.map((e) => (
          <EditalCard key={e.id} e={e} />
        ))}
      </div>

      {!carregando && itens.length === 0 && !erro && (
        <div className="cartao mx-auto max-w-md px-6 py-12 text-center">
          <p className="mb-1 font-semibold">Nenhum edital com esses filtros</p>
          <p className="suave text-sm">
            A coleta roda às 7h, 12h e 18h. Para buscar agora, use Ajustes → Coletar últimos 7 dias.
          </p>
        </div>
      )}

      {itens.length < total && (
        <div className="mt-6 flex justify-center">
          <button className="botao botao-sec w-full lg:w-auto" disabled={carregando} onClick={() => carregar(pagina + 1)}>
            {carregando ? "Carregando…" : `Carregar mais ${Math.min(24, total - itens.length)} de ${total - itens.length}`}
          </button>
        </div>
      )}
      {carregando && itens.length === 0 && <p className="suave py-16 text-center text-sm">Carregando editais…</p>}
    </Shell>
  );
}
