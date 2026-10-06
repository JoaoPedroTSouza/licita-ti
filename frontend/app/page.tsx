"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import ReguaPrazos from "@/components/ReguaPrazos";
import BarrasDiarias from "@/components/BarrasDiarias";
import InstalarApp from "@/components/InstalarApp";
import { StatusBadge } from "@/components/EditalCard";
import { api } from "@/lib/api";
import { formatarData, formatarValorCurto, tempoDesde } from "@/lib/format";
import { STATUS_IDEIA, type Painel, type Status, type StatusIdeia } from "@/lib/types";

export default function PainelPage() {
  const [p, setP] = useState<Painel | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    api<Painel>("/painel")
      .then(setP)
      .catch((e) => setErro(e instanceof Error ? e.message : "Não foi possível carregar o painel."));
  }, []);

  const ultima = p?.coletas[0];

  return (
    <Shell
      titulo="Painel"
      subtitulo={ultima ? `Última coleta ${tempoDesde(ultima.finalizado_em)}` : "Visão geral do monitoramento"}
      acao={
        <Link href="/ideias?nova=1" className="botao botao-roxo hidden lg:inline-flex">
          Nova ideia
        </Link>
      }
    >
      <InstalarApp />
      {erro && <p className="mb-4 rounded-xl bg-vermelho-suave p-3 text-sm text-vermelho-texto">{erro}</p>}
      {!p && !erro && <p className="suave py-16 text-center text-sm">Carregando painel…</p>}

      {p && (
        <div className="space-y-4 lg:space-y-5">
          {/* Números principais: um único painel dividido, não cinco cartões iguais */}
          <section className="cartao grid grid-cols-2 divide-borda sm:grid-cols-3 lg:grid-cols-5 lg:divide-x">
            <Numero valor={p.kpis.relevantes_abertos} rotulo="Relevantes com propostas abertas" href="/editais" />
            <Numero valor={p.kpis.novos_7d} rotulo="Novos relevantes nos últimos 7 dias" href="/editais" />
            <Numero valor={p.kpis.analisando + p.kpis.participando} rotulo="No seu funil agora" href="/acompanhamento" />
            <Numero valor={formatarValorCurto(p.kpis.valor_em_aberto)} rotulo="Valor estimado em aberto" />
            <Numero valor={p.kpis.ideias_ativas} rotulo="Ideias em andamento" href="/ideias" tom="roxo" />
          </section>

          <ReguaPrazos prazos={p.prazos} urgentes={p.kpis.encerrando_48h} />

          <div className="grid gap-4 lg:grid-cols-12 lg:gap-5">
            <section className="cartao p-4 lg:col-span-7 lg:p-6">
              <BarrasDiarias serie={p.serie} />
            </section>

            <section className="cartao p-4 lg:col-span-5 lg:p-6">
              <h2 className="mb-4 text-base font-semibold">Onde estão as oportunidades abertas</h2>
              <BarrasHorizontais itens={p.por_uf.map((u) => ({ rotulo: u.uf, total: u.total }))} vazio="Sem editais abertos no momento." />
              {p.por_categoria.length > 0 && (
                <>
                  <h3 className="mb-2 mt-6 text-sm font-semibold">Por tipo de serviço, segundo a IA</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {p.por_categoria.map((c) => (
                      <span key={c.categoria} className="rounded-full bg-roxo-suave px-2.5 py-1 text-xs text-roxo-texto">
                        {c.categoria} <b className="tabular">{c.total}</b>
                      </span>
                    ))}
                  </div>
                </>
              )}
            </section>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 lg:gap-5">
            <section className="cartao p-4 lg:p-6">
              <Cabecalho titulo="Seu funil" href="/acompanhamento" link="Abrir acompanhamento" />
              <ul className="space-y-2.5">
                {(["novo", "analisando", "participando", "descartado"] as Status[]).map((s) => (
                  <li key={s} className="flex items-center justify-between">
                    <StatusBadge status={s} />
                    <span className="tabular font-semibold">{p.funil[s]}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="cartao border-roxo/25 p-4 lg:p-6">
              <Cabecalho titulo="Ideias" href="/ideias" link="Abrir quadro" tom="roxo" />
              <ul className="space-y-2.5">
                {(["nova", "validando", "executando", "concluida"] as StatusIdeia[]).map((s) => (
                  <li key={s} className="flex items-center justify-between text-sm">
                    <span>{STATUS_IDEIA[s].rotulo}</span>
                    <span className="tabular font-semibold">{p.ideias[s]}</span>
                  </li>
                ))}
              </ul>
              <Link href="/ideias?nova=1" className="botao botao-roxo mt-4 w-full lg:hidden">Nova ideia</Link>
            </section>

            <section className="cartao p-4 md:col-span-2 lg:col-span-1 lg:p-6">
              <Cabecalho titulo="Saúde das coletas" href="/ajustes" link="Coletar agora" />
              {p.coletas.length === 0 ? (
                <p className="suave text-sm">Nenhuma coleta ainda. O worker faz a primeira assim que sobe.</p>
              ) : (
                <ul className="divide-y divide-borda text-sm">
                  {p.coletas.slice(0, 5).map((c) => (
                    <li key={c.id} className="flex items-center gap-2 py-2">
                      <span
                        className={`grid h-5 w-5 place-items-center rounded-full text-[11px] font-bold ${
                          c.erro ? "bg-vermelho-suave text-vermelho-texto" : "bg-ok-suave text-ok-texto"
                        }`}
                        aria-hidden
                      >
                        {c.erro ? "!" : "✓"}
                      </span>
                      <span className="suave flex-1 text-xs">{formatarData(c.finalizado_em)}</span>
                      {c.erro ? (
                        <span className="text-xs font-medium text-vermelho-texto">Falhou</span>
                      ) : (
                        <span className="tabular text-xs">
                          {c.recebidos} lidos, <b>{c.relevantes}</b> relevantes
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      )}
    </Shell>
  );
}

function Numero({
  valor,
  rotulo,
  href,
  tom = "azul",
}: {
  valor: number | string;
  rotulo: string;
  href?: string;
  tom?: "azul" | "roxo";
}) {
  const corpo = (
    <>
      <p className={`tabular text-[28px] font-semibold leading-none tracking-tight ${tom === "roxo" ? "text-roxo-texto" : ""}`}>{valor}</p>
      <p className="suave mt-2 text-[13px] leading-snug">{rotulo}</p>
    </>
  );
  const cls = "block px-4 py-4 lg:px-6 lg:py-5";
  return href ? (
    <Link href={href} className={`${cls} hover:bg-superficie-2 first:rounded-l-[14px] last:rounded-r-[14px]`}>
      {corpo}
    </Link>
  ) : (
    <div className={cls}>{corpo}</div>
  );
}

function Cabecalho({ titulo, href, link, tom = "azul" }: { titulo: string; href: string; link: string; tom?: "azul" | "roxo" }) {
  return (
    <div className="mb-4 flex items-baseline justify-between gap-2">
      <h2 className="text-base font-semibold">{titulo}</h2>
      <Link href={href} className={`text-sm font-medium hover:underline ${tom === "roxo" ? "text-roxo-texto" : "text-azul-texto"}`}>
        {link}
      </Link>
    </div>
  );
}

function BarrasHorizontais({ itens, vazio }: { itens: { rotulo: string; total: number }[]; vazio: string }) {
  if (itens.length === 0) return <p className="suave text-sm">{vazio}</p>;
  const max = Math.max(...itens.map((i) => i.total));
  return (
    <ul className="space-y-2">
      {itens.map((i) => (
        <li key={i.rotulo} className="grid grid-cols-[2.5rem_1fr_2rem] items-center gap-2 text-sm" title={`${i.rotulo}: ${i.total}`}>
          <span className="font-medium">{i.rotulo}</span>
          <span className="h-3 rounded-r-[4px] bg-azul" style={{ width: `${Math.max(4, (i.total / max) * 100)}%` }} />
          <span className="tabular text-right">{i.total}</span>
        </li>
      ))}
    </ul>
  );
}
