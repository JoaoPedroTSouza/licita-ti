"use client";

import { useState } from "react";
import { oportunidades } from "@/shared/api/cliente";
import Botao from "@/shared/ui/Botao";
import DialogoDescarte from "./DialogoDescarte";

/** Botões Interessa/Descartar com o diálogo de motivo, estado ocupado e erro. */
export default function AcoesOportunidade({
  id,
  aoInteressar,
  aoDescartar,
}: {
  id: number;
  aoInteressar: (processoId: number) => void;
  aoDescartar: () => void;
}) {
  const [ocupado, setOcupado] = useState(false);
  const [dialogo, setDialogo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function agir(acao: () => Promise<void>) {
    setOcupado(true);
    setErro(null);
    try {
      await acao();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível concluir.");
      setDialogo(false);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div>
      <div className="flex gap-2">
        <Botao
          disabled={ocupado}
          onClick={() => agir(async () => aoInteressar((await oportunidades.interessa(id)).id))}
        >
          Interessa
        </Botao>
        <Botao variante="secundario" disabled={ocupado} onClick={() => setDialogo(true)}>
          Descartar
        </Botao>
      </div>
      {erro && <p role="alert" className="mt-2 text-sm text-perigo">{erro}</p>}
      {dialogo && (
        <DialogoDescarte
          ocupado={ocupado}
          aoCancelar={() => setDialogo(false)}
          aoConfirmar={(motivo) =>
            agir(async () => {
              await oportunidades.descartar(id, motivo || undefined);
              aoDescartar();
            })
          }
        />
      )}
    </div>
  );
}
