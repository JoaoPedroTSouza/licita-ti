"use client";

import { useParams } from "next/navigation";
import DetalheOportunidade from "@/features/entrada/DetalheOportunidade";

export default function Pagina() {
  const { id } = useParams<{ id: string }>();
  return <DetalheOportunidade id={Number(id)} />;
}
