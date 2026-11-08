const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const getToken = () => {
  try { return localStorage.getItem("ic_token"); } catch { return null; }
};
export const setToken = (t) => {
  try { t ? localStorage.setItem("ic_token", t) : localStorage.removeItem("ic_token"); } catch { /* sin storage */ }
};

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_URL}${path}`, { method, headers, body: payload });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && token) { setToken(null); window.location.href = "/login"; }
    const d = data.detail;
    const msg = Array.isArray(d) ? d.map((e) => e.msg.replace("Value error, ", "")).join(". ") : d || "Error inesperado";
    throw new Error(msg);
  }
  return data;
}
