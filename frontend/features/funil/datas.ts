/** Conversões entre ISO com fuso e o valor de <input type="datetime-local"> (horário local do navegador). */
const dois = (n: number) => String(n).padStart(2, "0");

export function isoParaLocal(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${dois(d.getMonth() + 1)}-${dois(d.getDate())}T${dois(d.getHours())}:${dois(d.getMinutes())}`;
}

export function localParaIso(valor: string): string | null {
  return valor ? new Date(valor).toISOString() : null;
}

export const MOEDAS = ["BRL", "USD", "EUR"] as const;

export const mensagemDe = (e: unknown, padrao: string) => (e instanceof Error && e.message ? e.message : padrao);

export const dataHora = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
