const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const dataHora = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "America/Sao_Paulo",
});

export function formatarValor(v: number | null | undefined): string {
  if (!v) return "Valor sigiloso/não informado";
  return moeda.format(v);
}

const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });

/** R$ 1,2 mi · R$ 380 mil */
export function formatarValorCurto(v: number | null | undefined): string {
  if (!v) return "R$ 0";
  return `R$ ${compacto.format(v)}`;
}

export function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—";
  return dataHora.format(new Date(iso));
}

/** "encerra em 2 dias", "encerra em 5h", "encerrado" */
export function prazoRelativo(iso: string | null | undefined): { texto: string; urgente: boolean; encerrado: boolean } {
  if (!iso) return { texto: "sem prazo informado", urgente: false, encerrado: false };
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return { texto: "encerrado", urgente: false, encerrado: true };
  const horas = Math.floor(diff / 3_600_000);
  if (horas < 24) return { texto: `encerra em ${Math.max(1, horas)}h`, urgente: true, encerrado: false };
  const dias = Math.floor(horas / 24);
  return { texto: `encerra em ${dias} dia${dias > 1 ? "s" : ""}`, urgente: dias <= 2, encerrado: false };
}

export function tempoDesde(iso: string | null | undefined): string {
  if (!iso) return "nunca";
  const min = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000);
  if (min < 1) return "agora";
  if (min < 60) return `há ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `há ${h}h`;
  return `há ${Math.floor(h / 24)} dia(s)`;
}
