"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import EditalCard from "@/components/EditalCard";
import { api } from "@/lib/api";
import { STATUS_INFO, type EditalResumo, type Pagina, type Status } from "@/lib/types";

const ETAPAS: Status[] = ["analisando", "participando", "descartado"];
const DICAS: Record<string, string> = {
  analisando: "Lendo o edital e checando documentos",
  participando: "Proposta enviada ou em preparação",
  descartado: "Fora do perfil ou sem condições",
};

function porPrazo(a: EditalResumo, b: EditalResumo) {
  const pa = a.data_encerramento ? new Date(a.data_encerramento).getTime() : Infinity;
  const pb = b.data_encerramento ? new Date(b.data_encerramento).getTime() : Infinity;
  return pa - pb;
}

export default function AcompanhamentoPage() {
  const [aba, setAba] = useState<Status>("analisando");
  const [dados, setDados] = useState<Record<string, EditalResumo[]> | null>(null);

  useEffect(() => {
    Promise.all(
      ETAPAS.map((s) => api<Pagina>(`/editais?filtro=todos&status=${s}&por_pagina=100`).then((r) => [s, r.itens.sort(porPrazo)] as const))
    )
      .then((pares) => setDados(Object.fromEntries(pares)))
      .catch(() => setDados({}));
  }, []);

  return (
    <Shell titulo="Acompanhamento" subtitulo="Editais que você está analisando ou disputando, do prazo mais próximo ao mais distante">
      <div className="cartao mb-4 grid grid-cols-3 gap-1 p-1 lg:hidden">
        {ETAPAS.map((s) => (
          <button
            key={s}
            onClick={() => setAba(s)}
            className={`rounded-lg py-2 text-sm font-semibold ${aba === s ? "bg-azul text-white" : "suave"}`}
          >
            {STATUS_INFO[s].rotulo} <span className="tabular opacity-75">{dados?.[s]?.length ?? ""}</span>
          </button>
        ))}
      </div>

      {!dados && <p className="suave py-16 text-center text-sm">Carregando…</p>}

      {dados && (
        <div className="grid gap-5 lg:grid-cols-3 lg:items-start">
          {ETAPAS.map((s) => {
            const itens = dados[s] ?? [];
            return (
              <section key={s} className={`${aba === s ? "" : "hidden"} lg:block`}>
                <header className="mb-3 hidden lg:block">
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_INFO[s].cor}`}>{STATUS_INFO[s].rotulo}</span>
                    <span className="suave tabular text-sm">{itens.length}</span>
                  </div>
                  <p className="suave mt-1 text-xs">{DICAS[s]}</p>
                </header>
                <div className={`space-y-3 ${s === "descartado" ? "lg:opacity-75" : ""}`}>
                  {itens.map((e) => <EditalCard key={e.id} e={e} />)}
                  {itens.length === 0 && (
                    <p className="suave rounded-xl border border-dashed borda px-4 py-8 text-center text-sm">
                      Nenhum edital aqui. Abra um edital e mude a situação no funil.
                    </p>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </Shell>
  );
}
