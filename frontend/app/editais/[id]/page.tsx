"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Shell from "@/components/Shell";
import { Prazo, ScoreBadge } from "@/components/EditalCard";
import { api } from "@/lib/api";
import { formatarData, formatarValor } from "@/lib/format";
import { PRIORIDADES, STATUS_IDEIA, STATUS_INFO, type EditalDetalhe, type Ideia, type Status } from "@/lib/types";

const ORDEM: Status[] = ["novo", "analisando", "participando", "descartado"];

export default function EditalPage() {
  const { id } = useParams<{ id: string }>();
  const [e, setE] = useState<EditalDetalhe | null>(null);
  const [ideias, setIdeias] = useState<Ideia[]>([]);
  const [erro, setErro] = useState("");
  const [notas, setNotas] = useState("");
  const [estadoNotas, setEstadoNotas] = useState<"" | "salvando" | "salvo">("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api<EditalDetalhe>(`/editais/${id}`)
      .then((d) => {
        setE(d);
        setNotas(d.notas ?? "");
      })
      .catch((err) => setErro(err.message));
    api<Ideia[]>(`/ideias?edital_id=${id}`).then(setIdeias).catch(() => {});
  }, [id]);

  async function atualizar(campos: Partial<Pick<EditalDetalhe, "status" | "favorito" | "notas">>) {
    if (!e) return;
    setE({ ...e, ...campos });
    try {
      setE(await api<EditalDetalhe>(`/editais/${id}`, { method: "PATCH", body: JSON.stringify(campos) }));
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível salvar.");
    }
  }

  function mudarNotas(valor: string) {
    setNotas(valor);
    setEstadoNotas("salvando");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      await atualizar({ notas: valor });
      setEstadoNotas("salvo");
    }, 800);
  }

  async function compartilhar() {
    if (!e) return;
    const url = e.link_pncp ?? location.href;
    if (navigator.share) await navigator.share({ title: "Edital", text: e.objeto, url }).catch(() => {});
    else await navigator.clipboard.writeText(url);
  }

  if (!e) {
    return (
      <Shell titulo="Edital" voltar>
        {erro ? (
          <p className="rounded-xl bg-vermelho-suave p-4 text-sm text-vermelho-texto">{erro}</p>
        ) : (
          <p className="suave py-16 text-center text-sm">Carregando edital…</p>
        )}
      </Shell>
    );
  }

  const favorito = (
    <button
      onClick={() => atualizar({ favorito: !e.favorito })}
      aria-pressed={e.favorito}
      className={`botao botao-sec px-3 ${e.favorito ? "text-roxo-texto" : ""}`}
    >
      <span aria-hidden>{e.favorito ? "★" : "☆"}</span>
      <span className="hidden lg:inline">{e.favorito ? "Favorito" : "Favoritar"}</span>
    </button>
  );

  return (
    <Shell titulo={e.orgao ?? "Edital"} subtitulo={`${e.municipio ?? "—"}/${e.uf ?? "—"}, ${e.modalidade_nome ?? ""}`} voltar acao={favorito}>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px] lg:gap-8">
        {/* ---------- Coluna principal ---------- */}
        <div className="min-w-0 space-y-5">
          <div>
            <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
              <ScoreBadge score={e.ia_score} />
              {e.ia_categoria && <span className="rounded-md bg-roxo-suave px-1.5 py-0.5 text-roxo-texto">{e.ia_categoria}</span>}
              {e.srp && <span className="suave">Registro de preços</span>}
            </div>
            <h2 className="max-w-[70ch] text-lg font-semibold leading-snug lg:text-xl">{e.objeto}</h2>
          </div>

          {e.ia_resumo && (
            <section className="rounded-2xl bg-roxo-suave/70 p-5">
              <h3 className="mb-1.5 text-sm font-semibold text-roxo-texto">Análise da IA</h3>
              <p className="max-w-[70ch] text-[15px] leading-relaxed">{e.ia_resumo}</p>
              {e.ia_motivo && <p className="suave mt-2 text-sm">{e.ia_motivo}</p>}
              {e.ia_exigencias.length > 0 && (
                <>
                  <h4 className="mt-4 text-sm font-semibold">Exigências prováveis</h4>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">
                    {e.ia_exigencias.map((x) => <li key={x}>{x}</li>)}
                  </ul>
                </>
              )}
            </section>
          )}

          {e.informacao_complementar && (
            <details className="cartao p-5 text-sm">
              <summary className="cursor-pointer font-semibold">Informação complementar</summary>
              <p className="suave mt-2 max-w-[75ch] whitespace-pre-line leading-relaxed">{e.informacao_complementar}</p>
            </details>
          )}

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Minhas notas</h3>
              <span className="suave text-xs" aria-live="polite">
                {estadoNotas === "salvando" ? "Salvando…" : estadoNotas === "salvo" ? "Salvo" : ""}
              </span>
            </div>
            <textarea
              className="campo min-h-36 text-sm leading-relaxed"
              placeholder="Documentos pendentes, dúvidas para pedir esclarecimento, preço pensado…"
              value={notas}
              onChange={(ev) => mudarNotas(ev.target.value)}
            />
          </section>

          <section className="cartao p-5">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Ideias ligadas a este edital</h3>
              <Link href={`/ideias?edital=${e.id}`} className="text-sm font-medium text-roxo-texto hover:underline">
                Criar ideia
              </Link>
            </div>
            {ideias.length === 0 ? (
              <p className="suave text-sm">Anote aqui a proposta, a estratégia de preço ou um produto que este edital inspirou.</p>
            ) : (
              <ul className="space-y-2">
                {ideias.map((i) => (
                  <li key={i.id} className="flex items-center gap-2 text-sm">
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${PRIORIDADES[i.prioridade].cor}`}>
                      {PRIORIDADES[i.prioridade].rotulo}
                    </span>
                    <Link href="/ideias" className="flex-1 truncate font-medium hover:underline">{i.titulo}</Link>
                    <span className="suave text-xs">{STATUS_IDEIA[i.status].singular}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        {/* ---------- Lateral ---------- */}
        <aside className="space-y-5 lg:sticky lg:top-6 lg:self-start">
          <section className="cartao divide-y divide-borda text-sm">
            <Linha rotulo="Valor estimado"><b className="tabular text-base">{formatarValor(e.valor_estimado)}</b></Linha>
            <Linha rotulo="Propostas até">
              <span className="tabular">{formatarData(e.data_encerramento)}</span>
              <Prazo iso={e.data_encerramento} className="ml-2" />
            </Linha>
            <Linha rotulo="Abertura"><span className="tabular">{formatarData(e.data_abertura)}</span></Linha>
            <Linha rotulo="Disputa">{e.modo_disputa ?? "—"}</Linha>
            <Linha rotulo="Nº da compra"><span className="tabular">{e.numero_compra ?? "—"}</span></Linha>
            <Linha rotulo="Unidade">{e.unidade ?? "—"}</Linha>
          </section>

          <section>
            <h3 className="mb-2 text-sm font-semibold">Situação no meu funil</h3>
            <div className="grid grid-cols-2 gap-2">
              {ORDEM.map((s) => (
                <button
                  key={s}
                  onClick={() => atualizar({ status: s })}
                  aria-pressed={e.status === s}
                  className={`rounded-xl px-3 py-2.5 text-sm font-semibold transition ${
                    e.status === s ? `${STATUS_INFO[s].cor} ring-1 ring-current` : "cartao hover:bg-superficie-2"
                  }`}
                >
                  {STATUS_INFO[s].rotulo}
                </button>
              ))}
            </div>
            {(e.status === "analisando" || e.status === "participando") && (
              <p className="suave mt-2 text-xs">Você recebe um lembrete antes do prazo de propostas encerrar.</p>
            )}
          </section>

          <section className="grid gap-2">
            {e.link_pncp && (
              <a href={e.link_pncp} target="_blank" rel="noreferrer" className="botao">Ver edital e anexos no PNCP</a>
            )}
            {e.link_origem && (
              <a href={e.link_origem} target="_blank" rel="noreferrer" className="botao botao-sec">Abrir no sistema de origem</a>
            )}
            <button onClick={compartilhar} className="botao botao-sec">Compartilhar</button>
          </section>

          <div className="suave space-y-1 text-xs">
            {e.keywords_encontradas.length > 0 && <p>Encontrado por: {e.keywords_encontradas.join(", ")}</p>}
            <p className="tabular">PNCP {e.numero_controle_pncp}</p>
          </div>
        </aside>
      </div>
    </Shell>
  );
}

function Linha({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 px-4 py-3">
      <span className="suave shrink-0">{rotulo}</span>
      <span className="text-right">{children}</span>
    </div>
  );
}
