"use client";

import { useCallback, useEffect, useState } from "react";
import { processos } from "@/shared/api/cliente";
import type { Etapa, Processo } from "@/shared/api/tipos";
import { ETAPAS } from "@/shared/formato";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import SecaoArquivos from "./SecaoArquivos";
import SecaoContatos from "./SecaoContatos";
import SecaoLembretes from "./SecaoLembretes";
import SecaoNotas from "./SecaoNotas";
import { MOEDAS, dataHora, isoParaLocal, localParaIso, mensagemDe } from "./datas";

const rotuloEtapa = (e: Etapa) => ETAPAS.find((x) => x.id === e)?.rotulo ?? e;
const textoValor = (p: Processo) => (p.valor ? String(Number(p.valor.valor)) : "");

function Campos({ p, aoMudar }: { p: Processo; aoMudar: () => Promise<void> }) {
  const [titulo, setTitulo] = useState(p.titulo);
  const [organizacao, setOrganizacao] = useState(p.organizacao ?? "");
  const [valor, setValor] = useState(textoValor(p));
  const [moeda, setMoeda] = useState(p.valor?.moeda ?? "BRL");
  const [prazo, setPrazo] = useState(isoParaLocal(p.prazo));
  const [link, setLink] = useState(p.link ?? "");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) return;
    const dados: Parameters<typeof processos.editar>[1] = {};
    if (titulo.trim() !== p.titulo) dados.titulo = titulo.trim();
    if ((organizacao.trim() || null) !== p.organizacao) dados.organizacao = organizacao.trim() || null;
    if ((link.trim() || null) !== p.link) dados.link = link.trim() || null;
    if (prazo !== isoParaLocal(p.prazo)) dados.prazo = localParaIso(prazo);
    if (valor !== textoValor(p) || (valor && moeda !== p.valor?.moeda)) {
      dados.valor = valor ? { valor, moeda } : null;
    }
    if (Object.keys(dados).length === 0) return;
    setOcupado(true);
    setErro(null);
    try {
      await processos.editar(p.id, dados);
      await aoMudar();
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível salvar."));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <form onSubmit={salvar} className="flex flex-col gap-2">
      <label className="text-sm">
        Título
        <input required className="campo mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
      </label>
      <label className="text-sm">
        Organização
        <input className="campo mt-1" value={organizacao} onChange={(e) => setOrganizacao(e.target.value)} />
      </label>
      <div className="flex gap-2">
        <label className="min-w-0 flex-1 text-sm">
          Valor
          <input
            type="number"
            min="0"
            step="0.01"
            className="campo mt-1"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
          />
        </label>
        <label className="w-24 text-sm">
          Moeda
          <select className="campo mt-1" value={moeda} onChange={(e) => setMoeda(e.target.value)}>
            {MOEDAS.map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </label>
      </div>
      <label className="text-sm">
        Prazo
        <input type="datetime-local" className="campo mt-1" value={prazo} onChange={(e) => setPrazo(e.target.value)} />
      </label>
      <label className="text-sm">
        Link
        <input type="url" className="campo mt-1" value={link} onChange={(e) => setLink(e.target.value)} />
      </label>
      {p.link && (
        <a href={p.link} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold underline">
          Abrir link
        </a>
      )}
      {erro && (
        <p role="alert" className="text-sm text-perigo">
          {erro}
        </p>
      )}
      <Botao type="submit" disabled={ocupado || !titulo.trim()} className="self-end">
        Salvar
      </Botao>
    </form>
  );
}

function Mover({ p, aoMudar }: { p: Processo; aoMudar: () => Promise<void> }) {
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function mover(etapa: Etapa) {
    if (etapa === p.etapa) return;
    setOcupado(true);
    setErro(null);
    try {
      await processos.mover(p.id, etapa);
      await aoMudar();
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível mover."));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div>
      <label className="text-sm font-semibold" htmlFor="mover-para">
        Mover para…
      </label>
      <select
        id="mover-para"
        className="campo mt-1"
        value={p.etapa}
        disabled={ocupado}
        onChange={(e) => void mover(e.target.value as Etapa)}
      >
        {ETAPAS.map((e) => (
          <option key={e.id} value={e.id}>
            {e.rotulo}
          </option>
        ))}
      </select>
      {erro && (
        <p role="alert" className="mt-1 text-sm text-perigo">
          {erro}
        </p>
      )}
    </div>
  );
}

export default function DetalheProcesso({
  id,
  desktop,
  aoFechar,
  aoMudar,
}: {
  id: number;
  desktop: boolean;
  aoFechar: () => void;
  /** Recarrega o quadro. */
  aoMudar: () => Promise<void> | void;
}) {
  const [p, setP] = useState<Processo | null>(null);
  const [erro, setErro] = useState(false);
  const [versao, setVersao] = useState(0);

  const carregar = useCallback(async () => {
    try {
      setP(await processos.obter(id));
      setErro(false);
    } catch {
      setErro(true);
    }
  }, [id]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  /** Depois de qualquer mutação: atualiza o detalhe e o quadro. */
  const atualizar = useCallback(async () => {
    await Promise.all([carregar(), aoMudar()]);
    setVersao((v) => v + 1); // refaz os campos a partir do que o servidor guardou
  }, [carregar, aoMudar]);

  let corpo: React.ReactNode;
  if (!p) {
    corpo = erro ? (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar o processo.</p>
        <Botao onClick={carregar}>Tentar de novo</Botao>
      </div>
    ) : (
      <Carregando />
    );
  } else {
    corpo = (
      <div className="flex flex-col gap-6">
        <Mover p={p} aoMudar={atualizar} />
        {/* A chave remonta os campos depois de cada mutação, para nunca contradizer o servidor. */}
        <Campos
          key={versao}
          p={p}
          aoMudar={atualizar}
        />
        <section aria-labelledby="titulo-historico">
          <h3 id="titulo-historico" className="mb-2 font-semibold">Histórico de etapas</h3>
          <ul className="flex flex-col gap-1 text-sm">
            {[...p.historico].reverse().map((h, i) => (
              <li key={i}>
                {h.de ? `${rotuloEtapa(h.de)} → ` : "Entrou em "}
                <strong>{rotuloEtapa(h.para)}</strong> <span className="suave text-xs">{dataHora(h.em)}</span>
              </li>
            ))}
          </ul>
        </section>
        <SecaoNotas id={p.id} notas={p.notas} aoMudar={atualizar} />
        <SecaoArquivos id={p.id} arquivos={p.arquivos} aoMudar={atualizar} />
        <SecaoLembretes id={p.id} itens={p.lembretes} aoMudar={atualizar} />
        <SecaoContatos id={p.id} contatoIds={p.contato_ids} aoMudar={atualizar} />
      </div>
    );
  }

  return (
    <aside
      aria-label="Detalhe do processo"
      className={
        desktop
          ? "fixed inset-y-0 right-0 z-30 w-[360px] overflow-y-auto border-l border-borda bg-superficie p-4 shadow-lg"
          : "fixed inset-0 z-50 overflow-y-auto bg-fundo p-4 pb-12"
      }
    >
      <div className="mb-4 flex items-center justify-between gap-2">
        {desktop ? (
          <>
            <h2 className="truncate text-lg font-bold">{p?.titulo ?? "Processo"}</h2>
            <Botao variante="secundario" onClick={aoFechar} aria-label="Fechar detalhe">
              ×
            </Botao>
          </>
        ) : (
          <Botao variante="secundario" onClick={aoFechar}>
            ← Voltar
          </Botao>
        )}
      </div>
      {corpo}
    </aside>
  );
}
