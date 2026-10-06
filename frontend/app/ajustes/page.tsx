"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";
import { formatarData } from "@/lib/format";
import { ativarPush, desativarPush, inscricaoAtual, pushSuportado } from "@/lib/push";
import type { Preferencias } from "@/lib/types";

const UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" ");

interface Execucao {
  id: number;
  finalizado_em: string | null;
  data_referencia: string;
  recebidos: number;
  novos: number;
  relevantes: number;
  notificados: number;
  erro: string | null;
}

const linhas = (t: string) => t.split("\n").map((s) => s.trim()).filter(Boolean);

export default function AjustesPage() {
  const [prefs, setPrefs] = useState<Preferencias | null>(null);
  const [modalidades, setModalidades] = useState<Record<string, string>>({});
  const [chaves, setChaves] = useState("");
  const [exclusoes, setExclusoes] = useState("");
  const [msg, setMsg] = useState("");
  const [pushAtivo, setPushAtivo] = useState(false);
  const [pushMsg, setPushMsg] = useState("");
  const [historico, setHistorico] = useState<Execucao[]>([]);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    api<{ preferencias: Preferencias; modalidades: Record<string, string> }>("/config").then((r) => {
      setPrefs(r.preferencias);
      setModalidades(r.modalidades);
      setChaves(r.preferencias.palavras_chave.join("\n"));
      setExclusoes(r.preferencias.palavras_exclusao.join("\n"));
    });
    api<Execucao[]>("/coleta/historico").then(setHistorico).catch(() => {});
    inscricaoAtual().then((s) => setPushAtivo(Boolean(s)));
  }, []);

  function avisar(texto: string) {
    setMsg(texto);
    setTimeout(() => setMsg(""), 4500);
  }

  async function salvar() {
    if (!prefs) return;
    setSalvando(true);
    try {
      const corpo = { ...prefs, palavras_chave: linhas(chaves), palavras_exclusao: linhas(exclusoes) };
      const r = await api<{ preferencias: Preferencias }>("/config", { method: "PUT", body: JSON.stringify(corpo) });
      setPrefs(r.preferencias);
      avisar("Preferências salvas. Valem a partir da próxima coleta.");
    } finally {
      setSalvando(false);
    }
  }

  async function alternarPush() {
    setPushMsg("");
    try {
      if (pushAtivo) {
        await desativarPush();
        setPushAtivo(false);
      } else {
        await ativarPush();
        setPushAtivo(true);
        setPushMsg("Alertas ativados neste aparelho.");
      }
    } catch (e) {
      setPushMsg(e instanceof Error ? e.message : "Não foi possível configurar as notificações.");
    }
  }

  async function coletarAgora(dias: number) {
    const r = await api<{ mensagem: string }>("/coleta", { method: "POST", body: JSON.stringify({ dias }) });
    avisar(r.mensagem);
  }

  const botaoSalvar = (
    <button className="botao" onClick={salvar} disabled={!prefs || salvando}>
      {salvando ? "Salvando…" : "Salvar preferências"}
    </button>
  );

  if (!prefs) {
    return (
      <Shell titulo="Ajustes">
        <p className="suave py-16 text-center text-sm">Carregando…</p>
      </Shell>
    );
  }

  const toggle = <T,>(lista: T[], item: T) => (lista.includes(item) ? lista.filter((x) => x !== item) : [...lista, item]);

  return (
    <Shell titulo="Ajustes" subtitulo="O que monitorar, quando avisar e como a IA avalia os editais" acao={<span className="hidden lg:block">{botaoSalvar}</span>}>
      {msg && (
        <p className="mb-4 rounded-xl bg-azul-suave p-3 text-sm text-azul-texto" role="status">
          {msg}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-2 lg:gap-5">
        {/* ---------- Coluna 1: o que buscar ---------- */}
        <div className="space-y-4 lg:space-y-5">
          <Secao titulo="Palavras-chave" ajuda="Uma por linha, sem acento. Plurais simples são reconhecidos.">
            <textarea className="campo min-h-56 font-mono text-xs leading-relaxed" value={chaves} onChange={(e) => setChaves(e.target.value)} />
            <p className="mb-1.5 mt-4 text-sm font-medium">Descartar quando contiver</p>
            <textarea className="campo min-h-32 font-mono text-xs leading-relaxed" value={exclusoes} onChange={(e) => setExclusoes(e.target.value)} />
          </Secao>

          <Secao titulo="Estados" ajuda="Nenhum marcado = Brasil todo.">
            <div className="grid grid-cols-7 gap-1.5 sm:grid-cols-9">
              {UFS.map((uf) => (
                <button
                  key={uf}
                  onClick={() => setPrefs({ ...prefs, ufs: toggle(prefs.ufs, uf) })}
                  aria-pressed={prefs.ufs.includes(uf)}
                  className={`rounded-lg py-1.5 text-xs font-semibold ${prefs.ufs.includes(uf) ? "bg-acao-azul text-white" : "bg-superficie-2 hover:bg-azul-suave"}`}
                >
                  {uf}
                </button>
              ))}
            </div>
          </Secao>

          <Secao titulo="Modalidades monitoradas">
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(modalidades).map(([cod, nome]) => (
                <label key={cod} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-[var(--azul)]"
                    checked={prefs.modalidades.includes(Number(cod))}
                    onChange={() => setPrefs({ ...prefs, modalidades: toggle(prefs.modalidades, Number(cod)) })}
                  />
                  {nome}
                </label>
              ))}
            </div>
          </Secao>

          <Secao titulo="Faixa de valor" ajuda="Em reais. Deixe em branco para não limitar.">
            <div className="grid grid-cols-2 gap-2">
              <input type="number" inputMode="numeric" className="campo tabular" placeholder="Mínimo" value={prefs.valor_minimo || ""}
                onChange={(e) => setPrefs({ ...prefs, valor_minimo: Number(e.target.value) || 0 })} />
              <input type="number" inputMode="numeric" className="campo tabular" placeholder="Máximo" value={prefs.valor_maximo || ""}
                onChange={(e) => setPrefs({ ...prefs, valor_maximo: Number(e.target.value) || 0 })} />
            </div>
          </Secao>
        </div>

        {/* ---------- Coluna 2: IA, avisos e coleta ---------- */}
        <div className="space-y-4 lg:space-y-5">
          <Secao titulo="Seu perfil" ajuda="A IA usa este texto para julgar se o edital cabe no seu porte e especialidade." tom="roxo">
            <textarea className="campo min-h-28 text-sm leading-relaxed" value={prefs.perfil} onChange={(e) => setPrefs({ ...prefs, perfil: e.target.value })} />
            <label className="mt-4 block text-sm">
              <span className="flex justify-between">
                Nota mínima da IA para avisar
                <b className="tabular text-roxo-texto">{prefs.score_minimo_ia_push}</b>
              </span>
              <input
                type="range"
                min={30}
                max={95}
                step={5}
                value={prefs.score_minimo_ia_push}
                onChange={(e) => setPrefs({ ...prefs, score_minimo_ia_push: Number(e.target.value) })}
                className="mt-2 w-full accent-[var(--roxo)]"
              />
            </label>
          </Secao>

          <Secao titulo="Notificações">
            {pushSuportado() ? (
              <>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium">Alertas neste aparelho</p>
                    <p className="suave text-xs">Novos editais relevantes e prazos se aproximando.</p>
                  </div>
                  <button
                    role="switch"
                    aria-checked={pushAtivo}
                    aria-label="Alertas neste aparelho"
                    onClick={alternarPush}
                    className={`relative h-7 w-12 shrink-0 rounded-full transition ${pushAtivo ? "bg-acao-azul" : "bg-borda"}`}
                  >
                    <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all ${pushAtivo ? "left-6" : "left-1"}`} />
                  </button>
                </div>
                {pushMsg && <p className="mt-2 text-xs">{pushMsg}</p>}
                {pushAtivo && (
                  <button className="botao botao-sec mt-3 w-full text-sm" onClick={() => api("/push/teste", { method: "POST" })}>
                    Enviar notificação de teste
                  </button>
                )}
              </>
            ) : (
              <p className="suave text-sm">Abra no Chrome do Android e instale o app para receber notificações.</p>
            )}
          </Secao>

          <Secao titulo="Coleta" ajuda="Automática às 7h, 12h e 18h. Use os botões para buscar agora.">
            <div className="grid grid-cols-2 gap-2">
              <button className="botao botao-sec text-sm" onClick={() => coletarAgora(1)}>Coletar hoje</button>
              <button className="botao botao-sec text-sm" onClick={() => coletarAgora(7)}>Coletar últimos 7 dias</button>
            </div>
            <ul className="mt-4 divide-y divide-borda text-xs">
              {historico.slice(0, 8).map((h) => (
                <li key={h.id} className="flex justify-between gap-2 py-2">
                  <span className="suave tabular">{formatarData(h.finalizado_em)}</span>
                  {h.erro ? (
                    <span className="font-medium text-vermelho-texto" title={h.erro}>Falhou</span>
                  ) : (
                    <span className="tabular">
                      {h.recebidos} lidos, {h.novos} novos, {h.relevantes} relevantes
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </Secao>
        </div>
      </div>

      <div className="sticky bottom-24 z-10 mt-5 lg:hidden">
        <div className="[&>button]:w-full [&>button]:shadow-lg">{botaoSalvar}</div>
      </div>
    </Shell>
  );
}

function Secao({
  titulo,
  ajuda,
  tom,
  children,
}: {
  titulo: string;
  ajuda?: string;
  tom?: "roxo";
  children: React.ReactNode;
}) {
  return (
    <section className={`cartao p-5 lg:p-6 ${tom === "roxo" ? "border-roxo/25" : ""}`}>
      <h2 className="text-base font-semibold">{titulo}</h2>
      {ajuda && <p className="suave mb-3 mt-0.5 text-sm">{ajuda}</p>}
      {!ajuda && <div className="mb-3" />}
      {children}
    </section>
  );
}
