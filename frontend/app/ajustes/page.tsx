"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, setToken } from "@/lib/api";
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
  const router = useRouter();
  const [prefs, setPrefs] = useState<Preferencias | null>(null);
  const [modalidades, setModalidades] = useState<Record<string, string>>({});
  const [chaves, setChaves] = useState("");
  const [exclusoes, setExclusoes] = useState("");
  const [msg, setMsg] = useState("");
  const [pushAtivo, setPushAtivo] = useState(false);
  const [pushMsg, setPushMsg] = useState("");
  const [historico, setHistorico] = useState<Execucao[]>([]);

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

  async function salvar() {
    if (!prefs) return;
    const corpo = { ...prefs, palavras_chave: linhas(chaves), palavras_exclusao: linhas(exclusoes) };
    const r = await api<{ preferencias: Preferencias }>("/config", { method: "PUT", body: JSON.stringify(corpo) });
    setPrefs(r.preferencias);
    setMsg("Preferências salvas. Valem a partir da próxima coleta.");
    setTimeout(() => setMsg(""), 4000);
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
      setPushMsg(e instanceof Error ? e.message : "Falha ao configurar notificações");
    }
  }

  async function coletarAgora(dias: number) {
    const r = await api<{ mensagem: string }>("/coleta", { method: "POST", body: JSON.stringify({ dias }) });
    setMsg(r.mensagem);
  }

  if (!prefs) {
    return (
      <Shell titulo="Ajustes">
        <p className="suave py-10 text-center text-sm">Carregando…</p>
      </Shell>
    );
  }

  const toggle = <T,>(lista: T[], item: T) => (lista.includes(item) ? lista.filter((x) => x !== item) : [...lista, item]);

  return (
    <Shell titulo="Ajustes">
      {msg && <p className="mb-4 rounded-xl bg-marca-suave p-3 text-sm text-marca-forte">{msg}</p>}

      <Secao titulo="Notificações">
        {pushSuportado() ? (
          <>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Alertas de novos editais</p>
                <p className="suave text-xs">Novos editais relevantes e prazos se aproximando.</p>
              </div>
              <button
                role="switch"
                aria-checked={pushAtivo}
                onClick={alternarPush}
                className={`relative h-7 w-12 shrink-0 rounded-full transition ${pushAtivo ? "bg-marca" : "bg-zinc-300 dark:bg-zinc-700"}`}
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

      <Secao titulo="Seu perfil (usado pela IA)">
        <textarea className="campo min-h-24 text-sm" value={prefs.perfil} onChange={(e) => setPrefs({ ...prefs, perfil: e.target.value })} />
        <label className="mt-3 block text-sm">
          Nota mínima da IA para notificar: <b className="tabular-nums">{prefs.score_minimo_ia_push}</b>
          <input
            type="range"
            min={30}
            max={95}
            step={5}
            value={prefs.score_minimo_ia_push}
            onChange={(e) => setPrefs({ ...prefs, score_minimo_ia_push: Number(e.target.value) })}
            className="mt-1 w-full accent-teal-700"
          />
        </label>
      </Secao>

      <Secao titulo="Palavras-chave (uma por linha)">
        <textarea className="campo min-h-40 font-mono text-xs" value={chaves} onChange={(e) => setChaves(e.target.value)} />
        <p className="suave mt-1 text-xs">Sem acento e em minúsculas. Plurais simples são reconhecidos.</p>
        <p className="mb-1 mt-4 text-sm font-medium">Excluir quando contiver</p>
        <textarea className="campo min-h-28 font-mono text-xs" value={exclusoes} onChange={(e) => setExclusoes(e.target.value)} />
      </Secao>

      <Secao titulo="Estados (nenhum = Brasil todo)">
        <div className="flex flex-wrap gap-1.5">
          {UFS.map((uf) => (
            <button
              key={uf}
              onClick={() => setPrefs({ ...prefs, ufs: toggle(prefs.ufs, uf) })}
              className={`w-11 rounded-lg py-1.5 text-xs font-semibold ${prefs.ufs.includes(uf) ? "bg-marca text-white" : "cartao"}`}
            >
              {uf}
            </button>
          ))}
        </div>
      </Secao>

      <Secao titulo="Modalidades monitoradas">
        <div className="space-y-2">
          {Object.entries(modalidades).map(([cod, nome]) => (
            <label key={cod} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 accent-teal-700"
                checked={prefs.modalidades.includes(Number(cod))}
                onChange={() => setPrefs({ ...prefs, modalidades: toggle(prefs.modalidades, Number(cod)) })}
              />
              {nome}
            </label>
          ))}
        </div>
      </Secao>

      <Secao titulo="Faixa de valor (R$, 0 = sem limite)">
        <div className="grid grid-cols-2 gap-2">
          <input type="number" inputMode="numeric" className="campo" placeholder="Mínimo" value={prefs.valor_minimo || ""}
            onChange={(e) => setPrefs({ ...prefs, valor_minimo: Number(e.target.value) || 0 })} />
          <input type="number" inputMode="numeric" className="campo" placeholder="Máximo" value={prefs.valor_maximo || ""}
            onChange={(e) => setPrefs({ ...prefs, valor_maximo: Number(e.target.value) || 0 })} />
        </div>
      </Secao>

      <button className="botao sticky bottom-24 z-10 mb-6 w-full shadow-lg" onClick={salvar}>
        Salvar preferências
      </button>

      <Secao titulo="Coleta">
        <div className="grid grid-cols-2 gap-2">
          <button className="botao botao-sec text-sm" onClick={() => coletarAgora(1)}>Coletar hoje</button>
          <button className="botao botao-sec text-sm" onClick={() => coletarAgora(7)}>Últimos 7 dias</button>
        </div>
        <ul className="mt-3 divide-y borda text-xs">
          {historico.slice(0, 6).map((h) => (
            <li key={h.id} className="flex justify-between py-2">
              <span className="suave">{formatarData(h.finalizado_em)}</span>
              {h.erro ? (
                <span className="text-red-600">falhou</span>
              ) : (
                <span className="tabular-nums">
                  {h.recebidos} lidos · {h.novos} novos · {h.relevantes} relevantes
                </span>
              )}
            </li>
          ))}
        </ul>
      </Secao>

      <button
        className="botao botao-sec mb-6 w-full text-red-600"
        onClick={() => {
          setToken(null);
          router.replace("/login");
        }}
      >
        Sair
      </button>
    </Shell>
  );
}

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="cartao mb-4 p-4">
      <h2 className="mb-3 text-sm font-bold">{titulo}</h2>
      {children}
    </section>
  );
}
