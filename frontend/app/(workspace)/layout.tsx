"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getToken, oportunidades } from "@/shared/api/cliente";
import { ContagemEntradaContext } from "./ContagemEntrada";
import Navegacao from "./Navegacao";

/** Casca das telas logadas: exige token e mostra a navegação. */
export default function LayoutWorkspace({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [pronto, setPronto] = useState(false);
  const [novas, setNovas] = useState(0);
  const atualizar = useCallback(
    () => oportunidades.listar().then((l) => setNovas(l.length)).catch(() => {}),
    [],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setPronto(true);
    void atualizar();
  }, [router, atualizar]);

  const valor = useMemo(() => ({ contagem: novas, atualizar }), [novas, atualizar]);

  if (!pronto) return null;

  return (
    <ContagemEntradaContext.Provider value={valor}>
    <div className="mx-auto min-h-dvh max-w-[1280px] lg:grid lg:grid-cols-[220px_minmax(0,1fr)]">
      <Navegacao />
      <main className="pb-nav min-w-0 px-4 pt-4 lg:px-10 lg:pt-8">{children}</main>
    </div>
    </ContagemEntradaContext.Provider>
  );
}
