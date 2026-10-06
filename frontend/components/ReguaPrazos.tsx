"use client";

import Link from "next/link";
import { useState } from "react";
import { prazoRelativo } from "@/lib/format";
import type { Painel } from "@/lib/types";

const TZ = "America/Sao_Paulo";
const chaveDia = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" });
const diaSemana = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", weekday: "short" });
const hora = new Intl.DateTimeFormat("pt-BR", { timeZone: TZ, hour: "2-digit", minute: "2-digit" });

function somarDias(chave: string, n: number): { chave: string; data: Date } {
  const d = new Date(`${chave}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return { chave: d.toISOString().slice(0, 10), data: d };
}

const MAX_POR_DIA = 4;

/**
 * Régua dos próximos 14 dias: cada edital aparece no dia em que as propostas encerram.
 * Vermelho = até 48h. A sigla do estado e a hora vão escritas, então a cor nunca é a única pista.
 */
export default function ReguaPrazos({ prazos, urgentes }: { prazos: Painel["prazos"]; urgentes: number }) {
  const [foco, setFoco] = useState<number | null>(null);
  const hoje = chaveDia.format(new Date());
  const dias = Array.from({ length: 14 }, (_, i) => somarDias(hoje, i));
  const porDia = new Map<string, Painel["prazos"]>();
  for (const p of prazos) {
    const k = chaveDia.format(new Date(p.data_encerramento));
    porDia.set(k, [...(porDia.get(k) ?? []), p]);
  }

  return (
    <section className="cartao p-4 lg:p-6">
      <div className="mb-4 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h2 className="text-base font-semibold">Prazos das próximas duas semanas</h2>
        <p className="suave text-sm">
          {prazos.length === 0
            ? "Nenhum edital relevante encerra nesse período."
            : `${prazos.length} editais encerram propostas`}
        </p>
        {urgentes > 0 && (
          <span className="rounded-full bg-vermelho-suave px-2.5 py-0.5 text-sm font-semibold text-vermelho-texto lg:ml-auto">
            {urgentes} {urgentes === 1 ? "encerra" : "encerram"} em até 48h
          </span>
        )}
      </div>

      <div className="-mx-4 overflow-x-auto px-4 lg:mx-0 lg:px-0">
        <ol className="grid min-w-[880px] grid-cols-14 gap-[2px]" style={{ gridTemplateColumns: "repeat(14, minmax(0, 1fr))" }}>
          {dias.map(({ chave, data }, i) => {
            const lista = porDia.get(chave) ?? [];
            const urgenteDia = i <= 1;
            const fimDeSemana = [0, 6].includes(data.getUTCDay());
            return (
              <li key={chave} className="flex min-h-[148px] flex-col">
                <div
                  className={`mb-1.5 rounded-t-lg px-1.5 pb-1.5 pt-1 text-center ${
                    i === 0 ? "bg-vermelho-suave text-vermelho-texto" : fimDeSemana ? "suave" : ""
                  }`}
                >
                  <p className="text-[11px] capitalize">{i === 0 ? "hoje" : diaSemana.format(data).replace(".", "")}</p>
                  <p className="tabular text-lg font-semibold leading-tight">{data.getUTCDate()}</p>
                </div>
                <div
                  className={`flex flex-1 flex-col gap-1 rounded-b-lg p-1 ${
                    urgenteDia ? "bg-vermelho-suave/50" : fimDeSemana ? "bg-superficie-2/60" : "bg-superficie-2"
                  }`}
                >
                  {lista.slice(0, MAX_POR_DIA).map((p) => (
                    <div key={p.id} className="relative">
                      <Link
                        href={`/editais/${p.id}`}
                        onMouseEnter={() => setFoco(p.id)}
                        onMouseLeave={() => setFoco(null)}
                        onFocus={() => setFoco(p.id)}
                        onBlur={() => setFoco(null)}
                        aria-label={`${p.objeto}. Encerra ${prazoRelativo(p.data_encerramento).texto}.`}
                        className={`flex items-center justify-between gap-1 rounded-md px-1.5 py-1 text-[11px] font-semibold ${
                          urgenteDia
                            ? "bg-vermelho text-white"
                            : p.status === "participando" || p.status === "analisando"
                              ? "bg-azul text-white"
                              : "bg-superficie text-azul-texto ring-1 ring-inset ring-azul/30"
                        }`}
                      >
                        <span>{p.uf ?? "—"}</span>
                        <span className="tabular font-medium opacity-90">{hora.format(new Date(p.data_encerramento)).replace(":00", "h")}</span>
                      </Link>
                      {foco === p.id && (
                        <div
                          role="tooltip"
                          className={`pointer-events-none absolute top-full z-30 mt-1.5 w-64 rounded-xl border borda bg-superficie p-3 text-left shadow-[0_8px_24px_rgba(20,20,40,0.12)] ${
                            i > 10 ? "right-0" : "left-0"
                          }`}
                        >
                          <p className="line-clamp-3 text-[13px] font-medium leading-snug">{p.objeto}</p>
                          <p className="suave mt-1 truncate text-xs">{p.orgao}</p>
                          <p className="mt-1.5 text-xs font-semibold">{prazoRelativo(p.data_encerramento).texto}</p>
                        </div>
                      )}
                    </div>
                  ))}
                  {lista.length > MAX_POR_DIA && (
                    <Link href="/acompanhamento" className="suave px-1.5 text-[11px] font-medium hover:underline">
                      +{lista.length - MAX_POR_DIA}
                    </Link>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="suave mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs">
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-sm bg-vermelho" />Até 48h</span>
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-sm bg-azul" />No seu funil</span>
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-sm ring-1 ring-inset ring-azul/40" />Relevante, ainda não analisado</span>
      </div>
    </section>
  );
}
