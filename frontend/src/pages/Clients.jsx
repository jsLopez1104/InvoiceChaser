import { useEffect, useState } from "react";
import { api } from "../api";

const empty = { name: "", email: "", phone: "" };

export default function Clients() {
  const [list, setList] = useState([]);
  const [f, setF] = useState(empty);
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = () => api("/clients").then(setList);
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault(); setError("");
    try {
      await api("/clients", { method: "POST", body: { ...f, phone: f.phone || null } });
      setF(empty); load();
    } catch (err) { setError(err.message); }
  };

  const remove = async (id) => {
    try { await api(`/clients/${id}`, { method: "DELETE" }); load(); } catch (err) { setError(err.message); }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Clientes</h1>

      <form onSubmit={submit} className="card grid gap-3 sm:grid-cols-4 sm:items-end">
        <div><label className="label">Nombre</label><input className="input" required minLength={2} value={f.name} onChange={set("name")} /></div>
        <div><label className="label">Correo de cobro</label><input className="input" type="email" required value={f.email} onChange={set("email")} /></div>
        <div><label className="label">Teléfono (opcional)</label><input className="input" value={f.phone} onChange={set("phone")} /></div>
        <button className="btn">Agregar cliente</button>
        {error && <p className="text-sm text-bad sm:col-span-4">{error}</p>}
      </form>

      <div className="card overflow-x-auto p-0">
        <table className="w-full min-w-[520px]">
          <thead className="border-b border-border"><tr><th className="th">Nombre</th><th className="th">Correo</th><th className="th">Teléfono</th><th className="th"></th></tr></thead>
          <tbody className="divide-y divide-border">
            {list.map((c) => (
              <tr key={c.id}>
                <td className="td font-medium">{c.name}</td>
                <td className="td text-muted">{c.email}</td>
                <td className="td text-muted">{c.phone || "—"}</td>
                <td className="td text-right"><button onClick={() => remove(c.id)} className="btn-ghost">Borrar</button></td>
              </tr>
            ))}
            {list.length === 0 && <tr><td className="td text-muted" colSpan={4}>Aún no tienes clientes.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
