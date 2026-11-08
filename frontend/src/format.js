export const cop = (n) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n);

export const fdate = (s) =>
  new Date(s.length === 10 ? `${s}T12:00:00` : s).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });

export const offsetLabel = (o) => (o < 0 ? `${-o} días antes` : o === 0 ? "día de vencimiento" : `${o} días de mora`);
