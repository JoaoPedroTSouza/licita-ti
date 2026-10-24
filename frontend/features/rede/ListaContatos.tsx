"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { contatos, processos } from "@/shared/api/cliente";
import type { Contato } from "@/shared/api/tipos";
import { formatarUltimoContato } from "@/shared/formato";
import Botao from "@/shared/ui/Botao";
import Carregando from "@/shared/ui/Carregando";
import Etiqueta from "@/shared/ui/Etiqueta";
import Vazio from "@/shared/ui/Vazio";
import { mensagemDe } from "@/features/funil/datas";
import FormContato from "./FormContato";

type Edicao = { contato?: Contato } | null;

export default function ListaContatos() {
  const [itens, setItens] = useState<Contato[] | null>(null);
  const [titulos, setTitulos] = useState<Map<number, string>>(new Map());
  const [erro, setErro] = useState(false);
  const [form, setForm] = useState<Edicao>(null);
  const [ocupadoId, setOcupadoId] = useState<number | null>(null);
  const [erroAcao, setErroAcao] = useState<{ id: number; texto: string } | null>(null);

  const carregar = useCallback(async () => {
    try {
      setItens(await contatos.listar());
      setErro(false);
    } catch {
      setErro(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
    // Os títulos só enfeitam os links: se falhar, mostramos "Processo N".
    processos
      .listar()
      .then((l) => setTitulos(new Map(l.map((p) => [p.id, p.titulo]))))
      .catch(() => {});
  }, [carregar]);

  async function falouHoje(c: Contato) {
    setOcupadoId(c.id);
    setErroAcao(null);
    try {
      await contatos.registrarContato(c.id);
      await carregar();
    } catch (e) {
      setErroAcao({ id: c.id, texto: mensagemDe(e, "Não foi possível registrar o contato.") });
    } finally {
      setOcupadoId(null);
    }
  }

  if (!itens) {
    return erro ? (
      <div role="alert" className="py-10 text-center">
        <p className="mb-3 text-sm">Não foi possível carregar a rede.</p>
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
        <h1 className="text-2xl font-bold tracking-tight">Rede</h1>
        <Botao onClick={() => setForm({})}>Novo contato</Botao>
      </div>
      {erro && (
        <p role="alert" className="mb-3 text-sm text-perigo">
          Não foi possível atualizar a lista.
        </p>
      )}
      {itens.length === 0 ? (
        <Vazio titulo="Nenhum contato ainda">Guarde aqui quem pode indicar ou contratar você.</Vazio>
      ) : (
        <ul className="flex flex-col gap-3">
          {itens.map((c) => (
            <li key={c.id} className="cartao p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-semibold">
                    {c.nome}
                    {c.atrasado && <Etiqueta tom="aviso">Atrasado</Etiqueta>}
                  </p>
                  {c.organizacao && <p className="suave text-sm">{c.organizacao}</p>}
                  <p className="suave mt-1 text-sm">
                    Último contato: {formatarUltimoContato(c.ultimo_contato, agora)}
                    {c.frequencia_dias !== null && ` · a cada ${c.frequencia_dias} dias`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Botao disabled={ocupadoId === c.id} onClick={() => falouHoje(c)}>
                    Falei hoje
                  </Botao>
                  <Botao variante="secundario" onClick={() => setForm({ contato: c })}>
                    Editar
                  </Botao>
                </div>
              </div>
              {c.processo_ids.length > 0 && (
                <p className="mt-2 text-sm">
                  <span className="suave">Processos: </span>
                  {c.processo_ids.map((pid, i) => (
                    <span key={pid}>
                      {i > 0 && ", "}
                      <Link href={`/funil?processo=${pid}`} className="underline">
                        {titulos.get(pid) ?? `Processo ${pid}`}
                      </Link>
                    </span>
                  ))}
                </p>
              )}
              {erroAcao?.id === c.id && (
                <p role="alert" className="mt-2 text-sm text-perigo">
                  {erroAcao.texto}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
      {form && (
        <FormContato
          key={form.contato?.id ?? "novo"}
          contato={form.contato}
          aoCancelar={() => setForm(null)}
          aoSalvar={() => {
            setForm(null);
            void carregar();
          }}
        />
      )}
    </div>
  );
}
