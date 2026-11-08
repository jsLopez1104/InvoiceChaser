import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { Footer, Logo } from "../components/Layout";

export function AuthShell({ title, children }) {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-4 py-12">
        <div className="mb-8"><Logo /></div>
        <h1 className="mb-1 text-2xl font-semibold">{title}</h1>
        <p className="mb-6 text-sm text-muted">Persigue tus facturas sin pagar para que tú no tengas que hacerlo.</p>
        {children}
      </div>
      <Footer />
    </div>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const doLogin = async (u, p) => {
    setError(""); setLoading(true);
    try {
      const { access_token } = await api("/auth/login", { method: "POST", form: { username: u, password: p } });
      setToken(access_token);
      navigate("/");
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  };

  return (
    <AuthShell title="Inicia sesión">
      <form onSubmit={(e) => { e.preventDefault(); doLogin(email, password); }} className="space-y-4">
        <div><label className="label">Correo</label>
          <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></div>
        <div><label className="label">Contraseña</label>
          <input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></div>
        {error && <p className="text-sm text-bad">{error}</p>}
        <button className="btn w-full" disabled={loading}>Entrar</button>
      </form>
      <button onClick={() => doLogin("demo@invoicechaser.dev", "demo12345")} disabled={loading}
        className="mt-3 w-full rounded-md border border-violet/50 px-4 py-2 text-sm text-violetSoft hover:bg-violet/10">
        Probar la demo sin registrarme
      </button>
      <p className="mt-6 text-center text-sm text-muted">
        ¿No tienes cuenta? <Link to="/registro" className="text-violetSoft hover:underline">Regístrate</Link>
      </p>
    </AuthShell>
  );
}
