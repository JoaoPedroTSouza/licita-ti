"use client";

import Link from "next/link";
import { formatarAproxBrl, formatarDinheiro, formatarPrazo } from "@/shared/formato";
import type { ProcessoResumo } from "@/shared/api/tipos";

export default function CartaoProcesso({
  p,
  agora,
  arrastavel,
  ativo,
}: {
  p: ProcessoResumo;
  agora: Date;
  arrastavel: boolean;
  ativo: boolean;
}) {
  const prazo = p.prazo ? formatarPrazo(p.prazo, agora) : null;
  return (
    <li
      draggable={arrastavel}
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", String(p.id));
        e.dataTransfer.effectAllowed = "move";
      }}
      className={`cartao ${arrastavel ? "cursor-grab" : ""} ${ativo ? "border-acento" : ""}`}
    >
      <Link href={`/funil?processo=${p.id}`} draggable={false} className="block p-3">
        <p className="text-sm font-semibold leading-snug">{p.titulo}</p>
        {p.organizacao && <p className="suave mt-0.5 text-xs">{p.organizacao}</p>}
        <p className="mt-2 flex flex-wrap items-baseline gap-x-2 text-xs">
          {p.valor && (
            <span className="tabular">
              {formatarDinheiro(p.valor)}{" "}
              {p.valor.moeda !== "BRL" && <span className="suave">{formatarAproxBrl(p.valor_brl)}</span>}
            </span>
          )}
          {prazo && (
            <span className={prazo === "vencido" || prazo.startsWith("hoje") ? "text-perigo" : "suave"}>{prazo}</span>
          )}
        </p>
      </Link>
    </li>
  );
}
