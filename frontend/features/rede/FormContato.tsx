"use client";

import { useEffect, useRef, useState } from "react";
import { contatos } from "@/shared/api/cliente";
import type { Contato } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { mensagemDe } from "@/features/funil/datas";

/** Diálogo modal nativo para criar (sem `contato`) ou editar um contato; ao salvar devolve o que o servidor guardou. */
export default function FormContato({
  contato,
  aoSalvar,
  aoCancelar,
}: {
  contato?: Contato;
  aoSalvar: (c: Contato) => void;
  aoCancelar: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [nome, setNome] = useState(contato?.nome ?? "");
  const [organizacao, setOrganizacao] = useState(contato?.organizacao ?? "");
  const [comoConheceu, setComoConheceu] = useState(contato?.como_conheceu ?? "");
  const [frequencia, setFrequencia] = useState(contato?.frequencia_dias?.toString() ?? "");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
    return () => d?.close();
  }, []);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!nome.trim()) return;
    const dias = frequencia.trim() === "" ? null : Number(frequencia);
    if (dias !== null && (!Number.isInteger(dias) || dias < 1)) {
      setErro("A frequência deve ser um número inteiro de dias, a partir de 1.");
      return;
    }
    const dados = {
      nome: nome.trim(),
      organizacao: organizacao.trim() || null,
      como_conheceu: comoConheceu.trim() || null,
      frequencia_dias: dias,
    };
    setOcupado(true);
    setErro(null);
    try {
      aoSalvar(contato ? await contatos.editar(contato.id, dados) : await contatos.criar(dados));
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível salvar o contato."));
      setOcupado(false);
    }
  }

  return (
    <dialog
      ref={ref}
      aria-labelledby="titulo-contato"
      onCancel={(e) => {
        e.preventDefault();
        aoCancelar();
      }}
      className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-lg border border-borda bg-superficie p-5 text-texto backdrop:bg-black/50"
    >
      <form onSubmit={enviar} className="flex flex-col gap-3">
        <h2 id="titulo-contato" className="text-lg font-semibold">
          {contato ? "Editar contato" : "Novo contato"}
        </h2>
        <label className="text-sm">
          Nome
          <input required className="campo mt-1" value={nome} onChange={(e) => setNome(e.target.value)} />
        </label>
        <label className="text-sm">
          Organização
          <input className="campo mt-1" value={organizacao} onChange={(e) => setOrganizacao(e.target.value)} />
        </label>
        <label className="text-sm">
          Como nos conhecemos
          <input className="campo mt-1" value={comoConheceu} onChange={(e) => setComoConheceu(e.target.value)} />
        </label>
        <label className="text-sm">
          Falar a cada (dias)
          <input
            type="number"
            min="1"
            step="1"
            className="campo mt-1"
            value={frequencia}
            onChange={(e) => setFrequencia(e.target.value)}
          />
          <span className="suave mt-1 block text-xs">Deixe vazio para não receber lembrete.</span>
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
          <Botao type="submit" disabled={ocupado || !nome.trim()}>
            Salvar
          </Botao>
        </div>
      </form>
    </dialog>
  );
}
