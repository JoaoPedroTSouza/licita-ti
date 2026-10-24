"use client";

import { useState } from "react";
import { lembretes } from "@/shared/api/cliente";
import type { Lembrete } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { dataHora, localParaIso, mensagemDe } from "./datas";

export default function SecaoLembretes({
  id,
  itens,
  aoMudar,
}: {
  id: number;
  itens: Lembrete[];
  aoMudar: () => Promise<void>;
}) {
  const [texto, setTexto] = useState("");
  const [venceEm, setVenceEm] = useState("");
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function agir(chave: string, acao: () => Promise<unknown>): Promise<boolean> {
    setOcupado(chave);
    setErro(null);
    try {
      await acao();
      await aoMudar();
      return true;
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível concluir."));
      return false;
    } finally {
      setOcupado(null);
    }
  }

  async function criar(e: React.FormEvent) {
    e.preventDefault();
    const iso = localParaIso(venceEm);
    if (!texto.trim() || !iso) return;
    const ok = await agir("novo", () => lembretes.criar({ texto: texto.trim(), vence_em: iso, processo_id: id }));
    if (ok) {
      setTexto("");
      setVenceEm("");
    }
  }

  const pendentes = itens.filter((l) => !l.concluido);

  return (
    <section aria-labelledby="titulo-lembretes">
      <h3 id="titulo-lembretes" className="mb-2 font-semibold">Lembretes</h3>
      <ul className="mb-2 flex flex-col gap-2">
        {pendentes.map((l) => (
          <li key={l.id} className="rounded-md bg-superficie-2 p-2 text-sm">
            <p>{l.texto}</p>
            <p className="suave text-xs">{dataHora(l.vence_em)}</p>
            <div className="mt-1 flex gap-2">
              <Botao variante="secundario" disabled={ocupado !== null} onClick={() => agir(`c${l.id}`, () => lembretes.concluir(l.id))}>
                Concluir
              </Botao>
              <Botao variante="secundario" disabled={ocupado !== null} onClick={() => agir(`r${l.id}`, () => lembretes.remover(l.id))}>
                Remover
              </Botao>
            </div>
          </li>
        ))}
        {pendentes.length === 0 && <li className="suave text-sm">Sem lembretes pendentes.</li>}
      </ul>
      <form onSubmit={criar} className="flex flex-col gap-2">
        <input
          aria-label="Texto do lembrete"
          placeholder="Lembrar de…"
          className="campo"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />
        <input
          aria-label="Data e hora do lembrete"
          type="datetime-local"
          className="campo"
          value={venceEm}
          onChange={(e) => setVenceEm(e.target.value)}
        />
        <Botao type="submit" disabled={ocupado !== null || !texto.trim() || !venceEm} className="self-end">
          Criar lembrete
        </Botao>
      </form>
      {erro && (
        <p role="alert" className="mt-2 text-sm text-perigo">
          {erro}
        </p>
      )}
    </section>
  );
}
