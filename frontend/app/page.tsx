"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import EditalCard from "@/components/EditalCard";
import InstalarApp from "@/components/InstalarApp";
import { api } from "@/lib/api";
import { tempoDesde } from "@/lib/format";
import type { EditalResumo, Pagina, Resumo } from "@/lib/types";

const FILTROS = [
  { id: "relevantes", rotulo: "Relevantes" },
  { id: "todos", rotulo: "Todos" },
  { id: "favoritos", rotulo: "Favoritos" },
] as const;

export default function Page() {
  return (
    <Suspense>
      <Inicio />
    </Suspense>
  );
}

function Inicio() {
  const router = useRouter();
  const params = useSearchParams();
  const filtro = params.get("filtro") ?? "relevantes";

  const [resumo, setResumo] = useState<Resumo | null>(null);
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
      const qs = new URLSearchParams({ filtro, pagina: String(pag), por_pagina: "20", abertos: String(abertos) });
      if (buscaAplicada) qs.set("q", buscaAplicada);
      try {
        const r = await api<Pagina>(`/editais?${qs}`);
        setItens((ant) => (pag === 1 ? r.itens : [...ant, ...r.itens]));
        setTotal(r.total);
        setPagina(pag);
      } catch (e) {
        setErro(e instanceof Error ? e.message : "Falha ao carregar");
      } finally {
        setCarregando(false);
      }
    },
    [filtro, buscaAplicada, abertos]
  );

  useEffect(() => {
    carregar(1);
  }, [carregar]);

  useEffect(() => {
    api<Resumo>("/resumo").then(setResumo).catch(() => {});
  }, []);

  return (
    <Shell titulo="Editais">
      <InstalarApp />

      {resumo && (
        <section className="mb-4 grid grid-cols-3 gap-2">
          <Indicador valor={resumo.novos_hoje} rotulo="novos em 24h" />
          <Indicador valor={resumo.relevantes_abertos} rotulo="abertos relevantes" />
          <Indicador valor={resumo.encerrando_em_48h} rotulo="prazos em 48h" alerta={resumo.encerrando_em_48h > 0} />
        </section>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setBuscaAplicada(busca.trim());
        }}
        className="mb-3"
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

      <div className="mb-4 flex items-center gap-2 overflow-x-auto">
        {FILTROS.map((f) => (
          <button
            key={f.id}
            onClick={() => router.replace(f.id === "relevantes" ? "/" : `/?filtro=${f.id}`)}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium ${
              filtro === f.id ? "bg-marca text-white" : "cartao"
            }`}
          >
            {f.rotulo}
          </button>
        ))}
        <span className="flex-1" />
        <label className="suave flex shrink-0 items-center gap-1.5 text-xs">
          <input type="checkbox" checked={abertos} onChange={(e) => setAbertos(e.target.checked)} className="accent-teal-700" />
          só abertos
        </label>
      </div>

      {erro && <p className="cartao mb-3 p-3 text-sm text-red-600">{erro}</p>}

      <div className="space-y-3">
        {itens.map((e) => (
          <EditalCard key={e.id} e={e} />
        ))}
      </div>

      {!carregando && itens.length === 0 && !erro && (
        <div className="suave py-16 text-center text-sm">
          <p className="mb-1 text-base font-semibold" style={{ color: "var(--texto)" }}>
            Nada por aqui ainda
          </p>
          <p>A coleta roda 3 vezes ao dia. Você também pode disparar uma em Ajustes.</p>
        </div>
      )}

      {itens.length < total && (
        <button className="botao botao-sec mt-4 w-full" disabled={carregando} onClick={() => carregar(pagina + 1)}>
          {carregando ? "Carregando…" : `Carregar mais (${total - itens.length})`}
        </button>
      )}
      {carregando && itens.length === 0 && <p className="suave py-10 text-center text-sm">Carregando…</p>}

      {resumo && <p className="suave mt-6 text-center text-xs">Última coleta {tempoDesde(resumo.ultima_coleta)}</p>}
    </Shell>
  );
}

function Indicador({ valor, rotulo, alerta }: { valor: number; rotulo: string; alerta?: boolean }) {
  return (
    <div className="cartao px-3 py-2.5">
      <p className={`text-2xl font-bold tabular-nums ${alerta ? "text-red-600 dark:text-red-400" : ""}`}>{valor}</p>
      <p className="suave text-[11px] leading-tight">{rotulo}</p>
    </div>
  );
}
