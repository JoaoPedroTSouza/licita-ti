import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variante?: "primario" | "secundario" | "perigo";
};

const CLASSES = { primario: "", secundario: "botao-sec", perigo: "botao-perigo" } as const;

export default function Botao({ variante = "primario", className = "", type = "button", ...resto }: Props) {
  return <button type={type} className={`botao ${CLASSES[variante]} ${className}`} {...resto} />;
}
