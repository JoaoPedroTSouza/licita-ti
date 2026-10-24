"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { oportunidades, status } from "@/shared/api/cliente";
import type { Oportunidade } from "@/shared/api/tipos";
import { useContagemEntrada } from "@/app/(workspace)/ContagemEntrada";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import Vazio from "@/shared/ui/Vazio";
import CartaoOportunidade from "./CartaoOportunidade";

interface Dados {
  iaConfigurada: boolean;
  itens: Oportunidade[];
}

export default function ListaEntrada() {
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState(false);
  const [aviso, setAviso] = useState<number | null>(null);
  const { atualizar } = useContagemEntrada();

  const carregar = useCallback(async () => {
    setErro(false);
    try {
      const [st, itens] = await Promise.all([status.obter(), oportunidades.listar()]);
      setDados({ iaConfigurada: st.ia_configurada, itens });
    } catch {
      setErro(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
    // Vindo do detalhe após "Interessa": mostra o aviso e limpa o endereço.
    const id = Number(new URLSearchParams(window.location.search).get("interessa"));
    if (id) {
      setAviso(id);
      window.history.replaceState(null, "", "/entrada");
    }
  }, [carregar]);

  useEffect(() => {
    if (aviso === null) return;
    const t = setTimeout(() => setAviso(null), 8000);
    return () => clearTimeout(t);
  }, [aviso]);

  function triado(id: number, processoId?: number) {
    setDados((d) => d && { ...d, itens: d.itens.filter((o) => o.id !== id) });
    if (processoId !== undefined) setAviso(processoId);
    void atualizar();
  }

  let corpo: React.ReactNode;
  if (!dados) {
    corpo = erro ? (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar a Entrada.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    ) : (
      <Carregando />
    );
  } else if (!dados.iaConfigurada) {
    corpo = (
      <Vazio titulo="A IA não está configurada, então nenhuma oportunidade pode ser avaliada. Veja Ajustes." />
    );
  } else if (dados.itens.length === 0) {
    corpo = <Vazio titulo="Nada novo por enquanto." />;
  } else {
    const agora = new Date();
    corpo = (
      <div className="flex flex-col gap-3">
        {dados.itens.map((o) => (
          <CartaoOportunidade
            key={o.id}
            o={o}
            agora={agora}
            aoInteressar={(p) => triado(o.id, p)}
            aoDescartar={() => triado(o.id)}
          />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold tracking-tight">Entrada</h1>
      {aviso !== null && (
        <div role="status" className="mb-4 flex items-center justify-between gap-3 rounded-lg bg-acento-suave px-4 py-3 text-sm text-acento-texto">
          <span>
            Adicionada ao funil.{" "}
            <Link href={`/funil?processo=${aviso}`} className="font-semibold underline">Ver no funil</Link>
          </span>
          <button type="button" onClick={() => setAviso(null)} aria-label="Fechar aviso" className="px-1 text-base">
            ×
          </button>
        </div>
      )}
      {corpo}
    </div>
  );
}
