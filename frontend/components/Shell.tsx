"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken } from "@/lib/api";

const ABAS = [
  { href: "/", rotulo: "Editais", icone: IconeLista },
  { href: "/acompanhamento", rotulo: "Acompanhar", icone: IconeQuadro },
  { href: "/ajustes", rotulo: "Ajustes", icone: IconeAjustes },
];

/** Moldura das telas logadas: verifica a sessão, título no topo e navegação inferior. */
export default function Shell({
  titulo,
  voltar,
  acao,
  children,
}: {
  titulo: string;
  voltar?: boolean;
  acao?: React.ReactNode;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
    else setPronto(true);
  }, [router]);

  if (!pronto) return null;

  return (
    <div className="mx-auto min-h-dvh max-w-xl pb-nav">
      <header
        className="sticky top-0 z-20 flex items-center gap-2 border-b borda px-4 py-3 backdrop-blur"
        style={{ background: "color-mix(in srgb, var(--fundo) 88%, transparent)", paddingTop: "calc(0.75rem + env(safe-area-inset-top))" }}
      >
        {voltar && (
          <button onClick={() => router.back()} aria-label="Voltar" className="-ml-2 rounded-full p-2 active:bg-black/5">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
          </button>
        )}
        <h1 className="flex-1 truncate text-lg font-bold tracking-tight">{titulo}</h1>
        {acao}
      </header>

      <main className="px-4 pt-4">{children}</main>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t borda"
        style={{ background: "var(--superficie)", paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="mx-auto grid max-w-xl grid-cols-3">
          {ABAS.map(({ href, rotulo, icone: Icone }) => {
            const ativo = href === "/" ? pathname === "/" || pathname.startsWith("/editais") : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-xs font-medium ${ativo ? "text-marca" : "suave"}`}
              >
                <Icone ativo={ativo} />
                {rotulo}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

function IconeLista({ ativo }: { ativo: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={ativo ? 2.4 : 1.8} strokeLinecap="round">
      <path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01" />
    </svg>
  );
}
function IconeQuadro({ ativo }: { ativo: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={ativo ? 2.4 : 1.8} strokeLinejoin="round">
      <rect x="3" y="4" width="5" height="16" rx="1.5" /><rect x="10" y="4" width="5" height="10" rx="1.5" /><rect x="17" y="4" width="4" height="13" rx="1.5" />
    </svg>
  );
}
function IconeAjustes({ ativo }: { ativo: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={ativo ? 2.4 : 1.8} strokeLinecap="round">
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" />
    </svg>
  );
}
