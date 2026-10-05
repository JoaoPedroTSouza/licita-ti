"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import EditalCard from "@/components/EditalCard";
import { api } from "@/lib/api";
import { STATUS_INFO, type Pagina, type Resumo, type Status } from "@/lib/types";

const ETAPAS: Status[] = ["analisando", "participando", "descartado"];

export default function AcompanhamentoPage() {
  const [etapa, setEtapa] = useState<Status>("analisando");
  const [dados, setDados] = useState<Pagina | null>(null);
  const [contagem, setContagem] = useState<Resumo["por_status"] | null>(null);

  useEffect(() => {
    api<Resumo>("/resumo").then((r) => setContagem(r.por_status)).catch(() => {});
  }, []);

  useEffect(() => {
    setDados(null);
    api<Pagina>(`/editais?filtro=todos&status=${etapa}&por_pagina=100`).then(setDados).catch(() => {});
  }, [etapa]);

  // Ordena por prazo mais próximo primeiro (o que importa no funil)
  const itens = [...(dados?.itens ?? [])].sort((a, b) => {
    const pa = a.data_encerramento ? new Date(a.data_encerramento).getTime() : Infinity;
    const pb = b.data_encerramento ? new Date(b.data_encerramento).getTime() : Infinity;
    return pa - pb;
  });

  return (
    <Shell titulo="Acompanhamento">
      <div className="cartao mb-4 grid grid-cols-3 gap-1 p-1">
        {ETAPAS.map((s) => (
          <button
            key={s}
            onClick={() => setEtapa(s)}
            className={`rounded-xl py-2 text-sm font-semibold ${etapa === s ? "bg-marca text-white" : "suave"}`}
          >
            {STATUS_INFO[s].rotulo}
            {contagem && <span className="ml-1 opacity-75 tabular-nums">{contagem[s]}</span>}
          </button>
        ))}
      </div>

      {!dados && <p className="suave py-10 text-center text-sm">Carregando…</p>}
      {dados && itens.length === 0 && (
        <p className="suave py-16 text-center text-sm">
          Nenhum edital em “{STATUS_INFO[etapa].rotulo}”.
          <br />
          Abra um edital e mude a situação para ele aparecer aqui.
        </p>
      )}
      <div className="space-y-3">
        {itens.map((e) => (
          <EditalCard key={e.id} e={e} />
        ))}
      </div>
    </Shell>
  );
}
