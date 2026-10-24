"use client";

import { useCallback, useEffect, useState } from "react";
import { status } from "@/shared/api/cliente";
import type { Status } from "@/shared/api/tipos";
import AtivarNotificacoes from "@/features/ajustes/AtivarNotificacoes";
import FormAjustes from "@/features/ajustes/FormAjustes";
import FormPerfil from "@/features/ajustes/FormPerfil";
import StatusFontes from "@/features/ajustes/StatusFontes";
import Botao from "@/shared/ui/Botao";
import Cartao from "@/shared/ui/Cartao";
import Carregando from "@/shared/ui/Carregando";

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <Cartao className="p-4">
      <h2 className="mb-3 text-base font-semibold">{titulo}</h2>
      {children}
    </Cartao>
  );
}

export default function Pagina() {
  const [estado, setEstado] = useState<Status | null>(null);
  const [erro, setErro] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setEstado(await status.obter());
      setErro(false);
    } catch {
      setErro(true);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight">Ajustes</h1>

      {estado && !estado.ia_configurada && (
        <p role="alert" className="rounded-lg bg-aviso-suave p-3 text-sm text-aviso-texto">
          A IA não está configurada: defina ANTHROPIC_API_KEY no .env. Sem ela, nenhuma oportunidade é avaliada nem
          aparece na Entrada.
        </p>
      )}
      {estado && estado.ia_configurada && estado.pendentes_classificacao > 0 && (
        <p role="status" className="rounded-lg bg-aviso-suave p-3 text-sm text-aviso-texto">
          {estado.pendentes_classificacao === 1
            ? "1 oportunidade aguardando avaliação da IA."
            : `${estado.pendentes_classificacao} oportunidades aguardando avaliação da IA.`}
        </p>
      )}
      {estado && !estado.push_configurado && (
        <p role="alert" className="rounded-lg bg-aviso-suave p-3 text-sm text-aviso-texto">
          As notificações não estão configuradas: gere as chaves com <code>python -m radar.interfaces.gen_vapid</code> e
          preencha VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY no .env.
        </p>
      )}

      <Secao titulo="Perfil">
        <FormPerfil />
      </Secao>
      <Secao titulo="Alertas e resumo">
        <FormAjustes />
      </Secao>
      <Secao titulo="Notificações">
        <AtivarNotificacoes configurado={estado?.push_configurado ?? false} />
      </Secao>
      <Secao titulo="Fontes">
        {estado ? (
          <StatusFontes fontes={estado.fontes} />
        ) : erro ? (
          <div role="alert" className="py-4 text-center">
            <p className="mb-3 text-sm">Não foi possível carregar o status das fontes.</p>
            <Botao onClick={carregar}>Tentar de novo</Botao>
          </div>
        ) : (
          <Carregando />
        )}
      </Secao>
    </div>
  );
}
