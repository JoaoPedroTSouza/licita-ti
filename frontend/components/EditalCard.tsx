import Link from "next/link";
import { formatarValor, prazoRelativo } from "@/lib/format";
import { STATUS_INFO, type EditalResumo } from "@/lib/types";

export function StatusBadge({ status }: { status: EditalResumo["status"] }) {
  const info = STATUS_INFO[status];
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${info.cor}`}>{info.rotulo}</span>;
}

/** Nota da IA (roxo = análise da IA). A força da nota aparece no preenchimento. */
export function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;
  const forte = score >= 75;
  return (
    <span
      className={`tabular rounded-md px-1.5 py-0.5 text-[11px] font-bold ${
        forte ? "bg-acao-roxo text-white" : "bg-roxo-suave text-roxo-texto"
      }`}
      title={`Aderência estimada pela IA: ${score} de 100`}
    >
      IA {score}
    </span>
  );
}

export function Prazo({ iso, className = "" }: { iso: string | null; className?: string }) {
  const p = prazoRelativo(iso);
  return (
    <span
      className={`text-xs font-medium ${
        p.encerrado ? "suave line-through" : p.urgente ? "rounded-full bg-vermelho-suave px-2 py-0.5 text-vermelho-texto" : "suave"
      } ${className}`}
    >
      {p.texto}
    </span>
  );
}

export default function EditalCard({ e }: { e: EditalResumo }) {
  return (
    <Link
      href={`/editais/${e.id}`}
      className="cartao flex flex-col p-4 transition-colors hover:border-azul/40 lg:p-5"
    >
      <div className="mb-2 flex items-center gap-2 text-xs">
        <ScoreBadge score={e.ia_score} />
        <span className="font-semibold">{e.uf ?? "—"}</span>
        <span className="suave truncate">{e.modalidade_nome}</span>
        <span className="flex-1" />
        {e.favorito && <span aria-label="Favorito" className="text-roxo">★</span>}
        {e.status !== "novo" && <StatusBadge status={e.status} />}
      </div>
      <p className="line-clamp-3 text-[15px] font-medium leading-snug">{e.objeto}</p>
      <p className="suave mt-1.5 truncate text-xs">
        {e.orgao}
        {e.municipio ? `, ${e.municipio}` : ""}
      </p>
      <div className="mt-auto flex items-center justify-between pt-3 text-sm">
        <span className="tabular font-semibold">{formatarValor(e.valor_estimado)}</span>
        <Prazo iso={e.data_encerramento} />
      </div>
    </Link>
  );
}
