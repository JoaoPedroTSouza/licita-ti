"use client";

import { useState } from "react";

const dataCurta = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", day: "2-digit", month: "2-digit" });
const diaLongo = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", weekday: "long", day: "numeric", month: "long" });

/** Barras verticais de uma série (azul). Tooltip por barra; alvo de hover = coluna inteira. */
export default function BarrasDiarias({
  serie,
}: {
  serie: { data: string; candidatos: number; relevantes: number }[];
}) {
  const [foco, setFoco] = useState<number | null>(null);
  const max = Math.max(4, ...serie.map((s) => s.relevantes));
  const teto = Math.ceil(max / 4) * 4;
  const linhas = [teto, teto / 2, 0];
  const total = serie.reduce((a, s) => a + s.relevantes, 0);

  return (
    <figure>
      <figcaption className="mb-4 flex items-baseline justify-between gap-4">
        <span className="text-base font-semibold">Editais relevantes por dia de publicação</span>
        <span className="suave tabular text-sm">{total} em 14 dias</span>
      </figcaption>

      <div className="relative flex h-48 gap-3">
        {/* eixo y */}
        <div className="suave tabular flex w-6 flex-col justify-between text-right text-[11px]">
          {linhas.map((v) => (
            <span key={v} className="-translate-y-1/2 first:translate-y-0 last:translate-y-1/2">{v}</span>
          ))}
        </div>

        <div className="relative flex-1">
          {linhas.map((v) => (
            <div
              key={v}
              className="absolute inset-x-0 border-t border-grade"
              style={{ top: `${100 - (v / teto) * 100}%` }}
            />
          ))}
          <div className="absolute inset-0 flex items-end gap-[2px]">
            {serie.map((s, i) => {
              const d = new Date(`${s.data}T12:00:00Z`);
              return (
                <div
                  key={s.data}
                  className="relative flex h-full flex-1 cursor-default items-end justify-center"
                  onMouseEnter={() => setFoco(i)}
                  onMouseLeave={() => setFoco(null)}
                  tabIndex={0}
                  onFocus={() => setFoco(i)}
                  onBlur={() => setFoco(null)}
                  aria-label={`${diaLongo.format(d)}: ${s.relevantes} relevantes de ${s.candidatos} candidatos`}
                >
                  <div
                    className={`w-full max-w-7 rounded-t-[4px] transition-colors ${foco === i ? "bg-azul-forte" : "bg-azul"}`}
                    style={{ height: s.relevantes ? `${(s.relevantes / teto) * 100}%` : 0 }}
                  />
                  {foco === i && (
                    <div
                      role="tooltip"
                      className={`pointer-events-none absolute bottom-full z-20 mb-2 w-44 rounded-xl border borda bg-superficie p-2.5 text-xs shadow-[0_8px_24px_rgba(20,20,40,0.12)] ${
                        i > serie.length - 4 ? "right-0" : i < 3 ? "left-0" : "left-1/2 -translate-x-1/2"
                      }`}
                    >
                      <p className="mb-1 font-semibold capitalize">{diaLongo.format(d)}</p>
                      <p className="flex justify-between"><span className="suave">Relevantes</span><b className="tabular">{s.relevantes}</b></p>
                      <p className="flex justify-between"><span className="suave">Candidatos</span><span className="tabular">{s.candidatos}</span></p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="suave tabular ml-9 mt-2 flex gap-[2px] text-[11px]">
        {serie.map((s, i) => (
          <span key={s.data} className="flex-1 text-center">
            {i % 2 === 0 ? dataCurta.format(new Date(`${s.data}T12:00:00Z`)) : ""}
          </span>
        ))}
      </div>
    </figure>
  );
}
