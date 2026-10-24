"use client";

import { useState } from "react";
import { processos } from "@/shared/api/cliente";
import type { Nota } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { dataHora, mensagemDe } from "./datas";

export default function SecaoNotas({
  id,
  notas,
  aoMudar,
}: {
  id: number;
  notas: Nota[];
  aoMudar: () => Promise<void>;
}) {
  const [texto, setTexto] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function adicionar(e: React.FormEvent) {
    e.preventDefault();
    if (!texto.trim()) return;
    setOcupado(true);
    setErro(null);
    try {
      await processos.anotar(id, texto.trim());
      setTexto("");
      await aoMudar();
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível salvar a nota."));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section aria-labelledby="titulo-notas">
      <h3 id="titulo-notas" className="mb-2 font-semibold">Notas</h3>
      <form onSubmit={adicionar} className="mb-2 flex flex-col gap-2">
        <textarea aria-label="Nova nota" rows={2} className="campo" value={texto} onChange={(e) => setTexto(e.target.value)} />
        <Botao type="submit" disabled={ocupado || !texto.trim()} className="self-end">
          Anotar
        </Botao>
      </form>
      {erro && (
        <p role="alert" className="mb-2 text-sm text-perigo">
          {erro}
        </p>
      )}
      <ul className="flex flex-col gap-2">
        {[...notas].reverse().map((n, i) => (
          <li key={i} className="rounded-md bg-superficie-2 p-2 text-sm">
            <p className="whitespace-pre-line">{n.texto}</p>
            <p className="suave mt-1 text-xs">{dataHora(n.criada_em)}</p>
          </li>
        ))}
        {notas.length === 0 && <li className="suave text-sm">Sem notas.</li>}
      </ul>
    </section>
  );
}
