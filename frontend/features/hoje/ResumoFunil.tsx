import type { ResumoFunil as Resumo } from "@/shared/api/tipos";
import { formatarAproxBrl } from "@/shared/formato";
import Cartao from "@/shared/ui/Cartao";

const EXIBIDAS = [
  { id: "analisando", rotulo: "Analisando" },
  { id: "proposta_enviada", rotulo: "Proposta" },
  { id: "negociacao", rotulo: "Negociação" },
  { id: "fechado", rotulo: "Fechado" },
] as const;

export default function ResumoFunil({ funil }: { funil: Resumo }) {
  return (
    <section aria-labelledby="titulo-funil">
      <h2 id="titulo-funil" className="mb-3 text-lg font-semibold">Funil</h2>
      <Cartao className="p-4">
        <div className="grid grid-cols-2 gap-3">
          {EXIBIDAS.map((e) => (
            <div key={e.id}>
              <p className="text-2xl font-bold tabular-nums">{funil.contagem[e.id] ?? 0}</p>
              <p className="suave text-sm">{e.rotulo}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 border-t border-borda pt-3 text-sm">
          <span className="suave">Em aberto: </span>
          <span className="font-semibold">{formatarAproxBrl(funil.valor_aberto_brl) || "≈ R$ 0"}</span>
          {funil.sem_conversao > 0 && (
            <span className="suave"> (+{funil.sem_conversao} sem conversão)</span>
          )}
        </p>
      </Cartao>
    </section>
  );
}
