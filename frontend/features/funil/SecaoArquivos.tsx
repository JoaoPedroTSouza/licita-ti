"use client";

import { useRef, useState } from "react";
import { ErroApi, processos } from "@/shared/api/cliente";
import type { Arquivo } from "@/shared/api/tipos";
import Botao from "@/shared/ui/Botao";
import { mensagemDe } from "./datas";

function tamanho(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

export default function SecaoArquivos({
  id,
  arquivos,
  aoMudar,
}: {
  id: number;
  arquivos: Arquivo[];
  aoMudar: () => Promise<void>;
}) {
  const entrada = useRef<HTMLInputElement>(null);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(arquivo: File | undefined) {
    if (!arquivo) return;
    setOcupado("envio");
    setErro(null);
    try {
      await processos.anexar(id, arquivo);
      await aoMudar();
    } catch (e) {
      setErro(
        e instanceof ErroApi && e.status === 413
          ? "Arquivo maior que 20 MB"
          : mensagemDe(e, "Não foi possível enviar o arquivo."),
      );
    } finally {
      setOcupado(null);
      if (entrada.current) entrada.current.value = "";
    }
  }

  async function baixar(a: Arquivo) {
    setOcupado(`b${a.id}`);
    setErro(null);
    try {
      const url = URL.createObjectURL(await processos.baixarArquivo(id, a.id));
      const link = document.createElement("a");
      link.href = url;
      link.download = a.nome;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível baixar o arquivo."));
    } finally {
      setOcupado(null);
    }
  }

  return (
    <section aria-labelledby="titulo-arquivos">
      <h3 id="titulo-arquivos" className="mb-2 font-semibold">Arquivos</h3>
      <ul className="mb-2 flex flex-col gap-1">
        {arquivos.map((a) => (
          <li key={a.id} className="flex items-center justify-between gap-2 text-sm">
            <span className="min-w-0 truncate">
              {a.nome} <span className="suave text-xs">({tamanho(a.tamanho)})</span>
            </span>
            <Botao variante="secundario" onClick={() => baixar(a)} disabled={ocupado !== null} aria-label={`Baixar ${a.nome}`}>
              Baixar
            </Botao>
          </li>
        ))}
        {arquivos.length === 0 && <li className="suave text-sm">Sem arquivos.</li>}
      </ul>
      <input
        ref={entrada}
        type="file"
        aria-label="Enviar arquivo"
        disabled={ocupado !== null}
        onChange={(e) => void enviar(e.target.files?.[0])}
        className="w-full text-sm"
      />
      {ocupado === "envio" && (
        <p role="status" className="suave mt-1 text-xs">
          Enviando…
        </p>
      )}
      {erro && (
        <p role="alert" className="mt-2 text-sm text-perigo">
          {erro}
        </p>
      )}
    </section>
  );
}
