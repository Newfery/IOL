import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth";
import { getAssets, getCuenta, getDolarQuotes, getPortfolio, type Asset, type Cuenta, type Holding } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Invertix — Tu cuenta" },
      { name: "description", content: "Mirá tu saldo total en pesos, dólar MEP o CCL y el rendimiento de tus inversiones." },
      { property: "og:title", content: "Invertix — Tu cuenta" },
      { property: "og:description", content: "Saldo, inversiones y rendimientos en un solo lugar." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <Home />
    </RequireAuth>
  ),
});

type Moneda = "ARS" | "MEP" | "CCL";
const ars = (n: number) => n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
const usd = (n: number) => `US$ ${n.toLocaleString("es-AR", { maximumFractionDigits: 2 })}`;
const COLORS = ["var(--primary)", "var(--gain)", "var(--chart-3, #f59e0b)", "var(--chart-4, #60a5fa)", "var(--loss)"];

function Home() {
  const { user } = useAuth();
  const [cuenta, setCuenta] = useState<Cuenta | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [quotes, setQuotes] = useState({ mep: 0, ccl: 0 });
  const [moneda, setMoneda] = useState<Moneda>("ARS");

  useEffect(() => {
    if (!user) return;
    getCuenta(user.id).then(setCuenta);
    getAssets().then(setAssets);
    getPortfolio().then(setHoldings);
    getDolarQuotes().then(setQuotes);
  }, [user]);

  const rows = useMemo(
    () =>
      holdings.map((h) => {
        const a = assets.find((x) => x.symbol === h.symbol);
        const price = a?.price ?? h.avgPrice;
        const value = price * h.qty;
        const pnl = (price - h.avgPrice) * h.qty;
        return { ...h, name: a?.name ?? h.symbol, price, value, pnl, pnlPct: ((price - h.avgPrice) / h.avgPrice) * 100 };
      }),
    [holdings, assets],
  );

  const invertido = rows.reduce((s, r) => s + r.value, 0);
  const totalArs = cuenta && quotes.mep ? cuenta.saldo_ars + cuenta.saldo_usd * quotes.mep + invertido : 0;
  const totalPnl = rows.reduce((s, r) => s + r.pnl, 0);
  const shownTotal = moneda === "ARS" ? ars(totalArs) : usd(totalArs / (moneda === "MEP" ? quotes.mep : quotes.ccl || 1));
  const pieData = rows.filter((r) => r.pnl > 0).map((r) => ({ name: r.symbol, value: r.pnl }));

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <div>
          <h1 className="font-display text-2xl font-semibold">Hola, {user?.nombre}</h1>
          <p className="text-sm text-muted-foreground">Comitente N° {cuenta?.numero_comitente} · Perfil {user?.perfil_riesgo}</p>
        </div>

        <section className="rounded-xl border border-border bg-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Total</p>
              <p className="mt-2 font-display text-4xl font-semibold">{shownTotal}</p>
              <p className={`mt-1 text-sm ${totalPnl >= 0 ? "text-gain" : "text-loss"}`}>
                Rend. acumulado {totalPnl >= 0 ? "+" : ""}{ars(totalPnl)}
              </p>
            </div>
            <div>
              <p className="mb-2 text-xs text-muted-foreground">Expresado en</p>
              <div className="flex gap-1 rounded-lg bg-muted p-1">
                {(["ARS", "MEP", "CCL"] as Moneda[]).map((m) => (
                  <button key={m} onClick={() => setMoneda(m)}
                    className={`rounded-md px-3 py-1.5 text-xs font-semibold ${moneda === m ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>
                    {m === "ARS" ? "Pesos" : `Dólar ${m}`}
                  </button>
                ))}
              </div>
              {moneda !== "ARS" && (
                <p className="mt-2 text-right text-xs text-muted-foreground">
                  Cotización {ars(moneda === "MEP" ? quotes.mep : quotes.ccl)}
                </p>
              )}
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-3 font-display text-lg font-semibold">Disponible para invertir</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-border bg-card p-5">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Pesos</p>
              <p className="mt-2 font-display text-2xl font-semibold">{cuenta ? ars(cuenta.saldo_ars) : "—"}</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Dólares</p>
              <p className="mt-2 font-display text-2xl font-semibold">{cuenta ? usd(cuenta.saldo_usd) : "—"}</p>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border p-4">
            <h2 className="font-display text-lg font-semibold">Mis inversiones</h2>
          </div>
          {rows.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aún no realizaste ninguna inversión.{" "}
              <Link to="/operar" className="text-primary">Comenzar ahora →</Link>
            </div>
          ) : (
            <>
              <div className="p-6">
                <div className="mx-auto h-72 max-w-md">
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Rendimientos por activo</h3>
                  <ResponsiveContainer width="100%" height="90%">
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={2} stroke="none">
                        {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v: number) => ars(v)}
                        contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                        itemStyle={{ color: "var(--foreground)" }} labelStyle={{ color: "var(--foreground)" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <ul className="mx-auto mt-6 max-w-md space-y-3 text-sm">
                  {rows.map((r) => {
                    const idx = pieData.findIndex((p) => p.name === r.symbol);
                    return (
                      <li key={r.symbol} className="flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <span className="h-3 w-3 rounded-full" style={{ background: idx >= 0 ? COLORS[idx % COLORS.length] : "var(--muted)" }} />
                          <b>{r.symbol}</b>
                        </span>
                        <span className={`font-mono ${r.pnl >= 0 ? "text-gain" : "text-loss"}`}>
                          {r.pnl >= 0 ? "+" : ""}{r.pnlPct.toFixed(1)}%
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
