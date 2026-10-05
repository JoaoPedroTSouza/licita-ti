"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

/** Banner "Instalar app" usando o prompt nativo do Chrome no Android. */
export default function InstalarApp() {
  const [evento, setEvento] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const capturar = (e: Event) => {
      e.preventDefault();
      setEvento(e as BeforeInstallPromptEvent);
    };
    const instalado = () => setEvento(null);
    window.addEventListener("beforeinstallprompt", capturar);
    window.addEventListener("appinstalled", instalado);
    return () => {
      window.removeEventListener("beforeinstallprompt", capturar);
      window.removeEventListener("appinstalled", instalado);
    };
  }, []);

  if (!evento) return null;

  return (
    <div className="cartao mb-4 flex items-center gap-3 p-3">
      <img src="/icons/icon-192.png" alt="" width={40} height={40} className="rounded-xl" />
      <div className="flex-1 text-sm">
        <p className="font-semibold">Instale o Licita TI</p>
        <p className="suave text-xs">Abre em tela cheia e recebe alertas de editais.</p>
      </div>
      <button
        className="botao px-3 py-2 text-sm"
        onClick={async () => {
          await evento.prompt();
          await evento.userChoice;
          setEvento(null);
        }}
      >
        Instalar
      </button>
    </div>
  );
}
