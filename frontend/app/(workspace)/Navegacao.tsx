"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { setToken } from "@/shared/api/cliente";

type Item = { href: string; rotulo: string; icone: (p: { ativo: boolean }) => React.ReactElement };

const ITENS: Item[] = [
  { href: "/hoje", rotulo: "Hoje", icone: IconeHoje },
  { href: "/entrada", rotulo: "Entrada", icone: IconeEntrada },
  { href: "/funil", rotulo: "Funil", icone: IconeFunil },
  { href: "/rede", rotulo: "Rede", icone: IconeRede },
];
const AJUSTES: Item = { href: "/ajustes", rotulo: "Ajustes", icone: IconeAjustes };

const estaAtivo = (href: string, pathname: string) => pathname === href || pathname.startsWith(`${href}/`);

/**
 * Desktop (>= 1024px): menu lateral com Ajustes no rodapé.
 * Abaixo disso: barra superior com Ajustes e barra inferior com os quatro itens.
 */
export default function Navegacao({ novas }: { novas: number }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <>
      <aside className="sticky top-0 hidden h-dvh flex-col border-r borda px-3 py-6 lg:flex">
        <Link href="/hoje" className="mb-8 flex items-center gap-2.5 px-3">
          <img src="/icons/icon-192.png" alt="" width={28} height={28} className="rounded-md" />
          <span className="text-[17px] font-bold tracking-tight">Radar</span>
        </Link>
        <nav className="space-y-0.5">
          {ITENS.map((item) => (
            <ItemLateral key={item.href} item={item} pathname={pathname} novas={novas} />
          ))}
        </nav>
        <div className="mt-auto space-y-0.5">
          <ItemLateral item={AJUSTES} pathname={pathname} novas={0} />
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

      <header
        className="sticky top-0 z-20 flex items-center justify-between border-b borda bg-fundo px-4 py-2.5 lg:hidden"
        style={{ paddingTop: "calc(0.625rem + env(safe-area-inset-top))" }}
      >
        <span className="text-base font-bold tracking-tight">Radar</span>
        <Link
          href={AJUSTES.href}
          aria-label="Ajustes"
          className={`rounded-full p-2 ${estaAtivo(AJUSTES.href, pathname) ? "text-acento-texto" : "suave"}`}
        >
          <IconeAjustes ativo={estaAtivo(AJUSTES.href, pathname)} />
        </Link>
      </header>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t borda bg-superficie lg:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="mx-auto grid max-w-2xl grid-cols-4">
          {ITENS.map((item) => {
            const ativo = estaAtivo(item.href, pathname);
            const Icone = item.icone;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium ${
                  ativo ? "text-acento-texto" : "suave"
                }`}
              >
                <Icone ativo={ativo} />
                {item.rotulo}
                {item.href === "/entrada" && novas > 0 && <Contagem n={novas} flutuante />}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}

function ItemLateral({ item, pathname, novas }: { item: Item; pathname: string; novas: number }) {
  const ativo = estaAtivo(item.href, pathname);
  const Icone = item.icone;
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium ${
        ativo ? "bg-acento-suave text-acento-texto" : "hover:bg-superficie-2"
      }`}
    >
      <Icone ativo={ativo} />
      <span className="flex-1">{item.rotulo}</span>
      {item.href === "/entrada" && novas > 0 && <Contagem n={novas} />}
    </Link>
  );
}

function Contagem({ n, flutuante = false }: { n: number; flutuante?: boolean }) {
  return (
    <span
      aria-label={`${n} novas`}
      className={`tabular rounded-full bg-acento px-1.5 text-[11px] font-semibold leading-[18px] text-white ${
        flutuante ? "absolute right-[22%] top-1.5" : ""
      }`}
    >
      {n}
    </span>
  );
}

const traco = (ativo: boolean) => (ativo ? 2.2 : 1.7);
const base = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeLinecap: "round", strokeLinejoin: "round" } as const;

function IconeHoje({ ativo }: { ativo: boolean }) {
  return (
    <svg {...base} strokeWidth={traco(ativo)}>
      <rect x="3.5" y="5" width="17" height="15" rx="2" /><path d="M3.5 10h17M8 3v4M16 3v4" />
    </svg>
  );
}
function IconeEntrada({ ativo }: { ativo: boolean }) {
  return (
    <svg {...base} strokeWidth={traco(ativo)}>
      <path d="M3.5 13l2.5-7h12l2.5 7v5.5h-17zM3.5 13h5l1 2.5h5l1-2.5h5" />
    </svg>
  );
}
function IconeFunil({ ativo }: { ativo: boolean }) {
  return (
    <svg {...base} strokeWidth={traco(ativo)}>
      <rect x="3" y="4" width="5" height="16" rx="1.5" /><rect x="10" y="4" width="5" height="10" rx="1.5" /><rect x="17" y="4" width="4" height="13" rx="1.5" />
    </svg>
  );
}
function IconeRede({ ativo }: { ativo: boolean }) {
  return (
    <svg {...base} strokeWidth={traco(ativo)}>
      <circle cx="9" cy="8" r="3" /><path d="M3.5 19c.5-3 2.6-5 5.5-5s5 2 5.5 5M16 11a2.6 2.6 0 1 0 0-5.2M17.5 14.2c1.8.5 2.8 2.2 3 4.8" />
    </svg>
  );
}
function IconeAjustes({ ativo }: { ativo: boolean }) {
  return (
    <svg {...base} strokeWidth={traco(ativo)}>
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" />
    </svg>
  );
}
