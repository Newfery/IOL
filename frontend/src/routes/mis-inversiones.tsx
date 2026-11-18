import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth";
import { getAssets, getPortfolio, type Asset, type Holding } from "@/lib/api";

export const Route = createFileRoute("/mis-inversiones")({
  head: () => ({
    meta: [
      { title: "Invertix — Mis inversiones" },
      { name: "description", content: "Detalle de todas tus inversiones: cantidad, precio promedio, valor actual y rendimiento." },
      { property: "og:title", content: "Invertix — Mis inversiones" },
      { property: "og:description", content: "Detalle de todas tus inversiones y su rendimiento." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <MisInversiones />
    </RequireAuth>
  ),
});

const ars = (n: number) => n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
const COLORS = ["var(--primary)", "var(--gain)", "var(--chart-3, #f59e0b)", "var(--chart-4, #60a5fa)", "var(--loss)", "var(--chart-5, #a78bfa)"];

function MisInversiones() {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);

  useEffect(() => {
    if (!user) return;
    getAssets().then(setAssets);
    getPortfolio().then(setHoldings);
  }, [user]);

  const rows = useMemo(
    () =>
      holdings.map((h) => {
        const a = assets.find((x) => x.symbol === h.symbol);
        const price = a?.price ?? h.avgPrice;
        const value = price * h.qty;
        const pnl = (price - h.avgPrice) * h.qty;
        return {
          ...h,
          name: a?.name ?? h.symbol,
          type: a?.type ?? "—",
          price,
          value,
          pnl,
          pnlPct: ((price - h.avgPrice) / h.avgPrice) * 100,
        };
      }),
    [holdings, assets],
  );

  const totalValue = rows.reduce((s, r) => s + r.value, 0);
  const totalPnl = rows.reduce((s, r) => s + r.pnl, 0);
  const pieData = rows.map((r) => ({ name: r.symbol, value: r.value }));

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-semibold">Mis inversiones</h1>
            <p className="text-sm text-muted-foreground">Detalle de todas tus posiciones</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Valor total</p>
            <p className="font-display text-2xl font-semibold">{ars(totalValue)}</p>
            <p className={`text-sm ${totalPnl >= 0 ? "text-gain" : "text-loss"}`}>
              {totalPnl >= 0 ? "+" : ""}{ars(totalPnl)}
            </p>
          </div>
        </div>

        <section className="overflow-hidden rounded-xl border border-border bg-card">
          {rows.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aún no realizaste ninguna inversión.{" "}
              <Link to="/operar" className="text-primary">Comenzar ahora →</Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-3">Activo</th>
                    <th className="px-4 py-3">Tipo</th>
                    <th className="px-4 py-3 text-right">Cantidad</th>
                    <th className="px-4 py-3 text-right">Precio promedio</th>
                    <th className="px-4 py-3 text-right">Precio actual</th>
                    <th className="px-4 py-3 text-right">Valor actual</th>
                    <th className="px-4 py-3 text-right">Rendimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.symbol} className="border-b border-border/50 last:border-0">
                      <td className="px-4 py-3">
                        <b>{r.symbol}</b>
                        <span className="ml-2 text-muted-foreground">{r.name}</span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{r.type}</td>
                      <td className="px-4 py-3 text-right font-mono">{r.qty}</td>
                      <td className="px-4 py-3 text-right font-mono">{ars(r.avgPrice)}</td>
                      <td className="px-4 py-3 text-right font-mono">{ars(r.price)}</td>
                      <td className="px-4 py-3 text-right font-mono">{ars(r.value)}</td>
                      <td className={`px-4 py-3 text-right font-mono ${r.pnl >= 0 ? "text-gain" : "text-loss"}`}>
                        {r.pnl >= 0 ? "+" : ""}{r.pnlPct.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {rows.length > 0 && (
          <section className="rounded-xl border border-border bg-card p-6">
            <h2 className="mb-2 font-display text-lg font-semibold">Composición de la cartera</h2>
            <div className="mx-auto h-80 max-w-md">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={100} paddingAngle={2} stroke="none">
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip
                    formatter={(v: number) => ars(v)}
                    contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                    itemStyle={{ color: "var(--foreground)" }}
                    labelStyle={{ color: "var(--foreground)" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="mx-auto mt-6 max-w-md space-y-3 text-sm">
              {rows.map((r, i) => (
                <li key={r.symbol} className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                    <b>{r.symbol}</b>
                    <span className="text-muted-foreground">{r.name}</span>
                  </span>
                  <span className="font-mono">{((r.value / totalValue) * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
