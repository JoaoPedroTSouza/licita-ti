"use client";

import Link from "next/link";
import { useState } from "react";
import { contatos, lembretes } from "@/shared/api/cliente";
import type { ItemParaFazer } from "@/shared/api/tipos";
import { formatarPrazo } from "@/shared/formato";
import Botao from "@/shared/ui/Botao";
import Cartao from "@/shared/ui/Cartao";
import Vazio from "@/shared/ui/Vazio";

/** `quando` pode vir como data pura (AAAA-MM-DD): vale até o fim do dia em Brasília. */
function rotuloQuando(quando: string | null, agora: Date): string {
  if (!quando) return "";
  const iso = quando.length === 10 ? `${quando}T23:59:59-03:00` : quando;
  return formatarPrazo(iso, agora);
}

const urgente = (rotulo: string) => rotulo === "vencido" || rotulo.startsWith("hoje");

export default function ListaParaFazer({
  itens,
  agora,
  aoAgir,
}: {
  itens: ItemParaFazer[];
  agora: Date;
  aoAgir: () => void;
}) {
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function agir(chave: string, acao: () => Promise<unknown>) {
    setOcupado(chave);
    setErro(null);
    try {
      await acao();
      aoAgir();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível concluir.");
    } finally {
      setOcupado(null);
    }
  }

  return (
    <section aria-labelledby="titulo-para-fazer">
      <h2 id="titulo-para-fazer" className="mb-3 text-lg font-semibold">Para fazer</h2>
      {erro && <p role="alert" className="mb-2 text-sm text-perigo">{erro}</p>}
      {itens.length === 0 ? (
        <Vazio titulo="Nada para hoje." />
      ) : (
        <Cartao className="divide-y divide-borda">
          {itens.map((item) => {
            const chave = `${item.tipo}-${item.ref_id}`;
            const rotulo = rotuloQuando(item.quando, agora);
            return (
              <div key={chave} className="flex items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  {item.tipo === "prazo" && item.processo_id !== null ? (
                    <Link href={`/funil?processo=${item.processo_id}`} className="font-medium hover:underline">
                      {item.titulo}
                    </Link>
                  ) : (
                    <p className="font-medium">{item.titulo}</p>
                  )}
                  {rotulo && (
                    <p className={`text-sm ${urgente(rotulo) ? "font-semibold text-aviso-texto" : "suave"}`}>
                      {rotulo}
                    </p>
                  )}
                </div>
                {item.tipo === "lembrete" && (
                  <Botao
                    variante="secundario"
                    disabled={ocupado === chave}
                    onClick={() => agir(chave, () => lembretes.concluir(item.ref_id))}
                  >
                    Concluir
                  </Botao>
                )}
                {item.tipo === "contato" && (
                  <Botao
                    variante="secundario"
                    disabled={ocupado === chave}
                    onClick={() => agir(chave, () => contatos.registrarContato(item.ref_id))}
                  >
                    Falei hoje
                  </Botao>
                )}
              </div>
            );
          })}
        </Cartao>
      )}
    </section>
  );
}
