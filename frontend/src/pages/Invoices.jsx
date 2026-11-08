import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { cop, fdate, offsetLabel } from "../format";

const today = () => new Date().toISOString().slice(0, 10);
const plus = (days) => new Date(Date.now() + days * 864e5).toISOString().slice(0, 10);

function Badge({ inv }) {
  if (inv.status === "paid") return <span className="whitespace-nowrap rounded bg-ok/15 px-2 py-0.5 text-xs text-ok">Pagada</span>;
  if (inv.status === "cancelled") return <span className="whitespace-nowrap rounded bg-border px-2 py-0.5 text-xs text-muted">Anulada</span>;
  if (inv.is_overdue) return <span className="whitespace-nowrap rounded bg-bad/15 px-2 py-0.5 text-xs text-bad">{inv.days_overdue} días de mora</span>;
  return <span className="whitespace-nowrap rounded bg-warn/15 px-2 py-0.5 text-xs text-warn">Pendiente</span>;
}

export default function Invoices() {
  const [list, setList] = useState([]);
  const [clients, setClients] = useState([]);
  const [filter, setFilter] = useState("");
  const [open, setOpen] = useState(null);
  const [error, setError] = useState("");
  const [f, setF] = useState({ client_id: "", number: "", description: "", amount_cop: "", issue_date: today(), due_date: plus(30) });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = () => api(`/invoices${filter ? `?status=${filter}` : ""}`).then(setList);
  useEffect(() => { load(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { api("/clients").then(setClients); }, []);

  const submit = async (e) => {
    e.preventDefault(); setError("");
    try {
      await api("/invoices", { method: "POST", body: { ...f, client_id: Number(f.client_id), amount_cop: Number(f.amount_cop) } });
      setF({ ...f, number: "", description: "", amount_cop: "" }); load();
    } catch (err) { setError(err.message); }
  };

  const action = async (id, path) => {
    try { await api(`/invoices/${id}/${path}`, { method: "POST" }); load(); } catch (err) { setError(err.message); }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Facturas</h1>

      {clients.length === 0 ? (
        <p className="card text-sm text-muted">Primero <Link to="/clientes" className="text-violetSoft underline">agrega un cliente</Link>.</p>
      ) : (
        <form onSubmit={submit} className="card grid gap-3 sm:grid-cols-3 lg:grid-cols-6 lg:items-end">
          <div><label className="label">Cliente</label>
            <select className="input" required value={f.client_id} onChange={set("client_id")}>
              <option value="">Elige…</option>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select></div>
          <div><label className="label">Número</label><input className="input" required value={f.number} onChange={set("number")} placeholder="FV-1004" /></div>
          <div><label className="label">Monto (COP)</label><input className="input" type="number" min={1} required value={f.amount_cop} onChange={set("amount_cop")} /></div>
          <div><label className="label">Emisión</label><input className="input" type="date" required value={f.issue_date} onChange={set("issue_date")} /></div>
          <div><label className="label">Vencimiento</label><input className="input" type="date" required value={f.due_date} onChange={set("due_date")} /></div>
          <button className="btn">Crear factura</button>
          <div className="sm:col-span-3 lg:col-span-6"><label className="label">Descripción (opcional)</label><input className="input" value={f.description} onChange={set("description")} /></div>
          {error && <p className="text-sm text-bad sm:col-span-3 lg:col-span-6">{error}</p>}
        </form>
      )}

      <div className="flex gap-2">
        {[["", "Todas"], ["pending", "Pendientes"], ["paid", "Pagadas"], ["cancelled", "Anuladas"]].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)} className={`btn-ghost ${filter === v ? "border-violet text-ink" : ""}`}>{l}</button>
        ))}
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full min-w-[760px]">
          <thead className="border-b border-border">
            <tr><th className="th">Factura</th><th className="th">Cliente</th><th className="th">Monto</th><th className="th">Vence</th><th className="th">Estado</th><th className="th">Recordatorios</th><th className="th"></th></tr>
          </thead>
          <tbody className="divide-y divide-border">
            {list.map((inv) => (
              <Fragment key={inv.id}>
                <tr>
                  <td className="td"><span className="font-mono text-violetSoft">{inv.number}</span><p className="text-xs text-muted">{inv.description}</p></td>
                  <td className="td">{inv.client_name}</td>
                  <td className="td whitespace-nowrap font-medium">{cop(inv.amount_cop)}</td>
                  <td className="td whitespace-nowrap text-muted">{fdate(inv.due_date)}</td>
                  <td className="td"><Badge inv={inv} /></td>
                  <td className="td">
                    <button onClick={() => setOpen(open === inv.id ? null : inv.id)} className="text-xs text-muted hover:text-ink">
                      {inv.reminders.length} {inv.reminders.length === 1 ? "enviado" : "enviados"} {open === inv.id ? "▴" : "▾"}
                    </button>
                  </td>
                  <td className="td">
                    {inv.status === "pending" && (
                      <div className="flex justify-end gap-1.5">
                        {inv.payment_link && <a href={inv.payment_link} target="_blank" rel="noreferrer" className="btn-ghost">Link de pago</a>}
                        <button onClick={() => action(inv.id, "mark-paid")} className="btn-ghost">Marcar pagada</button>
                        <button onClick={() => action(inv.id, "cancel")} className="btn-ghost">Anular</button>
                      </div>
                    )}
                  </td>
                </tr>
                {open === inv.id && (
                  <tr><td colSpan={7} className="bg-bg/60 px-6 py-3">
                    {inv.reminders.length === 0 ? <p className="text-xs text-muted">Sin recordatorios todavía.</p> : (
                      <ul className="space-y-1">
                        {inv.reminders.map((r) => (
                          <li key={r.id} className="text-xs text-muted">✉ {fdate(r.sent_at)} · {offsetLabel(r.offset_days)} · <span className="text-ink">{r.subject}</span></li>
                        ))}
                      </ul>
                    )}
                  </td></tr>
                )}
              </Fragment>
            ))}
            {list.length === 0 && <tr><td className="td text-muted" colSpan={7}>No hay facturas.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
