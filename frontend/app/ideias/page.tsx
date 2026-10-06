"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import IdeiaEditor, { RASCUNHO_VAZIO, paraRascunho, type Rascunho } from "@/components/IdeiaEditor";
import { api } from "@/lib/api";
import { formatarValorCurto } from "@/lib/format";
import { PRIORIDADES, STATUS_IDEIA, TIPOS_IDEIA, type Ideia, type StatusIdeia, type TipoIdeia } from "@/lib/types";

const COLUNAS: StatusIdeia[] = ["nova", "validando", "executando", "concluida"];
const PESO = { alta: 0, media: 1, baixa: 2 } as const;

export default function Page() {
  return (
    <Suspense>
      <Ideias />
    </Suspense>
  );
}

function Ideias() {
  const router = useRouter();
  const params = useSearchParams();
  const [ideias, setIdeias] = useState<Ideia[] | null>(null);
  const [erro, setErro] = useState("");
  const [busca, setBusca] = useState("");
  const [tipo, setTipo] = useState<TipoIdeia | "">("");
  const [verDescartadas, setVerDescartadas] = useState(false);
  const [abaMobile, setAbaMobile] = useState<StatusIdeia>("nova");
  const [editor, setEditor] = useState<{ ideia: Ideia | null; inicial: Rascunho } | null>(null);
  const [arrastando, setArrastando] = useState<number | null>(null);
  const [alvo, setAlvo] = useState<StatusIdeia | null>(null);
  const [rapida, setRapida] = useState("");

  useEffect(() => {
    api<Ideia[]>("/ideias")
      .then(setIdeias)
      .catch((e) => setErro(e instanceof Error ? e.message : "Não foi possível carregar as ideias."));
  }, []);

  // ?nova=1 abre o editor; ?edital=ID abre já ligado ao edital
  useEffect(() => {
    const edital = params.get("edital");
    if (params.get("nova") || edital) {
      setEditor({
        ideia: null,
        inicial: edital ? { ...RASCUNHO_VAZIO, tipo: "proposta", edital_id: Number(edital) } : RASCUNHO_VAZIO,
      });
    }
  }, [params]);

  const fecharEditor = useCallback(() => {
    setEditor(null);
    if (params.get("nova") || params.get("edital")) router.replace("/ideias");
  }, [params, router]);

  const colunas = verDescartadas ? [...COLUNAS, "descartada" as StatusIdeia] : COLUNAS;

  const visiveis = useMemo(() => {
    const t = busca.trim().toLowerCase();
    return (ideias ?? []).filter(
      (i) =>
        (!tipo || i.tipo === tipo) &&
        (!t || i.titulo.toLowerCase().includes(t) || (i.descricao ?? "").toLowerCase().includes(t) || i.tags.some((g) => g.includes(t)))
    );
  }, [ideias, busca, tipo]);

  const porColuna = (s: StatusIdeia) =>
    visiveis.filter((i) => i.status === s).sort((a, b) => PESO[a.prioridade] - PESO[b.prioridade] || b.atualizado_em.localeCompare(a.atualizado_em));

  function aplicar(salva: Ideia) {
    setIdeias((lista) => {
      const sem = (lista ?? []).filter((i) => i.id !== salva.id);
      return [salva, ...sem];
    });
  }

  async function mover(id: number, status: StatusIdeia) {
    const atual = ideias?.find((i) => i.id === id);
    if (!atual || atual.status === status) return;
    aplicar({ ...atual, status }); // otimista
    try {
      aplicar(await api<Ideia>(`/ideias/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }));
    } catch {
      aplicar(atual);
      setErro("Não foi possível mover a ideia. Tente de novo.");
    }
  }

  async function criarRapida(e: React.FormEvent) {
    e.preventDefault();
    const titulo = rapida.trim();
    if (!titulo) return;
    setRapida("");
    try {
      aplicar(await api<Ideia>("/ideias", { method: "POST", body: JSON.stringify({ titulo }) }));
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível criar a ideia.");
    }
  }

  const potencialTotal = (ideias ?? [])
    .filter((i) => i.status === "validando" || i.status === "executando")
    .reduce((a, i) => a + (i.potencial_mensal ?? 0), 0);

  return (
    <Shell
      titulo="Ideias"
      subtitulo={
        ideias
          ? `${ideias.filter((i) => i.status !== "descartada").length} ideias${
              potencialTotal ? `, potencial de ${formatarValorCurto(potencialTotal)}/mês no que está em validação ou execução` : ""
            }`
          : " "
      }
      acao={
        <button className="botao botao-roxo" onClick={() => setEditor({ ideia: null, inicial: RASCUNHO_VAZIO })}>
          <span className="lg:hidden">Nova</span>
          <span className="hidden lg:inline">Nova ideia</span>
        </button>
      }
    >
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <input
          type="search"
          className="campo lg:w-[360px]"
          placeholder="Buscar por título, descrição ou etiqueta"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
        <select className="campo text-sm lg:w-56" value={tipo} onChange={(e) => setTipo(e.target.value as TipoIdeia | "")}>
          <option value="">Todos os tipos</option>
          {(Object.keys(TIPOS_IDEIA) as TipoIdeia[]).map((t) => (
            <option key={t} value={t}>{TIPOS_IDEIA[t]}</option>
          ))}
        </select>
        <span className="hidden flex-1 lg:block" />
        <label className="suave flex items-center gap-2 text-sm">
          <input type="checkbox" className="h-4 w-4 accent-[var(--roxo)]" checked={verDescartadas} onChange={(e) => setVerDescartadas(e.target.checked)} />
          Mostrar descartadas
        </label>
      </div>

      {erro && <p className="mb-4 rounded-xl bg-vermelho-suave p-3 text-sm text-vermelho-texto">{erro}</p>}
      {!ideias && !erro && <p className="suave py-16 text-center text-sm">Carregando ideias…</p>}

      {ideias && (
        <>
          {/* Abas no celular */}
          <div className="cartao mb-4 flex gap-1 overflow-x-auto p-1 lg:hidden">
            {colunas.map((s) => (
              <button
                key={s}
                onClick={() => setAbaMobile(s)}
                className={`shrink-0 rounded-lg px-3 py-2 text-sm font-medium ${abaMobile === s ? "bg-roxo text-white" : "suave"}`}
              >
                {STATUS_IDEIA[s].rotulo} <span className="tabular opacity-75">{porColuna(s).length}</span>
              </button>
            ))}
          </div>

          <div className={`grid gap-4 lg:items-start ${colunas.length === 5 ? "lg:grid-cols-5" : "lg:grid-cols-4"}`}>
            <>
              {colunas.map((s) => {
                const lista = porColuna(s);
                const sobre = alvo === s && arrastando !== null;
                return (
                  <section
                    key={s}
                    className={`${abaMobile === s ? "" : "hidden"} rounded-2xl p-2 transition-colors lg:block ${
                      sobre ? "bg-roxo-suave ring-2 ring-roxo/40" : "lg:bg-superficie-2/70"
                    }`}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setAlvo(s);
                    }}
                    onDragLeave={() => setAlvo((a) => (a === s ? null : a))}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (arrastando !== null) mover(arrastando, s);
                      setArrastando(null);
                      setAlvo(null);
                    }}
                  >
                    <header className="hidden px-2 pb-3 pt-2 lg:block">
                      <div className="flex items-baseline justify-between">
                        <h2 className="text-sm font-semibold">{STATUS_IDEIA[s].rotulo}</h2>
                        <span className="suave tabular text-sm">{lista.length}</span>
                      </div>
                      <p className="suave mt-0.5 text-xs">{STATUS_IDEIA[s].dica}</p>
                    </header>

                    {s === "nova" && (
                      <form onSubmit={criarRapida} className="mb-2">
                        <input
                          className="campo border-dashed bg-transparent text-sm"
                          placeholder="Anotar ideia rápida e Enter"
                          value={rapida}
                          onChange={(e) => setRapida(e.target.value)}
                        />
                      </form>
                    )}

                    <div className="space-y-2">
                      {lista.map((i) => (
                        <CartaoIdeia
                          key={i.id}
                          i={i}
                          arrastando={arrastando === i.id}
                          onAbrir={() => setEditor({ ideia: i, inicial: paraRascunho(i) })}
                          onArrastar={(ativo) => setArrastando(ativo ? i.id : null)}
                        />
                      ))}
                      {lista.length === 0 && (
                        <p className="suave rounded-xl border border-dashed borda px-3 py-6 text-center text-xs">
                          {s === "nova" ? "Nenhuma ideia anotada ainda." : "Arraste uma ideia para cá."}
                        </p>
                      )}
                    </div>
                  </section>
                );
              })}
            </>
          </div>
        </>
      )}

      {editor && (
        <IdeiaEditor
          ideia={editor.ideia}
          inicial={editor.inicial}
          onFechar={fecharEditor}
          onSalvo={(i) => {
            aplicar(i);
            fecharEditor();
          }}
          onExcluido={(id) => {
            setIdeias((l) => (l ?? []).filter((x) => x.id !== id));
            fecharEditor();
          }}
        />
      )}
    </Shell>
  );
}

function CartaoIdeia({
  i,
  arrastando,
  onAbrir,
  onArrastar,
}: {
  i: Ideia;
  arrastando: boolean;
  onAbrir: () => void;
  onArrastar: (ativo: boolean) => void;
}) {
  return (
    <button
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = "move";
        onArrastar(true);
      }}
      onDragEnd={() => onArrastar(false)}
      onClick={onAbrir}
      className={`cartao block w-full p-3.5 text-left transition hover:border-roxo/40 ${arrastando ? "opacity-40" : ""} lg:cursor-grab`}
    >
      <div className="mb-1.5 flex items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${PRIORIDADES[i.prioridade].cor}`}>
          {PRIORIDADES[i.prioridade].rotulo}
        </span>
        <span className="suave truncate text-xs">{TIPOS_IDEIA[i.tipo]}</span>
      </div>
      <p className="line-clamp-2 text-sm font-semibold leading-snug">{i.titulo}</p>
      {i.descricao && <p className="suave mt-1 line-clamp-2 text-xs leading-relaxed">{i.descricao}</p>}

      {i.edital && (
        <p className="mt-2 truncate rounded-lg bg-azul-suave px-2 py-1 text-xs text-azul-texto" title={i.edital.objeto}>
          {i.edital.uf ? `${i.edital.uf}: ` : ""}
          {i.edital.objeto}
        </p>
      )}

      {(i.tags.length > 0 || i.potencial_mensal) && (
        <div className="mt-2 flex flex-wrap items-center gap-1">
          {i.tags.slice(0, 3).map((t) => (
            <span key={t} className="suave rounded-md bg-superficie-2 px-1.5 py-0.5 text-[11px]">{t}</span>
          ))}
          {i.potencial_mensal ? (
            <span className="tabular ml-auto text-xs font-semibold text-roxo-texto">{formatarValorCurto(i.potencial_mensal)}/mês</span>
          ) : null}
        </div>
      )}
    </button>
  );
}
