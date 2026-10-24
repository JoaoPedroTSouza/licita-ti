import Link from "next/link";
import type { Oportunidade } from "@/shared/api/tipos";
import { formatarPrazo } from "@/shared/formato";
import Cartao from "@/shared/ui/Cartao";
import Etiqueta from "@/shared/ui/Etiqueta";
import NotaBadge from "@/shared/ui/NotaBadge";
import Vazio from "@/shared/ui/Vazio";

export default function MelhoresNovas({ itens, agora }: { itens: Oportunidade[]; agora: Date }) {
  return (
    <section aria-labelledby="titulo-novas">
      <h2 id="titulo-novas" className="mb-3 text-lg font-semibold">Melhores novas</h2>
      {itens.length === 0 ? (
        <Vazio titulo="Nenhuma oportunidade nova." />
      ) : (
        <Cartao className="divide-y divide-borda">
          {itens.map((o) => (
            <Link
              key={o.id}
              href={`/entrada/${o.id}`}
              className="flex items-center gap-3 px-4 py-3 hover:bg-superficie-2"
            >
              <NotaBadge nota={o.nota} />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{o.titulo}</p>
                <p className="suave truncate text-sm">{o.organizacao}</p>
              </div>
              {o.pessoa_fisica && <span className="shrink-0"><Etiqueta tom="aviso">Pessoa física</Etiqueta></span>}
              {o.prazo && <span className="suave shrink-0 text-sm">{formatarPrazo(o.prazo, agora)}</span>}
            </Link>
          ))}
        </Cartao>
      )}
    </section>
  );
}
