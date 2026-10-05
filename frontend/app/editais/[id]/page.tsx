"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Shell from "@/components/Shell";
import { ScoreBadge } from "@/components/EditalCard";
import { api } from "@/lib/api";
import { formatarData, formatarValor, prazoRelativo } from "@/lib/format";
import { STATUS_INFO, type EditalDetalhe, type Status } from "@/lib/types";

const ORDEM: Status[] = ["novo", "analisando", "participando", "descartado"];

export default function EditalPage() {
  const { id } = useParams<{ id: string }>();
  const [e, setE] = useState<EditalDetalhe | null>(null);
  const [erro, setErro] = useState("");
  const [notas, setNotas] = useState("");
  const [salvandoNotas, setSalvandoNotas] = useState<"" | "salvando" | "salvo">("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api<EditalDetalhe>(`/editais/${id}`)
      .then((d) => {
        setE(d);
        setNotas(d.notas ?? "");
      })
      .catch((err) => setErro(err.message));
  }, [id]);

  async function atualizar(campos: Partial<Pick<EditalDetalhe, "status" | "favorito" | "notas">>) {
    if (!e) return;
    setE({ ...e, ...campos }); // otimista
    try {
      const d = await api<EditalDetalhe>(`/editais/${id}`, { method: "PATCH", body: JSON.stringify(campos) });
      setE(d);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha ao salvar");
    }
  }

  function mudarNotas(valor: string) {
    setNotas(valor);
    setSalvandoNotas("salvando");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      await atualizar({ notas: valor });
      setSalvandoNotas("salvo");
    }, 800);
  }

  async function compartilhar() {
    if (!e) return;
    const url = e.link_pncp ?? location.href;
    if (navigator.share) await navigator.share({ title: "Edital", text: e.objeto, url }).catch(() => {});
    else await navigator.clipboard.writeText(url);
  }

  const acaoFavorito = e && (
    <button
      onClick={() => atualizar({ favorito: !e.favorito })}
      aria-label={e.favorito ? "Remover dos favoritos" : "Favoritar"}
      className={`rounded-full p-2 text-xl leading-none ${e.favorito ? "text-amber-500" : "suave"}`}
    >
      {e.favorito ? "★" : "☆"}
    </button>
  );

  if (erro && !e) {
    return (
      <Shell titulo="Edital" voltar>
        <p className="cartao p-4 text-sm text-red-600">{erro}</p>
      </Shell>
    );
  }
  if (!e) {
    return (
      <Shell titulo="Edital" voltar>
        <p className="suave py-10 text-center text-sm">Carregando…</p>
      </Shell>
    );
  }

  const prazo = prazoRelativo(e.data_encerramento);

  return (
    <Shell titulo={e.orgao ?? "Edital"} voltar acao={acaoFavorito}>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <ScoreBadge score={e.ia_score} />
        {e.ia_categoria && <span className="cartao px-2 py-0.5">{e.ia_categoria}</span>}
        <span className="suave">{e.modalidade_nome}</span>
        {e.srp && <span className="suave">· Registro de preços</span>}
      </div>

      <h2 className="text-lg font-semibold leading-snug">{e.objeto}</h2>

      <section className="cartao mt-4 grid grid-cols-2 gap-x-4 gap-y-3 p-4 text-sm">
        <Campo rotulo="Valor estimado" valor={formatarValor(e.valor_estimado)} destaque />
        <Campo
          rotulo="Propostas até"
          valor={
            <>
              {formatarData(e.data_encerramento)}
              <span className={`block text-xs ${prazo.urgente ? "text-red-600 dark:text-red-400" : "suave"}`}>{prazo.texto}</span>
            </>
          }
        />
        <Campo rotulo="Abertura" valor={formatarData(e.data_abertura)} />
        <Campo rotulo="Local" valor={`${e.municipio ?? "—"}/${e.uf ?? "—"}`} />
        <Campo rotulo="Disputa" valor={e.modo_disputa ?? "—"} />
        <Campo rotulo="Nº da compra" valor={e.numero_compra ?? "—"} />
        <div className="col-span-2">
          <Campo rotulo="Unidade" valor={e.unidade ?? "—"} />
        </div>
      </section>

      {e.ia_resumo && (
        <section className="mt-4 rounded-2xl border-l-4 border-marca p-4" style={{ background: "var(--superficie)" }}>
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-marca">Análise da IA</p>
          <p className="text-sm leading-relaxed">{e.ia_resumo}</p>
          {e.ia_motivo && <p className="suave mt-2 text-xs">{e.ia_motivo}</p>}
          {e.ia_exigencias.length > 0 && (
            <>
              <p className="mt-3 text-xs font-semibold">Exigências prováveis</p>
              <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">
                {e.ia_exigencias.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      {e.informacao_complementar && (
        <details className="cartao mt-4 p-4 text-sm">
          <summary className="cursor-pointer font-semibold">Informação complementar</summary>
          <p className="suave mt-2 whitespace-pre-line">{e.informacao_complementar}</p>
        </details>
      )}

      <section className="mt-5">
        <p className="mb-2 text-sm font-semibold">Situação no meu funil</p>
        <div className="grid grid-cols-2 gap-2">
          {ORDEM.map((s) => (
            <button
              key={s}
              onClick={() => atualizar({ status: s })}
              className={`rounded-xl px-3 py-2.5 text-sm font-semibold transition ${
                e.status === s ? `${STATUS_INFO[s].cor} ring-2 ring-current` : "cartao"
              }`}
            >
              {STATUS_INFO[s].rotulo}
            </button>
          ))}
        </div>
        {(e.status === "analisando" || e.status === "participando") && (
          <p className="suave mt-2 text-xs">Você receberá um lembrete antes do prazo de propostas encerrar.</p>
        )}
      </section>

      <section className="mt-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-sm font-semibold">Minhas notas</p>
          <span className="suave text-xs">{salvandoNotas === "salvando" ? "salvando…" : salvandoNotas === "salvo" ? "salvo" : ""}</span>
        </div>
        <textarea
          className="campo min-h-28"
          placeholder="Documentos pendentes, dúvidas para impugnação, preço pensado…"
          value={notas}
          onChange={(ev) => mudarNotas(ev.target.value)}
        />
      </section>

      <section className="mt-5 grid gap-2">
        {e.link_pncp && (
          <a href={e.link_pncp} target="_blank" rel="noreferrer" className="botao">
            Ver edital e anexos no PNCP
          </a>
        )}
        {e.link_origem && (
          <a href={e.link_origem} target="_blank" rel="noreferrer" className="botao botao-sec">
            Abrir no sistema de origem
          </a>
        )}
        <button onClick={compartilhar} className="botao botao-sec">
          Compartilhar
        </button>
      </section>

      {e.keywords_encontradas.length > 0 && (
        <p className="suave mt-5 text-xs">Encontrado por: {e.keywords_encontradas.join(", ")}</p>
      )}
      <p className="suave mt-1 mb-4 text-xs">PNCP {e.numero_controle_pncp}</p>
    </Shell>
  );
}

function Campo({ rotulo, valor, destaque }: { rotulo: string; valor: React.ReactNode; destaque?: boolean }) {
  return (
    <div>
      <p className="suave text-[11px] uppercase tracking-wide">{rotulo}</p>
      <div className={destaque ? "text-base font-bold" : "font-medium"}>{valor}</div>
    </div>
  );
}
