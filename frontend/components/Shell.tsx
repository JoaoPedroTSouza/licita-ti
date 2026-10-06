"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, setToken } from "@/lib/api";

type Item = { href: string; rotulo: string; icone: (p: { ativo: boolean }) => React.ReactElement; tom: "azul" | "roxo" };

const MONITORAMENTO: Item[] = [
  { href: "/", rotulo: "Painel", icone: IconePainel, tom: "azul" },
  { href: "/editais", rotulo: "Editais", icone: IconeLista, tom: "azul" },
  { href: "/acompanhamento", rotulo: "Acompanhamento", icone: IconeQuadro, tom: "azul" },
];
const WORKSPACE: Item[] = [{ href: "/ideias", rotulo: "Ideias", icone: IconeIdeia, tom: "roxo" }];
const AJUSTES: Item = { href: "/ajustes", rotulo: "Ajustes", icone: IconeAjustes, tom: "azul" };

const MOBILE: Item[] = [
  MONITORAMENTO[0],
  MONITORAMENTO[1],
  { ...MONITORAMENTO[2], rotulo: "Funil" },
  WORKSPACE[0],
  AJUSTES,
];

function estaAtivo(href: string, pathname: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * Moldura das telas logadas.
 * Desktop (≥1024px): menu lateral de 240px + conteúdo até 1440px no total.
 * Celular: cabeçalho fixo + barra de navegação inferior.
 */
export default function Shell({
  titulo,
  subtitulo,
  voltar,
  acao,
  children,
}: {
  titulo: string;
  subtitulo?: React.ReactNode;
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
    <div className="mx-auto min-h-dvh max-w-[1440px] lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
      {/* ---------- Menu lateral (desktop) ---------- */}
      <aside className="sticky top-0 hidden h-dvh flex-col border-r borda px-4 py-6 lg:flex">
        <Link href="/" className="mb-8 flex items-center gap-2.5 px-2">
          <img src="/icons/icon-192.png" alt="" width={32} height={32} className="rounded-lg" />
          <span className="text-[17px] font-bold tracking-tight">Licita TI</span>
        </Link>

        <GrupoNav titulo="Monitoramento" itens={MONITORAMENTO} pathname={pathname} />
        <GrupoNav titulo="Workspace" itens={WORKSPACE} pathname={pathname} />

        <div className="mt-auto space-y-1">
          <ItemNav item={AJUSTES} ativo={estaAtivo(AJUSTES.href, pathname)} />
          <button
            onClick={() => {
              setToken(null);
              router.replace("/login");
            }}
            className="suave w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-superficie-2"
          >
            Sair
          </button>
        </div>
      </aside>

      {/* ---------- Conteúdo ---------- */}
      <div className="min-w-0 pb-nav">
        <header
          className="sticky top-0 z-20 border-b borda backdrop-blur lg:static lg:border-0 lg:backdrop-blur-none"
          style={{ background: "color-mix(in srgb, var(--fundo) 90%, transparent)", paddingTop: "env(safe-area-inset-top)" }}
        >
          <div className="flex items-center gap-3 px-4 py-3 lg:px-10 lg:pb-2 lg:pt-8">
            {voltar && (
              <button
                onClick={() => router.back()}
                aria-label="Voltar"
                className="-ml-2 rounded-full p-2 hover:bg-superficie-2"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
              </button>
            )}
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-lg font-bold tracking-tight lg:text-[26px] lg:leading-tight">{titulo}</h1>
              {subtitulo && <p className="suave mt-0.5 hidden text-sm lg:block">{subtitulo}</p>}
            </div>
            {acao}
          </div>
        </header>

        <main className="px-4 pt-4 lg:px-10 lg:pt-4">{children}</main>
      </div>

      {/* ---------- Barra inferior (celular/tablet) ---------- */}
      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t borda bg-superficie lg:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="mx-auto grid max-w-2xl grid-cols-5">
          {MOBILE.map((item) => {
            const ativo = estaAtivo(item.href, pathname);
            const Icone = item.icone;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium ${
                  ativo ? (item.tom === "roxo" ? "text-roxo-texto" : "text-azul-texto") : "suave"
                }`}
              >
                <Icone ativo={ativo} />
                {item.rotulo}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

function GrupoNav({ titulo, itens, pathname }: { titulo: string; itens: Item[]; pathname: string }) {
  return (
    <div className="mb-6">
      <p className="suave mb-1.5 px-3 text-xs font-medium">{titulo}</p>
      <div className="space-y-0.5">
        {itens.map((item) => (
          <ItemNav key={item.href} item={item} ativo={estaAtivo(item.href, pathname)} />
        ))}
      </div>
    </div>
  );
}

function ItemNav({ item, ativo }: { item: Item; ativo: boolean }) {
  const Icone = item.icone;
  const cores = ativo
    ? item.tom === "roxo"
      ? "bg-roxo-suave text-roxo-texto"
      : "bg-azul-suave text-azul-texto"
    : "hover:bg-superficie-2";
  return (
    <Link href={item.href} className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium ${cores}`}>
      <Icone ativo={ativo} />
      {item.rotulo}
    </Link>
  );
}

const traco = (ativo: boolean) => (ativo ? 2.2 : 1.7);

function IconePainel({ ativo }: { ativo: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={traco(ativo)} strokeLinecap="round">
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
    </svg>
  );
}
function IconeLista({ ativo }: { ativo: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={traco(ativo)} strokeLinecap="round">
      <path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01" />
    </svg>
  );
}
function IconeQuadro({ ativo }: { ativo: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={traco(ativo)} strokeLinejoin="round">
      <rect x="3" y="4" width="5" height="16" rx="1.5" /><rect x="10" y="4" width="5" height="10" rx="1.5" /><rect x="17" y="4" width="4" height="13" rx="1.5" />
    </svg>
  );
}
function IconeIdeia({ ativo }: { ativo: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={traco(ativo)} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z" />
    </svg>
  );
}
function IconeAjustes({ ativo }: { ativo: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={traco(ativo)} strokeLinecap="round">
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" />
    </svg>
  );
}
