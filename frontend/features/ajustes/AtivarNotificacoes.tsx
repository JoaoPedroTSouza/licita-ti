"use client";

import { useEffect, useState } from "react";
import { push } from "@/shared/api/cliente";
import { ativarPush, inscricaoAtual, pushSuportado } from "@/shared/pwa/push";
import Botao from "@/shared/ui/Botao";
import { mensagemDe } from "@/features/funil/datas";

/** Ativa o push neste aparelho e envia uma notificação de teste. */
export default function AtivarNotificacoes({ configurado }: { configurado: boolean }) {
  const [suportado, setSuportado] = useState(true);
  const [ativo, setAtivo] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  useEffect(() => {
    setSuportado(pushSuportado());
    inscricaoAtual()
      .then((s) => setAtivo(!!s))
      .catch(() => {});
  }, []);

  async function ativar() {
    setOcupado(true);
    setErro(null);
    setAviso(null);
    try {
      await ativarPush();
      setAtivo(true);
      setAviso("Notificações ativadas neste aparelho.");
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível ativar as notificações."));
    } finally {
      setOcupado(false);
    }
  }

  async function testar() {
    setOcupado(true);
    setErro(null);
    setAviso(null);
    try {
      const { entregues } = await push.testar();
      setAviso(
        entregues > 0
          ? `Teste enviado para ${entregues} ${entregues === 1 ? "aparelho" : "aparelhos"}.`
          : "Nenhum aparelho recebeu o teste. Ative as notificações neste aparelho primeiro.",
      );
    } catch (e) {
      setErro(mensagemDe(e, "Não foi possível enviar o teste."));
    } finally {
      setOcupado(false);
    }
  }

  if (!suportado) {
    return <p className="suave text-sm">Este navegador não suporta notificações push.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm">
        {ativo ? "As notificações estão ativas neste aparelho." : "As notificações ainda não estão ativas neste aparelho."}
      </p>
      <div className="flex flex-wrap gap-2">
        {!ativo && (
          <Botao onClick={ativar} disabled={ocupado || !configurado}>
            Ativar neste aparelho
          </Botao>
        )}
        <Botao variante="secundario" onClick={testar} disabled={ocupado || !configurado}>
          Enviar notificação de teste
        </Botao>
      </div>
      {erro && (
        <p role="alert" className="text-sm text-perigo">
          {erro}
        </p>
      )}
      {aviso && (
        <p role="status" className="text-sm text-acento-texto">
          {aviso}
        </p>
      )}
    </div>
  );
}
