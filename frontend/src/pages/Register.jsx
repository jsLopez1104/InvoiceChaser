import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { AuthShell } from "./Login";

export default function Register() {
  const navigate = useNavigate();
  const [f, setF] = useState({ full_name: "", business_name: "", email: "", password: "" });
  // Autorización Ley 1581: checkbox SIN marcar por defecto
  const [accept, setAccept] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await api("/auth/register", { method: "POST", body: { ...f, accept_privacy_policy: accept } });
      const { access_token } = await api("/auth/login", { method: "POST", form: { username: f.email, password: f.password } });
      setToken(access_token);
      navigate("/");
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  };

  return (
    <AuthShell title="Crea tu cuenta">
      <form onSubmit={submit} className="space-y-4">
        <div><label className="label">Tu nombre</label><input className="input" required minLength={2} value={f.full_name} onChange={set("full_name")} /></div>
        <div><label className="label">Nombre del negocio (aparece en los correos)</label><input className="input" required minLength={2} value={f.business_name} onChange={set("business_name")} /></div>
        <div><label className="label">Correo</label><input className="input" type="email" required value={f.email} onChange={set("email")} /></div>
        <div><label className="label">Contraseña (mínimo 8 caracteres)</label><input className="input" type="password" required minLength={8} value={f.password} onChange={set("password")} /></div>
        <label className="flex items-start gap-2 text-xs text-muted">
          <input type="checkbox" className="mt-0.5 accent-violet" checked={accept} onChange={(e) => setAccept(e.target.checked)} />
          <span>
            Autorizo el tratamiento de mis datos personales según la{" "}
            <Link to="/privacidad" target="_blank" className="text-violetSoft underline">Política de tratamiento de datos</Link>{" "}
            y acepto los <Link to="/terminos" target="_blank" className="text-violetSoft underline">Términos</Link>.
          </span>
        </label>
        {error && <p className="text-sm text-bad">{error}</p>}
        <button className="btn w-full" disabled={loading || !accept}>Crear cuenta</button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        ¿Ya tienes cuenta? <Link to="/login" className="text-violetSoft hover:underline">Inicia sesión</Link>
      </p>
    </AuthShell>
  );
}
