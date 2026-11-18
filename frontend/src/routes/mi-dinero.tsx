import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth";
import { getCuenta, getDolarQuotes, type Cuenta } from "@/lib/api";

export const Route = createFileRoute("/mi-dinero")({
  head: () => ({
    meta: [
      { title: "Invertix — Mi dinero" },
      { name: "description", content: "Tu dinero disponible, los plazos de tu dinero y el dinero comprometido en operaciones pendientes." },
      { property: "og:title", content: "Invertix — Mi dinero" },
      { property: "og:description", content: "Disponible, plazos y dinero comprometido de tu cuenta." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <MiDinero />
    </RequireAuth>
  ),
});

type Moneda = "ARS" | "USD";
const ars = (n: number) => n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
const usd = (n: number) => `US$ ${n.toLocaleString("es-AR", { maximumFractionDigits: 2 })}`;

// Plazos simulados del dinero (TODO: GET ${API_URL}/api/cuenta/plazos)
const MOCK_PLAZOS = [
  { label: "Disponible para operar", detalle: "Liquidación inmediata", dias: 0, ars: 0.6, usd: 0.7 },
  { label: "En liquidación (24 hs)", detalle: "Ventas de hoy", dias: 1, ars: 0.25, usd: 0.2 },
  { label: "En liquidación (48 hs)", detalle: "Operaciones de ayer", dias: 2, ars: 0.15, usd: 0.1 },
];

// Operaciones pendientes simuladas (TODO: GET ${API_URL}/api/ordenes/pendientes)
const MOCK_PENDIENTES = [
  { desc: "Compra GGAL x50", ars: 321025, usd: 0 },
  { desc: "Compra AL30 x5", ars: 0, usd: 260 },
];

function MiDinero() {
  const { user } = useAuth();
  const [cuenta, setCuenta] = useState<Cuenta | null>(null);
  const [quotes, setQuotes] = useState({ mep: 0, ccl: 0 });
  const [moneda, setMoneda] = useState<Moneda>("ARS");
  const [oculto, setOculto] = useState(false);

  useEffect(() => {
    if (!user) return;
    getCuenta(user.id).then(setCuenta);
    getDolarQuotes().then(setQuotes);
  }, [user]);

  const totalArs = cuenta ? cuenta.saldo_ars : 0;
  const totalUsd = cuenta ? cuenta.saldo_usd : 0;
  const fmt = (n: number) => (moneda === "ARS" ? ars(n) : usd(n));
  const monto = (a: number, u: number) => (moneda === "ARS" ? a : u);
  const ocultar = (s: string) => (oculto ? s.replace(/[0-9]/g, "*") : s);

  const comprometidoArs = MOCK_PENDIENTES.reduce((s, p) => s + p.ars, 0);
  const comprometidoUsd = MOCK_PENDIENTES.reduce((s, p) => s + p.usd, 0);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <h1 className="font-display text-2xl font-semibold">Mi dinero</h1>

        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {(["ARS", "USD"] as Moneda[]).map((m) => (
            <button key={m} onClick={() => setMoneda(m)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-semibold ${moneda === m ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>
              {m === "ARS" ? "Pesos" : "Dólares"}
            </button>
          ))}
        </div>

        <section className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Tu disponible total</p>
              <p className="mt-2 font-display text-4xl font-semibold">
                {cuenta ? ocultar(fmt(moneda === "ARS" ? totalArs : totalUsd)) : "—"}
              </p>
              {moneda === "ARS" && cuenta && quotes.mep > 0 && (
                <p className="mt-1 text-sm text-muted-foreground">≈ {ocultar(usd(totalArs / quotes.mep))} al MEP</p>
              )}
            </div>
            <button onClick={() => setOculto(!oculto)} aria-label={oculto ? "Mostrar saldo" : "Ocultar saldo"}
              className="rounded-md border border-border p-2 text-muted-foreground hover:bg-muted hover:text-foreground">
              {oculto ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border p-4">
            <h2 className="font-display text-lg font-semibold">Plazos de tu dinero</h2>
          </div>
          <ul className="divide-y divide-border">
            {MOCK_PLAZOS.map((p) => {
              const base = moneda === "ARS" ? totalArs : totalUsd;
              const m = base * (moneda === "ARS" ? p.ars : p.usd);
              return (
                <li key={p.label} className="flex items-center justify-between p-4">
                  <div>
                    <p className="text-sm font-semibold">{p.label}</p>
                    <p className="text-xs text-muted-foreground">{p.detalle}</p>
                  </div>
                  <p className="font-mono text-sm">{cuenta ? ocultar(fmt(m)) : "—"}</p>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border p-4">
            <h2 className="font-display text-lg font-semibold">Dinero comprometido</h2>
            <p className="text-xs text-muted-foreground">Por operaciones pendientes</p>
          </div>
          <div className="p-4">
            <p className="font-display text-2xl font-semibold">{ocultar(fmt(monto(comprometidoArs, comprometidoUsd)))}</p>
            <ul className="mt-4 space-y-2">
              {MOCK_PENDIENTES.filter((p) => monto(p.ars, p.usd) > 0).map((p) => (
                <li key={p.desc} className="flex items-center justify-between rounded-lg bg-muted px-4 py-3 text-sm">
                  <span>{p.desc}</span>
                  <span className="font-mono">{ocultar(fmt(monto(p.ars, p.usd)))}</span>
                </li>
              ))}
              {MOCK_PENDIENTES.every((p) => monto(p.ars, p.usd) === 0) && (
                <li className="py-4 text-center text-sm text-muted-foreground">No tenés operaciones pendientes en esta moneda.</li>
              )}
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}
