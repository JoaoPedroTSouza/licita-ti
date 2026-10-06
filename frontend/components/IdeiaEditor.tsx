"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import {
  PRIORIDADES,
  STATUS_IDEIA,
  TIPOS_IDEIA,
  type Ideia,
  type Prioridade,
  type StatusIdeia,
  type TipoIdeia,
} from "@/lib/types";

export type Rascunho = {
  titulo: string;
  descricao: string;
  tipo: TipoIdeia;
  status: StatusIdeia;
  prioridade: Prioridade;
  tags: string;
  potencial_mensal: string;
  edital_id: number | null;
};

export const RASCUNHO_VAZIO: Rascunho = {
  titulo: "",
  descricao: "",
  tipo: "produto",
  status: "nova",
  prioridade: "media",
  tags: "",
  potencial_mensal: "",
  edital_id: null,
};

export function paraRascunho(i: Ideia): Rascunho {
  return {
    titulo: i.titulo,
    descricao: i.descricao ?? "",
    tipo: i.tipo,
    status: i.status,
    prioridade: i.prioridade,
    tags: i.tags.join(", "),
    potencial_mensal: i.potencial_mensal ? String(i.potencial_mensal) : "",
    edital_id: i.edital_id,
  };
}

/** Painel lateral (desktop) / tela cheia (celular) para criar e editar uma ideia. */
export default function IdeiaEditor({
  ideia,
  inicial,
  onFechar,
  onSalvo,
  onExcluido,
}: {
  ideia: Ideia | null;
  inicial: Rascunho;
  onFechar: () => void;
  onSalvo: (i: Ideia) => void;
  onExcluido: (id: number) => void;
}) {
  const [r, setR] = useState<Rascunho>(inicial);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const tituloRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    tituloRef.current?.focus();
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onFechar();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onFechar]);

  const set = <K extends keyof Rascunho>(k: K, v: Rascunho[K]) => setR((a) => ({ ...a, [k]: v }));

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!r.titulo.trim()) return setErro("Dê um título para a ideia.");
    setSalvando(true);
    setErro("");
    const corpo = {
      titulo: r.titulo.trim(),
      descricao: r.descricao.trim() || null,
      tipo: r.tipo,
      status: r.status,
      prioridade: r.prioridade,
      tags: r.tags.split(",").map((t) => t.trim()).filter(Boolean),
      potencial_mensal: r.potencial_mensal ? Number(r.potencial_mensal.replace(/\./g, "").replace(",", ".")) : null,
      edital_id: r.edital_id,
    };
    try {
      const salvo = ideia
        ? await api<Ideia>(`/ideias/${ideia.id}`, { method: "PATCH", body: JSON.stringify(corpo) })
        : await api<Ideia>("/ideias", { method: "POST", body: JSON.stringify(corpo) });
      onSalvo(salvo);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível salvar.");
    } finally {
      setSalvando(false);
    }
  }

  async function excluir() {
    if (!ideia || !confirm(`Excluir a ideia “${ideia.titulo}”? Isso não pode ser desfeito.`)) return;
    try {
      await api(`/ideias/${ideia.id}`, { method: "DELETE" });
      onExcluido(ideia.id);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível excluir.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label={ideia ? "Editar ideia" : "Nova ideia"}>
      <button aria-label="Fechar" onClick={onFechar} className="absolute inset-0 bg-[#15151c]/25 backdrop-blur-[1px]" />
      <form
        onSubmit={salvar}
        className="relative flex h-full w-full flex-col bg-superficie shadow-[-12px_0_40px_rgba(20,20,40,0.12)] sm:w-[480px] sm:border-l sm:borda"
        style={{ paddingTop: "env(safe-area-inset-top)", paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="flex items-center gap-3 border-b borda px-6 py-4">
          <span className="h-2.5 w-2.5 rounded-full bg-roxo" aria-hidden />
          <h2 className="flex-1 text-base font-semibold">{ideia ? "Editar ideia" : "Nova ideia"}</h2>
          <button type="button" onClick={onFechar} className="suave rounded-lg px-2 py-1 text-sm hover:bg-superficie-2">
            Fechar
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <input
            ref={tituloRef}
            className="w-full bg-transparent text-xl font-semibold outline-none placeholder:text-texto-suave/60 focus-visible:outline-none"
            placeholder="Qual é a ideia?"
            value={r.titulo}
            maxLength={200}
            onChange={(e) => set("titulo", e.target.value)}
          />
          <textarea
            className="campo min-h-32 text-sm leading-relaxed"
            placeholder="Problema que resolve, para quem, como ganhar dinheiro com isso, primeiros passos…"
            value={r.descricao}
            onChange={(e) => set("descricao", e.target.value)}
          />

          <Campo rotulo="Situação">
            <div className="flex flex-wrap gap-1.5">
              {(Object.keys(STATUS_IDEIA) as StatusIdeia[]).map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => set("status", s)}
                  className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium ${
                    r.status === s ? "bg-acao-roxo text-white" : "bg-superficie-2 hover:bg-roxo-suave"
                  }`}
                >
                  {STATUS_IDEIA[s].singular}
                </button>
              ))}
            </div>
          </Campo>

          <div className="grid gap-4 sm:grid-cols-2">
            <Campo rotulo="Tipo">
              <select className="campo text-sm" value={r.tipo} onChange={(e) => set("tipo", e.target.value as TipoIdeia)}>
                {(Object.keys(TIPOS_IDEIA) as TipoIdeia[]).map((t) => (
                  <option key={t} value={t}>{TIPOS_IDEIA[t]}</option>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Prioridade">
              <div className="grid grid-cols-3 gap-1.5">
                {(["baixa", "media", "alta"] as Prioridade[]).map((p) => (
                  <button
                    type="button"
                    key={p}
                    onClick={() => set("prioridade", p)}
                    className={`rounded-lg py-2 text-xs font-semibold ${
                      r.prioridade === p ? PRIORIDADES[p].cor + " ring-1 ring-current" : "bg-superficie-2"
                    }`}
                  >
                    {PRIORIDADES[p].rotulo}
                  </button>
                ))}
              </div>
            </Campo>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Campo rotulo="Potencial por mês (R$)">
              <input
                className="campo tabular text-sm"
                inputMode="decimal"
                placeholder="Ex.: 3000"
                value={r.potencial_mensal}
                onChange={(e) => set("potencial_mensal", e.target.value.replace(/[^\d.,]/g, ""))}
              />
            </Campo>
            <Campo rotulo="Etiquetas">
              <input
                className="campo text-sm"
                placeholder="saas, nicho, ia"
                value={r.tags}
                onChange={(e) => set("tags", e.target.value)}
              />
            </Campo>
          </div>

          {r.edital_id && (
            <div className="flex items-center gap-3 rounded-xl bg-azul-suave px-4 py-3 text-sm">
              <span className="flex-1">
                Ligada ao{" "}
                <Link href={`/editais/${r.edital_id}`} className="font-semibold text-azul-texto underline-offset-2 hover:underline">
                  edital #{r.edital_id}
                </Link>
              </span>
              <button type="button" onClick={() => set("edital_id", null)} className="suave text-xs hover:underline">
                Desvincular
              </button>
            </div>
          )}

          {erro && <p className="rounded-xl bg-vermelho-suave p-3 text-sm text-vermelho-texto">{erro}</p>}
        </div>

        <div className="flex items-center gap-2 border-t borda px-6 py-4">
          {ideia && (
            <button type="button" onClick={excluir} className="rounded-lg px-3 py-2 text-sm font-medium text-vermelho-texto hover:bg-vermelho-suave">
              Excluir
            </button>
          )}
          <span className="flex-1" />
          <button type="button" onClick={onFechar} className="botao botao-sec">Cancelar</button>
          <button className="botao botao-roxo" disabled={salvando}>
            {salvando ? "Salvando…" : ideia ? "Salvar alterações" : "Criar ideia"}
          </button>
        </div>
      </form>
    </div>
  );
}

/** Grupo de campo. Usa <div> (não <label>) porque alguns grupos são conjuntos de botões. */
function Campo({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div role="group" aria-label={rotulo}>
      <span className="mb-1.5 block text-sm font-medium">{rotulo}</span>
      {children}
    </div>
  );
}
