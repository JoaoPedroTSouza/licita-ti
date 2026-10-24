const TONS = {
  neutro: "bg-superficie-2 text-texto-suave",
  acento: "bg-acento-suave text-acento-texto",
  aviso: "bg-aviso-suave text-aviso-texto",
  perigo: "bg-perigo-suave text-perigo",
} as const;

export default function Etiqueta({
  tom = "neutro",
  children,
}: {
  tom?: keyof typeof TONS;
  children: React.ReactNode;
}) {
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${TONS[tom]}`}>
      {children}
    </span>
  );
}
