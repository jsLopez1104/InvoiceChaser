import { Navigate, Route, Routes } from "react-router-dom";
import { getToken } from "./api";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Clients from "./pages/Clients";
import Invoices from "./pages/Invoices";
import Pay from "./pages/Pay";
import Thanks from "./pages/Thanks";
import { Privacy, Terms } from "./pages/Legal";

function Private({ children }) {
  return getToken() ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Register />} />
      <Route path="/privacidad" element={<Privacy />} />
      <Route path="/terminos" element={<Terms />} />
      <Route path="/pagar/:reference" element={<Pay />} />
      <Route path="/gracias" element={<Thanks />} />
      <Route path="/" element={<Private><Dashboard /></Private>} />
      <Route path="/clientes" element={<Private><Clients /></Private>} />
      <Route path="/facturas" element={<Private><Invoices /></Private>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
