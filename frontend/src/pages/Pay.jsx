import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Logo } from "../components/Layout";
import { cop, fdate } from "../format";

// Simulador de Wompi para la demo: el pago pasa por el mismo webhook firmado que usaría Wompi real.
export default function Pay() {
  const { reference } = useParams();
  const navigate = useNavigate();
  const [inv, setInv] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { api(`/webhooks/demo/invoice/${reference}`).then(setInv).catch((e) => setError(e.message)); }, [reference]);

  const pay = async () => {
    setLoading(true);
    try { await api(`/webhooks/demo/pay/${reference}`, { method: "POST" }); navigate("/gracias"); }
    catch (e) { setError(e.message); setLoading(false); }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <div className="mb-6"><Logo /></div>
      <div className="card space-y-4">
        <p className="rounded bg-warn/15 px-3 py-2 text-xs text-warn">Simulador de pago (demo). No se cobra dinero real.</p>
        {error && <p className="text-sm text-bad">{error}</p>}
        {inv && (
          <>
            <div>
              <p className="text-xs text-muted">Factura</p>
              <p className="font-mono text-violetSoft">{inv.number}</p>
            </div>
            <div className="flex justify-between text-sm"><span className="text-muted">Vence</span><span>{fdate(inv.due_date)}</span></div>
            <div className="flex justify-between text-lg font-semibold"><span>Total</span><span>{cop(inv.amount_cop)}</span></div>
            {inv.status === "pending" ? (
              <button onClick={pay} disabled={loading} className="btn w-full">Pagar con Wompi (simulado)</button>
            ) : (
              <p className="text-sm text-ok">Esta factura ya está {inv.status === "paid" ? "pagada" : "anulada"}.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
