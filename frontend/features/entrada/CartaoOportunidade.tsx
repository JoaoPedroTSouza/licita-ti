import Link from "next/link";
import type { Oportunidade } from "@/shared/api/tipos";
import { formatarAproxBrl, formatarDinheiro, formatarPrazo } from "@/shared/formato";
import Cartao from "@/shared/ui/Cartao";
import Etiqueta from "@/shared/ui/Etiqueta";
import NotaBadge from "@/shared/ui/NotaBadge";
import AcoesOportunidade from "./AcoesOportunidade";

/** Linha de resumo compartilhada com o detalhe: organização, prazo e valores. */
export function Metadados({ o, agora }: { o: Oportunidade; agora: Date }) {
  return (
    <p className="suave text-sm">
      {[o.organizacao, o.pais].filter(Boolean).join(" · ")}
      {o.prazo && ` — prazo: ${formatarPrazo(o.prazo, agora)}`}
      {o.valor && ` — ${formatarDinheiro(o.valor)} ${formatarAproxBrl(o.valor_brl)}`}
    </p>
  );
}

export default function CartaoOportunidade({
  o,
  agora,
  aoInteressar,
  aoDescartar,
}: {
  o: Oportunidade;
  agora: Date;
  aoInteressar: (processoId: number) => void;
  aoDescartar: () => void;
}) {
  return (
    <Cartao className="p-4">
      <div className="flex items-start gap-3">
        <NotaBadge nota={o.nota} />
        <div className="min-w-0 flex-1">
          <Link href={`/entrada/${o.id}`} className="font-semibold hover:underline">{o.titulo}</Link>
          <Metadados o={o} agora={agora} />
        </div>
        {o.pessoa_fisica && <span className="shrink-0"><Etiqueta tom="aviso">Pessoa física</Etiqueta></span>}
      </div>
      {o.resumo && <p className="mt-2 line-clamp-3 text-sm">{o.resumo}</p>}
      <div className="mt-3">
        <AcoesOportunidade id={o.id} aoInteressar={aoInteressar} aoDescartar={aoDescartar} />
      </div>
    </Cartao>
  );
}
