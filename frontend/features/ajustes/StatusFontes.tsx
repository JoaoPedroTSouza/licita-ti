import type { ExecucaoFonte } from "@/shared/api/tipos";
import Etiqueta from "@/shared/ui/Etiqueta";
import { dataHora } from "@/features/funil/datas";

const NOMES: Record<string, string> = {
  ungm: "UNGM (ONU)",
  opas: "OPAS Brasil",
  banco_mundial: "Banco Mundial",
};

const nomeDaFonte = (fonte: string) => NOMES[fonte] ?? fonte;

/** Última execução de cada fonte: quando rodou, quantas oportunidades recebeu e o erro, se houve. */
export default function StatusFontes({ fontes }: { fontes: ExecucaoFonte[] }) {
  const porNome = new Map(fontes.map((f) => [f.fonte, f]));
  const nomes = [...Object.keys(NOMES), ...fontes.map((f) => f.fonte).filter((f) => !(f in NOMES))];

  return (
    <div>
      <ul className="divide-y divide-borda">
        {nomes.map((nome) => {
          const f = porNome.get(nome);
          return (
            <li key={nome} className="py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-medium">{nomeDaFonte(nome)}</span>
                <span className="suave text-xs">{f ? dataHora(f.finalizada_em) : "ainda não executada"}</span>
              </div>
              {f && (
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <Etiqueta>{f.recebidas} recebidas</Etiqueta>
                  <Etiqueta tom="acento">{f.novas} novas</Etiqueta>
                </div>
              )}
              {f?.erro && (
                <p role="alert" className="mt-1 text-sm text-perigo">
                  {f.erro}
                </p>
              )}
            </li>
          );
        })}
      </ul>
      <p className="suave mt-3 text-xs">
        ReliefWeb está desativada: a API exige um appname aprovado (veja docs/fontes/reliefweb.md).
      </p>
    </div>
  );
}
