export default function Vazio({ titulo, children }: { titulo: string; children?: React.ReactNode }) {
  return (
    <div className="cartao px-6 py-10 text-center">
      <p className="font-semibold">{titulo}</p>
      {children && <p className="suave mt-1 text-sm">{children}</p>}
    </div>
  );
}
