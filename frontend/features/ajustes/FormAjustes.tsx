"use client";

import { useCallback, useEffect, useState } from "react";
import { ajustes } from "@/shared/api/cliente";
import type { Ajustes } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import { mensagemDe } from "@/features/funil/datas";

/** Lista "3, 1" vira [3, 1]; devolve null se algum item não for inteiro positivo. */
function lerDias(texto: string): number[] | null {
  const partes = texto.split(",").map((p) => p.trim()).filter((p) => p !== "");
  const dias = partes.map((p) => (/^\d+$/.test(p) ? Number(p) : NaN));
  return dias.every((d) => Number.isInteger(d) && d > 0) ? dias : null;
}

/** Limiar do alerta imediato, horário do resumo diário e dias de aviso antes de um prazo. */
export default function FormAjustes() {
  const [limiar, setLimiar] = useState("");
  const [horario, setHorario] = useState("");
  const [dias, setDias] = useState("");
  const [carregado, setCarregado] = useState(false);
  const [erroCarga, setErroCarga] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [salvo, setSalvo] = useState(false);

  const preencher = (a: Ajustes) => {
    setLimiar(String(a.limiar_alerta));
    setHorario(a.horario_resumo);
    setDias(a.avisos_prazo_dias.join(", "));
  };

  const carregar = useCallback(async () => {
    try {
      preencher(await ajustes.obter());
      setErroCarga(false);
      setCarregado(true);
    } catch {
      setErroCarga(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setSalvo(false);
    const lista = lerDias(dias);
    if (!lista) {
      setErro("Informe os dias de aviso como números inteiros positivos separados por vírgula, por exemplo 3, 1.");
      return;
    }
    if (limiar.trim() === "" || !Number.isFinite(Number(limiar))) {
      setErro("Informe o limiar do alerta como um número.");
      return;
    }
    setOcupado(true);
    setErro(null);
    try {
      preencher(
        await ajustes.salvar({
          limiar_alerta: Number(limiar),
          horario_resumo: horario,
          avisos_prazo_dias: lista,
        }),
      );
      setSalvo(true);
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível salvar os ajustes."));
    } finally {
      setOcupado(false);
    }
  }

  if (!carregado) {
    return erroCarga ? (
      <div role="alert" className="py-6 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar os ajustes.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    ) : (
      <Carregando />
    );
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-3">
      <label className="text-sm">
        Limiar do alerta imediato (0 a 100)
        <input
          type="number"
          step="1"
          inputMode="numeric"
          className="campo mt-1"
          value={limiar}
          onChange={(e) => setLimiar(e.target.value)}
        />
        <span className="suave mt-1 block text-xs">
          Oportunidades com nota igual ou acima disso geram uma notificação na hora.
        </span>
      </label>
      <label className="text-sm">
        Horário do resumo diário
        <input type="time" required className="campo mt-1" value={horario} onChange={(e) => setHorario(e.target.value)} />
      </label>
      <label className="text-sm">
        Avisar quantos dias antes do prazo
        <input className="campo mt-1" value={dias} onChange={(e) => setDias(e.target.value)} placeholder="3, 1" />
        <span className="suave mt-1 block text-xs">Números separados por vírgula.</span>
      </label>
      {erro && (
        <p role="alert" className="text-sm text-perigo">
          {erro}
        </p>
      )}
      {salvo && (
        <p role="status" className="text-sm text-acento-texto">
          Ajustes salvos.
        </p>
      )}
      <div>
        <Botao type="submit" disabled={ocupado}>
          Salvar ajustes
        </Botao>
      </div>
    </form>
  );
}
