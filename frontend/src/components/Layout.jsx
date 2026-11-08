import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold">
      <img src="/favicon.svg" alt="" className="h-7 w-7" />
      Invoice<span className="text-violetSoft">Chaser</span>
    </Link>
  );
}

export function Footer() {
  return (
    <footer className="mx-auto mt-16 max-w-6xl px-4 pb-8 text-xs text-muted">
      <div className="flex flex-wrap gap-4 border-t border-border pt-6">
        <span>© 2026 InvoiceChaser · Proyecto de portafolio</span>
        <Link to="/privacidad" className="hover:text-ink">Política de datos</Link>
        <Link to="/terminos" className="hover:text-ink">Términos</Link>
      </div>
    </footer>
  );
}

export default function Layout({ children }) {
  const [me, setMe] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { api("/auth/me").then(setMe).catch(() => {}); }, []);

  const logout = () => { setToken(null); navigate("/login"); };
  const deleteAccount = async () => {
    const typed = window.prompt('Esto borra tu cuenta y TODOS tus datos. Escribe "BORRAR" para confirmar.');
    if (typed !== "BORRAR") return;
    await api("/auth/me", { method: "DELETE" });
    logout();
  };

  const link = ({ isActive }) =>
    `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-violet/15 text-violetSoft" : "text-muted hover:text-ink"}`;

  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Logo />
          <nav className="flex gap-1">
            <NavLink to="/" end className={link}>Resumen</NavLink>
            <NavLink to="/facturas" className={link}>Facturas</NavLink>
            <NavLink to="/clientes" className={link}>Clientes</NavLink>
          </nav>
          <div className="flex items-center gap-2 text-xs text-muted">
            {me && <span className="hidden sm:inline">{me.business_name}</span>}
            <button onClick={deleteAccount} className="btn-ghost" title="Derecho de supresión (Ley 1581)">Borrar cuenta</button>
            <button onClick={logout} className="btn-ghost">Salir</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      <Footer />
    </div>
  );
}
