"use client";

import { useEffect, useRef, useState } from "react";
import Botao from "@/shared/ui/Botao";

/** Diálogo modal nativo: Esc ou "Cancelar" fecham; o motivo é opcional. */
export default function DialogoDescarte({
  aoConfirmar,
  aoCancelar,
  ocupado,
}: {
  aoConfirmar: (motivo: string) => void;
  aoCancelar: () => void;
  ocupado: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const campo = useRef<HTMLTextAreaElement>(null);
  const [motivo, setMotivo] = useState("");

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
    campo.current?.focus();
    return () => d?.close();
  }, []);

  return (
    <dialog
      ref={ref}
      aria-labelledby="titulo-descarte"
      onCancel={(e) => {
        e.preventDefault();
        aoCancelar();
      }}
      className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-lg border border-borda bg-superficie p-5 text-texto backdrop:bg-black/50"
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          aoConfirmar(motivo.trim());
        }}
      >
        <h2 id="titulo-descarte" className="mb-3 text-lg font-semibold">Descartar oportunidade</h2>
        <label htmlFor="motivo-descarte" className="mb-1 block text-sm">
          Por quê? (ajuda a melhorar as próximas notas)
        </label>
        <textarea
          id="motivo-descarte"
          ref={campo}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-borda bg-fundo p-2 text-sm"
        />
        <div className="mt-4 flex justify-end gap-2">
          <Botao variante="secundario" onClick={aoCancelar} disabled={ocupado}>Cancelar</Botao>
          <Botao type="submit" variante="perigo" disabled={ocupado}>Descartar</Botao>
        </div>
      </form>
    </dialog>
  );
}
