import { useEffect, useState } from "react";
import { api } from "../api";
import { cop, fdate, offsetLabel } from "../format";

function Stat({ label, value, sub, tone = "text-ink" }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${tone}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-muted">{sub}</p>}
    </div>
  );
}

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [rules, setRules] = useState(null);
  const [msg, setMsg] = useState("");

  const load = () => {
    api("/dashboard").then(setD);
    api("/reminders/rules").then(setRules);
  };
  useEffect(load, []);

  const runNow = async () => {
    const r = await api("/reminders/run", { method: "POST" });
    setMsg(r.allowed_now ? `Se enviaron ${r.sent} recordatorio(s).` : "Fuera del horario permitido: no se envió nada.");
    load();
  };

  if (!d) return <p className="text-muted">Cargando…</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Resumen de cartera</h1>
        <p className="text-sm text-muted">Lo que te deben, lo que ya está vencido y lo que el bot ya cobró por ti.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Por cobrar" value={cop(d.total_pending_cop)} sub={`${d.count_pending} facturas pendientes`} />
        <Stat label="Vencido" value={cop(d.total_overdue_cop)} sub={`${d.count_overdue} facturas en mora`} tone="text-bad" />
        <Stat label="Cobrado" value={cop(d.total_paid_cop)} sub={`${d.count_paid} facturas pagadas`} tone="text-ok" />
        <Stat label="Recordatorios" value={d.reminders_sent} sub="enviados automáticamente" tone="text-violetSoft" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <h2 className="mb-3 font-medium">Últimos recordatorios enviados</h2>
          {d.recent_reminders.length === 0 ? (
            <p className="text-sm text-muted">Aún no se ha enviado ninguno.</p>
          ) : (
            <ul className="divide-y divide-border">
              {d.recent_reminders.map((r, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-2.5 text-sm">
                  <span><span className="font-mono text-violetSoft">{r.invoice_number}</span> · {r.client}</span>
                  <span className="text-xs text-muted">{offsetLabel(r.offset_days)} · {fdate(r.sent_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card space-y-3">
          <h2 className="font-medium">Reglas del bot</h2>
          {rules && (
            <>
              <p className="text-sm text-muted">Envía correos en estos días respecto al vencimiento:</p>
              <div className="flex flex-wrap gap-1.5">
                {rules.offsets.map((o) => (
                  <span key={o} className="rounded border border-border px-2 py-0.5 font-mono text-xs">{o > 0 ? `+${o}` : o}</span>
                ))}
              </div>
              <p className="text-xs text-muted">{rules.allowed_hours}</p>
              <p className="text-xs text-muted">Mínimo {rules.min_days_between_overdue} días entre cobros de una factura vencida (Ley 2300 de 2023).</p>
              <p className={`text-xs ${rules.allowed_now ? "text-ok" : "text-warn"}`}>
                ● {rules.allowed_now ? "Ahora está en horario permitido" : "Ahora está fuera de horario"}
              </p>
            </>
          )}
          <button onClick={runNow} className="btn w-full">Ejecutar ahora</button>
          {msg && <p className="text-xs text-muted">{msg}</p>}
        </div>
      </div>
    </div>
  );
}
