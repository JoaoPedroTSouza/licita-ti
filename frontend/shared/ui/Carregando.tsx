export default function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <p role="status" className="suave py-10 text-center text-sm">
      {texto}
    </p>
  );
}
