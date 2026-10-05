import Link from "next/link";
import { formatarValor, prazoRelativo } from "@/lib/format";
import { STATUS_INFO, type EditalResumo } from "@/lib/types";

export function StatusBadge({ status }: { status: EditalResumo["status"] }) {
  const info = STATUS_INFO[status];
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${info.cor}`}>{info.rotulo}</span>;
}

export function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;
  const cor =
    score >= 75 ? "bg-emerald-600 text-white" : score >= 50 ? "bg-amber-500 text-white" : "bg-zinc-400 text-white";
  return (
    <span className={`rounded-md px-1.5 py-0.5 text-[11px] font-bold tabular-nums ${cor}`} title="Aderência estimada pela IA">
      {score}
    </span>
  );
}

export default function EditalCard({ e }: { e: EditalResumo }) {
  const prazo = prazoRelativo(e.data_encerramento);
  return (
    <Link href={`/editais/${e.id}`} className="cartao block p-4 active:scale-[0.99] transition-transform">
      <div className="mb-2 flex items-center gap-2 text-xs">
        <ScoreBadge score={e.ia_score} />
        <span className="font-semibold">{e.uf ?? "—"}</span>
        <span className="suave truncate">{e.modalidade_nome}</span>
        <span className="flex-1" />
        {e.favorito && <span aria-label="Favorito">★</span>}
        {e.status !== "novo" && <StatusBadge status={e.status} />}
      </div>
      <p className="line-clamp-3 text-[15px] leading-snug font-medium">{e.objeto}</p>
      <p className="suave mt-1.5 truncate text-xs">
        {e.orgao}
        {e.municipio ? ` · ${e.municipio}` : ""}
      </p>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="font-semibold tabular-nums">{formatarValor(e.valor_estimado)}</span>
        <span
          className={`text-xs font-medium ${prazo.encerrado ? "suave line-through" : prazo.urgente ? "text-red-600 dark:text-red-400" : "suave"}`}
        >
          {prazo.texto}
        </span>
      </div>
    </Link>
  );
}
