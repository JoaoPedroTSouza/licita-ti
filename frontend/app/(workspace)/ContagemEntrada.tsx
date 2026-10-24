"use client";

import { createContext, useContext } from "react";

export interface ContagemEntrada {
  contagem: number;
  /** Rebusca a contagem de novas (chame depois de triar uma oportunidade). */
  atualizar: () => Promise<void>;
}

export const ContagemEntradaContext = createContext<ContagemEntrada>({
  contagem: 0,
  atualizar: async () => {},
});

export const useContagemEntrada = () => useContext(ContagemEntradaContext);
