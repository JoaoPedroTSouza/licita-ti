"use client";

import { useState } from "react";
import type { Etapa, ProcessoResumo } from "@/shared/api/tipos";
import CartaoProcesso from "./CartaoProcesso";

export default function ColunaEtapa({
  etapa,
  rotulo,
  itens,
  agora,
  desktop,
  aberta,
  selecionado,
  aoSoltar,
}: {
  etapa: Etapa;
  rotulo: string;
  itens: ProcessoResumo[];
  agora: Date;
  desktop: boolean;
  /** Só vale no celular: seção recolhível, aberta por padrão nas etapas em aberto. */
  aberta: boolean;
  selecionado: number | null;
  aoSoltar: (id: number, etapa: Etapa) => void;
}) {
  const [sobre, setSobre] = useState(false);
  const [recolhida, setRecolhida] = useState(!aberta);

  const lista = (
    <ul className="flex flex-col gap-2">
      {itens.map((p) => (
        <CartaoProcesso key={p.id} p={p} agora={agora} arrastavel={desktop} ativo={p.id === selecionado} />
      ))}
      {itens.length === 0 && <li className="suave py-3 text-center text-xs">Vazio</li>}
    </ul>
  );

  if (!desktop) {
    return (
      <section className="cartao">
        <h2>
          <button
            type="button"
            aria-expanded={!recolhida}
            onClick={() => setRecolhida((r) => !r)}
            className="flex w-full items-center justify-between px-4 py-3 text-left font-semibold"
          >
            <span>
              {rotulo} <span className="suave tabular font-normal">({itens.length})</span>
            </span>
            <span aria-hidden>{recolhida ? "▸" : "▾"}</span>
          </button>
        </h2>
        {!recolhida && <div className="px-3 pb-3">{lista}</div>}
      </section>
    );
  }

  return (
    <section
      aria-label={rotulo}
      data-etapa={etapa}
      onDragOver={(e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        setSobre(true);
      }}
      onDragLeave={() => setSobre(false)}
      onDrop={(e) => {
        e.preventDefault();
        setSobre(false);
        const id = Number(e.dataTransfer.getData("text/plain"));
        if (id) aoSoltar(id, etapa);
      }}
      className={`min-w-[220px] flex-1 rounded-lg p-2 ${sobre ? "bg-acento-suave" : "bg-superficie-2"}`}
    >
      <h2 className="mb-2 px-1 text-sm font-semibold">
        {rotulo} <span className="suave tabular font-normal">({itens.length})</span>
      </h2>
      {lista}
    </section>
  );
}
