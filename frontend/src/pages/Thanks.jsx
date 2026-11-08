import { Link } from "react-router-dom";
import { Logo } from "../components/Layout";

export default function Thanks() {
  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4 text-center">
      <div className="mx-auto mb-6"><Logo /></div>
      <div className="card">
        <p className="text-3xl">✓</p>
        <h1 className="mt-2 text-xl font-semibold">¡Pago recibido!</h1>
        <p className="mt-2 text-sm text-muted">La factura quedó marcada como pagada y no recibirás más recordatorios.</p>
        <Link to="/facturas" className="btn mt-5">Ver facturas</Link>
      </div>
    </div>
  );
}
