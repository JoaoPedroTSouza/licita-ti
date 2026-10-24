"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { processos } from "@/shared/api/cliente";
import type { Etapa, ProcessoResumo } from "@/shared/api/tipos";
import { ETAPAS } from "@/shared/formato";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import ColunaEtapa from "./ColunaEtapa";
import DetalheProcesso from "./DetalheProcesso";
import FormProcesso from "./FormProcesso";
import { mensagemDe } from "./datas";

const ABERTAS: Etapa[] = ["analisando", "proposta_enviada", "negociacao"];

/** true a partir de 1024 px; começa falso e corrige no navegador. */
function useDesktop(): boolean {
  const [desktop, setDesktop] = useState(false);
  useEffect(() => {
    const m = window.matchMedia("(min-width: 1024px)");
    const atualizar = () => setDesktop(m.matches);
    atualizar();
    m.addEventListener("change", atualizar);
    return () => m.removeEventListener("change", atualizar);
  }, []);
  return desktop;
}

export default function QuadroFunil() {
  const [itens, setItens] = useState<ProcessoResumo[] | null>(null);
  const [erro, setErro] = useState(false);
  const [erroMover, setErroMover] = useState<string | null>(null);
  const [novo, setNovo] = useState(false);
  const desktop = useDesktop();
  const router = useRouter();
  const param = useSearchParams().get("processo");
  const selecionado = param && Number(param) > 0 ? Number(param) : null;

  const carregar = useCallback(async () => {
    try {
      setItens(await processos.listar());
      setErro(false);
    } catch {
      setErro(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function soltar(id: number, etapa: Etapa) {
    const antes = itens;
    const alvo = antes?.find((p) => p.id === id);
    if (!alvo || alvo.etapa === etapa) return;
    setErroMover(null);
    setItens((l) => l && l.map((p) => (p.id === id ? { ...p, etapa } : p)));
    try {
      await processos.mover(id, etapa);
      void carregar();
    } catch (e) {
      setItens(antes);
      setErroMover(`Não foi possível mover "${alvo.titulo}": ${mensagemDe(e, "erro desconhecido")}`);
    }
  }

  if (!itens) {
    return erro ? (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar o funil.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    ) : (
      <Carregando />
    );
  }

  const agora = new Date();

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold tracking-tight">Funil</h1>
        <Botao onClick={() => setNovo(true)}>Novo processo</Botao>
      </div>
      {erroMover && (
        <p role="alert" className="mb-3 text-sm text-perigo">
          {erroMover}
        </p>
      )}
      <div className={desktop ? "flex gap-3 overflow-x-auto pb-2" : "flex flex-col gap-3"}>
        {ETAPAS.map((e) => (
          <ColunaEtapa
            key={e.id}
            etapa={e.id}
            rotulo={e.rotulo}
            itens={itens.filter((p) => p.etapa === e.id)}
            agora={agora}
            desktop={desktop}
            aberta={ABERTAS.includes(e.id)}
            selecionado={selecionado}
            aoSoltar={soltar}
          />
        ))}
      </div>
      {selecionado !== null && (
        <DetalheProcesso
          key={selecionado}
          id={selecionado}
          desktop={desktop}
          aoFechar={() => router.replace("/funil")}
          aoMudar={carregar}
        />
      )}
      {novo && (
        <FormProcesso
          aoCancelar={() => setNovo(false)}
          aoCriar={(p) => {
            setNovo(false);
            void carregar();
            router.push(`/funil?processo=${p.id}`);
          }}
        />
      )}
    </div>
  );
}
