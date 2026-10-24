"use client";

import { useCallback, useEffect, useState } from "react";
import { perfil } from "@/shared/api/cliente";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import { mensagemDe } from "@/features/funil/datas";

const vazioParaNulo = (v: string) => (v.trim() === "" ? null : v.trim());

/** Perfil profissional: texto que a IA usa para avaliar as oportunidades e a faixa de valor desejada (em reais). */
export default function FormPerfil() {
  const [texto, setTexto] = useState("");
  const [minimo, setMinimo] = useState("");
  const [maximo, setMaximo] = useState("");
  const [carregado, setCarregado] = useState(false);
  const [erroCarga, setErroCarga] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [salvo, setSalvo] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const p = await perfil.obter();
      setTexto(p.texto);
      setMinimo(p.faixa_min_brl ?? "");
      setMaximo(p.faixa_max_brl ?? "");
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
    setOcupado(true);
    setErro(null);
    setSalvo(false);
    try {
      const p = await perfil.salvar({
        texto: texto.trim(),
        faixa_min_brl: vazioParaNulo(minimo),
        faixa_max_brl: vazioParaNulo(maximo),
      });
      setTexto(p.texto);
      setMinimo(p.faixa_min_brl ?? "");
      setMaximo(p.faixa_max_brl ?? "");
      setSalvo(true);
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível salvar o perfil."));
    } finally {
      setOcupado(false);
    }
  }

  if (!carregado) {
    return erroCarga ? (
      <div role="alert" className="py-6 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar o perfil.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    ) : (
      <Carregando />
    );
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-3">
      <label className="text-sm">
        Descreva suas especialidades, áreas de interesse e o tipo de projeto que você quer
        <textarea rows={6} className="campo mt-1" value={texto} onChange={(e) => setTexto(e.target.value)} />
      </label>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className="text-sm">
          Valor mínimo (R$)
          <input
            type="number"
            min="0"
            step="0.01"
            inputMode="decimal"
            className="campo mt-1"
            value={minimo}
            onChange={(e) => setMinimo(e.target.value)}
          />
        </label>
        <label className="text-sm">
          Valor máximo (R$)
          <input
            type="number"
            min="0"
            step="0.01"
            inputMode="decimal"
            className="campo mt-1"
            value={maximo}
            onChange={(e) => setMaximo(e.target.value)}
          />
        </label>
      </div>
      {erro && (
        <p role="alert" className="text-sm text-perigo">
          {erro}
        </p>
      )}
      {salvo && (
        <p role="status" className="text-sm text-acento-texto">
          Perfil salvo.
        </p>
      )}
      <div>
        <Botao type="submit" disabled={ocupado}>
          Salvar perfil
        </Botao>
      </div>
    </form>
  );
}
