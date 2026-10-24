import type { HTMLAttributes } from "react";

export default function Cartao({ className = "", ...resto }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`cartao ${className}`} {...resto} />;
}
