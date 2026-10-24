import { Suspense } from "react";
import QuadroFunil from "@/features/funil/QuadroFunil";
import Carregando from "@/shared/ui/Carregando";

export default function Pagina() {
  return (
    <Suspense fallback={<Carregando />}>
      <QuadroFunil />
    </Suspense>
  );
}
