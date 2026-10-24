"use client";

import { useCallback, useEffect, useState } from "react";
import { painel } from "@/shared/api/cliente";
import type { Painel } from "@/shared/api/tipos";
import { formatarDiaPorExtenso } from "@/shared/formato";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import ListaParaFazer from "./ListaParaFazer";
import MelhoresNovas from "./MelhoresNovas";
import ResumoFunil from "./ResumoFunil";

export default function PainelDoDia() {
  const [dados, setDados] = useState<Painel | null>(null);
  const [erro, setErro] = useState(false);

  const carregar = useCallback(async () => {
    setErro(false);
    try {
      setDados(await painel.obter());
    } catch {
      setErro(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  if (!dados) {
    if (!erro) return <Carregando />;
    return (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar o painel.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    );
  }

  const agora = new Date();
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold tracking-tight">{formatarDiaPorExtenso(dados.dia)}</h1>
      <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-2">
        <ListaParaFazer itens={dados.para_fazer} agora={agora} aoAgir={carregar} />
        <ResumoFunil funil={dados.funil} />
        <div className="lg:col-span-2">
          <MelhoresNovas itens={dados.melhores_novas} agora={agora} />
        </div>
      </div>
    </div>
  );
}
