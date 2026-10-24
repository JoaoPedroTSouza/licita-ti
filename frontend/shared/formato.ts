/** Formatação de valores, prazos e etapas para a interface (pt-BR, fuso de Brasília). */
import type { Etapa } from "./api/tipos";

const FUSO = "America/Sao_Paulo";
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const PREFIXOS: Record<string, string> = { BRL: "R$", USD: "US$" };

export const ETAPAS: { id: Etapa; rotulo: string }[] = [
  { id: "analisando", rotulo: "Analisando" },
  { id: "proposta_enviada", rotulo: "Proposta enviada" },
  { id: "negociacao", rotulo: "Negociação" },
  { id: "fechado", rotulo: "Fechado" },
  { id: "perdido", rotulo: "Perdido" },
];

const decimais = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const umaCasa = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const inteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

export function formatarDinheiro(v: { valor: string; moeda: string } | null): string {
  if (!v) return "—";
  const prefixo = PREFIXOS[v.moeda] ?? v.moeda;
  return `${prefixo} ${decimais.format(Number(v.valor))}`;
}

export function formatarAproxBrl(brl: string | null): string {
  if (brl === null) return "";
  const n = Number(brl);
  if (n < 1000) return `≈ R$ ${inteiro.format(n)}`;
  const mil = Math.round(n / 1000);
  if (mil < 1000) return `≈ R$ ${inteiro.format(mil)} mil`;
  return `≈ R$ ${umaCasa.format(n / 1_000_000)} mi`;
}

type Partes = { ano: number; mes: number; dia: number; hora: string };

function partesEmBrasilia(d: Date): Partes {
  const f = new Intl.DateTimeFormat("en-US", {
    timeZone: FUSO, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  });
  const p = Object.fromEntries(f.formatToParts(d).map((x) => [x.type, x.value]));
  return { ano: +p.year, mes: +p.month, dia: +p.day, hora: `${p.hour}:${p.minute}` };
}

const diaAbsoluto = (p: Partes) => Date.UTC(p.ano, p.mes - 1, p.dia) / 86_400_000;

/**
 * Prazo relativo a `agora`, sempre no calendário de Brasília: "hoje 18:00", "amanhã",
 * "em 2..6 dias", "12/nov" (7 dias ou mais) e "vencido" quando o instante já passou.
 */
export function formatarPrazo(iso: string | null, agora: Date): string {
  if (!iso) return "—";
  const prazo = new Date(iso);
  if (prazo.getTime() < agora.getTime()) return "vencido";
  const alvo = partesEmBrasilia(prazo);
  const dias = diaAbsoluto(alvo) - diaAbsoluto(partesEmBrasilia(agora));
  if (dias <= 0) return `hoje ${alvo.hora}`;
  if (dias === 1) return "amanhã";
  if (dias < 7) return `em ${dias} dias`;
  return `${String(alvo.dia).padStart(2, "0")}/${MESES[alvo.mes - 1]}`;
}
