"use client";

import { useEffect, useState } from "react";
import { contatos, processos } from "@/shared/api/cliente";
import type { Contato } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { mensagemDe } from "./datas";

export default function SecaoContatos({
  id,
  contatoIds,
  aoMudar,
}: {
  id: number;
  contatoIds: number[];
  aoMudar: () => Promise<void>;
}) {
  const [lista, setLista] = useState<Contato[] | null>(null);
  const [escolhido, setEscolhido] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    contatos
      .listar()
      .then(setLista)
      .catch((e) => setErro(mensagemDe(e, "Não foi possível carregar a Rede.")));
  }, []);

  async function vincular() {
    if (!escolhido) return;
    setOcupado(true);
    setErro(null);
    try {
      await processos.vincularContato(id, Number(escolhido));
      setEscolhido("");
      await aoMudar();
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível vincular o contato."));
    } finally {
      setOcupado(false);
    }
  }

  const vinculados = (lista ?? []).filter((c) => contatoIds.includes(c.id));
  const disponiveis = (lista ?? []).filter((c) => !contatoIds.includes(c.id));

  return (
    <section aria-labelledby="titulo-contatos">
      <h3 id="titulo-contatos" className="mb-2 font-semibold">Contatos</h3>
      <ul className="mb-2 flex flex-col gap-1 text-sm">
        {vinculados.map((c) => (
          <li key={c.id}>
            {c.nome}
            {c.organizacao && <span className="suave"> · {c.organizacao}</span>}
          </li>
        ))}
        {contatoIds.length === 0 && <li className="suave">Nenhum contato vinculado.</li>}
      </ul>
      {disponiveis.length > 0 && (
        <div className="flex gap-2">
          <select
            aria-label="Vincular contato"
            className="campo min-w-0 flex-1"
            value={escolhido}
            onChange={(e) => setEscolhido(e.target.value)}
          >
            <option value="">Escolher da Rede…</option>
            {disponiveis.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
          <Botao onClick={vincular} disabled={ocupado || !escolhido}>
            Vincular
          </Botao>
        </div>
      )}
      {erro && (
        <p role="alert" className="mt-2 text-sm text-perigo">
          {erro}
        </p>
      )}
    </section>
  );
}
