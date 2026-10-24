"use client";

import { useEffect, useRef, useState } from "react";
import { processos } from "@/shared/api/cliente";
import type { Processo } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { MOEDAS, localParaIso, mensagemDe } from "./datas";

/** Diálogo modal nativo para registrar um processo que chegou por fora do app. */
export default function FormProcesso({
  aoCriar,
  aoCancelar,
}: {
  aoCriar: (p: Processo) => void;
  aoCancelar: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [titulo, setTitulo] = useState("");
  const [organizacao, setOrganizacao] = useState("");
  const [valor, setValor] = useState("");
  const [moeda, setMoeda] = useState("BRL");
  const [prazo, setPrazo] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
    return () => d?.close();
  }, []);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) return;
    setOcupado(true);
    setErro(null);
    try {
      const p = await processos.criar({
        titulo: titulo.trim(),
        organizacao: organizacao.trim() || null,
        valor: valor ? { valor, moeda } : null,
        prazo: localParaIso(prazo),
      });
      aoCriar(p);
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível criar o processo."));
      setOcupado(false);
    }
  }

  return (
    <dialog
      ref={ref}
      aria-labelledby="titulo-novo-processo"
      onCancel={(e) => {
        e.preventDefault();
        aoCancelar();
      }}
      className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-lg border border-borda bg-superficie p-5 text-texto backdrop:bg-black/50"
    >
      <form onSubmit={enviar} className="flex flex-col gap-3">
        <h2 id="titulo-novo-processo" className="text-lg font-semibold">Novo processo</h2>
        <label className="text-sm">
          Título
          <input required className="campo mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </label>
        <label className="text-sm">
          Organização
          <input className="campo mt-1" value={organizacao} onChange={(e) => setOrganizacao(e.target.value)} />
        </label>
        <div className="flex gap-2">
          <label className="min-w-0 flex-1 text-sm">
            Valor
            <input
              type="number"
              min="0"
              step="0.01"
              className="campo mt-1"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
            />
          </label>
          <label className="w-24 text-sm">
            Moeda
            <select className="campo mt-1" value={moeda} onChange={(e) => setMoeda(e.target.value)}>
              {MOEDAS.map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="text-sm">
          Prazo
          <input type="datetime-local" className="campo mt-1" value={prazo} onChange={(e) => setPrazo(e.target.value)} />
        </label>
        {erro && (
          <p role="alert" className="text-sm text-perigo">
            {erro}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Botao variante="secundario" onClick={aoCancelar} disabled={ocupado}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={ocupado || !titulo.trim()}>
            Criar
          </Botao>
        </div>
      </form>
    </dialog>
  );
}
