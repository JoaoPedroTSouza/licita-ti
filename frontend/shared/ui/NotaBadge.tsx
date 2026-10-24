import Etiqueta from "./Etiqueta";

/** Nota de aderência (0-100): verde a partir de 80, neutra abaixo; sem nota mostra "—". */
export default function NotaBadge({ nota }: { nota: number | null }) {
  return <Etiqueta tom={nota !== null && nota >= 80 ? "acento" : "neutro"}>{nota ?? "—"}</Etiqueta>;
}
