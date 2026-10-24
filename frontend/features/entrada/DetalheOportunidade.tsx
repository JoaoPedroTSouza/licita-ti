"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { oportunidades } from "@/shared/api/cliente";
import type { OportunidadeDetalhe } from "@/shared/api/tipos";
import { useContagemEntrada } from "@/app/(workspace)/ContagemEntrada";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import Etiqueta from "@/shared/ui/Etiqueta";
import NotaBadge from "@/shared/ui/NotaBadge";
import AcoesOportunidade from "./AcoesOportunidade";
import { Metadados } from "./CartaoOportunidade";

export default function DetalheOportunidade({ id }: { id: number }) {
  const [o, setO] = useState<OportunidadeDetalhe | null>(null);
  const [erro, setErro] = useState(false);
  const router = useRouter();
  const { atualizar } = useContagemEntrada();

  const carregar = useCallback(async () => {
    setErro(false);
    try {
      setO(await oportunidades.obter(id));
    } catch {
      setErro(true);
    }
  }, [id]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  if (!o) {
    if (!erro) return <Carregando />;
    return (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar a oportunidade.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    );
  }

  const voltar = (consulta = "") => {
    void atualizar();
    router.push(`/entrada${consulta}`);
  };

  let acao: React.ReactNode;
  if (o.status === "nova") {
    acao = (
      <AcoesOportunidade
        id={o.id}
        aoInteressar={(p) => voltar(`?interessa=${p}`)}
        aoDescartar={() => voltar()}
      />
    );
  } else if (o.processo_id !== null) {
    acao = (
      <p className="text-sm">
        Você marcou como interessante.{" "}
        <Link href={`/funil?processo=${o.processo_id}`} className="font-semibold underline">Ver no funil</Link>
      </p>
    );
  } else {
    acao = <p className="suave text-sm">Descartada.</p>;
  }

  return (
    <article className="max-w-3xl">
      <Link href="/entrada" className="suave mb-3 inline-block text-sm hover:underline">← Entrada</Link>
      <div className="flex items-start gap-3">
        <NotaBadge nota={o.nota} />
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold tracking-tight">{o.titulo}</h1>
          <Metadados o={o} agora={new Date()} />
        </div>
        {o.pessoa_fisica && <span className="shrink-0"><Etiqueta tom="aviso">Pessoa física</Etiqueta></span>}
      </div>
      <div className="my-4">{acao}</div>
      {o.resumo && (
        <section className="mb-4">
          <h2 className="mb-1 font-semibold">Resumo</h2>
          <p className="text-sm">{o.resumo}</p>
        </section>
      )}
      {o.motivo && (
        <section className="mb-4">
          <h2 className="mb-1 font-semibold">Motivo da nota</h2>
          <p className="text-sm">{o.motivo}</p>
        </section>
      )}
      {o.trecho_modalidade && (
        <section className="mb-4">
          <h2 className="mb-1 font-semibold">Trecho que indica trabalho remoto</h2>
          <blockquote className="border-l-2 border-borda pl-3 text-sm italic">{o.trecho_modalidade}</blockquote>
        </section>
      )}
      <details className="mb-4">
        <summary className="cursor-pointer font-semibold">Texto completo</summary>
        <p className="mt-2 whitespace-pre-line text-sm">{o.texto}</p>
      </details>
      <a href={o.link} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold underline">
        Abrir chamada original
      </a>
    </article>
  );
}
