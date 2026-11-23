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

const fmt = (n: number, currency: Asset["currency"]) =>
  n.toLocaleString("es-AR", { style: "currency", currency, maximumFractionDigits: 2 });

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
        const currency = a?.currency ?? h.currency;
        const value = price * h.qty;
        const pnl = (price - h.avgPrice) * h.qty;
        return {
          ...h,
          name: a?.name ?? h.symbol,
          type: a?.type ?? "—",
          currency,
          price,
          value,
          pnl,
          pnlPct: ((price - h.avgPrice) / h.avgPrice) * 100,
        };
      }),
    [holdings, assets],
  );

  const colorBySymbol = useMemo(() => {
    const symbols = [...new Set(rows.map((row) => row.symbol))].sort();
    const colors = new Map<string, string>();
    symbols.forEach((symbol, index) => {
      const hue = (index * 137.508) % 360;
      colors.set(symbol, `hsl(${hue}, 70%, 52%)`);
    });
    return colors;
  }, [rows]);

  const colorForSymbol = (symbol: string) => colorBySymbol.get(symbol) ?? "var(--muted)";
  const arsRows = rows.filter((r) => r.currency === "ARS");
  const usdRows = rows.filter((r) => r.currency === "USD");
  const totalArsValue = arsRows.reduce((s, r) => s + r.value, 0);
  const totalUsdValue = usdRows.reduce((s, r) => s + r.value, 0);
  const totalArsPnl = arsRows.reduce((s, r) => s + r.pnl, 0);
  const totalUsdPnl = usdRows.reduce((s, r) => s + r.pnl, 0);
  const arsPieData = arsRows.map((r) => ({ name: r.symbol, value: r.value }));
  const usdPieData = usdRows.map((r) => ({ name: r.symbol, value: r.value }));

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
            {arsRows.length > 0 && <p className="font-display text-2xl font-semibold">{fmt(totalArsValue, "ARS")}</p>}
            {usdRows.length > 0 && <p className="font-display text-2xl font-semibold">{fmt(totalUsdValue, "USD")}</p>}
            {arsRows.length > 0 && (
              <p className={`text-sm ${totalArsPnl >= 0 ? "text-gain" : "text-loss"}`}>
                Rendimiento ARS: {totalArsPnl >= 0 ? "+" : ""}{fmt(totalArsPnl, "ARS")}
              </p>
            )}
            {usdRows.length > 0 && (
              <p className={`text-sm ${totalUsdPnl >= 0 ? "text-gain" : "text-loss"}`}>
                Rendimiento USD: {totalUsdPnl >= 0 ? "+" : ""}{fmt(totalUsdPnl, "USD")}
              </p>
            )}
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
                        <Link
                          to="/activos/$symbol"
                          params={{ symbol: r.symbol }}
                          className="font-semibold hover:text-primary"
                        >
                          {r.symbol}
                        </Link>
                        <span className="ml-2 text-muted-foreground">{r.name}</span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{r.type}</td>
                      <td className="px-4 py-3 text-right font-mono">{r.qty}</td>
                      <td className="px-4 py-3 text-right font-mono">{fmt(r.avgPrice, r.currency)}</td>
                      <td className="px-4 py-3 text-right font-mono">{fmt(r.price, r.currency)}</td>
                      <td className="px-4 py-3 text-right font-mono">{fmt(r.value, r.currency)}</td>
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
            <div className="grid items-start gap-8 md:grid-cols-2">
              <div className="space-y-6">
                {[
                  { label: "ARS", currency: "ARS" as const, data: arsPieData },
                  { label: "USD", currency: "USD" as const, data: usdPieData },
                ].filter((chart) => chart.data.length > 0).map((chart) => (
                  <div key={chart.currency}>
                    <h3 className="text-sm font-semibold text-muted-foreground">Posiciones en {chart.label}</h3>
                    <div className="mx-auto h-72 max-w-md">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={chart.data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={100} paddingAngle={2} stroke="none">
                            {chart.data.map((entry) => (
                              <Cell key={entry.name} fill={colorForSymbol(entry.name)} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(v: number) => fmt(v, chart.currency)}
                            contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                            itemStyle={{ color: "var(--foreground)" }}
                            labelStyle={{ color: "var(--foreground)" }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
              <ul className="space-y-3 text-sm md:pt-1">
                {rows.map((r) => {
                  const currencyTotal = r.currency === "ARS" ? totalArsValue : totalUsdValue;
                  return (
                    <li key={r.symbol} className="flex items-center justify-between gap-4">
                      <span className="flex min-w-0 items-center gap-2">
                        <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: colorForSymbol(r.symbol) }} />
                        <b className="shrink-0">{r.symbol}</b>
                        <span className="truncate text-muted-foreground">{r.name}</span>
                        <span className="shrink-0 text-xs text-muted-foreground">{r.currency}</span>
                      </span>
                      <span className="shrink-0 font-mono">{(currencyTotal ? (r.value / currencyTotal) * 100 : 0).toFixed(1)}%</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
