import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { getAssets, getPortfolio, type Asset, type Holding } from "@/lib/api";
import { createAssetColorMap, getAssetColor } from "@/lib/asset-colors";

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

const PAGE_SIZE = 10;

function MisInversiones() {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [page, setPage] = useState(1);
  const [compositionCurrency, setCompositionCurrency] = useState<Asset["currency"]>("ARS");

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

  const colorBySymbol = useMemo(
    () => createAssetColorMap(rows.map((row) => row.symbol)),
    [rows],
  );
  const arsRows = rows.filter((r) => r.currency === "ARS");
  const usdRows = rows.filter((r) => r.currency === "USD");
  const totalArsValue = arsRows.reduce((s, r) => s + r.value, 0);
  const totalUsdValue = usdRows.reduce((s, r) => s + r.value, 0);
  const totalArsPnl = arsRows.reduce((s, r) => s + r.pnl, 0);
  const totalUsdPnl = usdRows.reduce((s, r) => s + r.pnl, 0);
  const arsPieData = arsRows.map((r) => ({ name: r.symbol, value: r.value }));
  const usdPieData = usdRows.map((r) => ({ name: r.symbol, value: r.value }));
  useEffect(() => {
    if (compositionCurrency === "ARS" && arsRows.length === 0 && usdRows.length > 0) {
      setCompositionCurrency("USD");
    } else if (compositionCurrency === "USD" && usdRows.length === 0 && arsRows.length > 0) {
      setCompositionCurrency("ARS");
    }
  }, [compositionCurrency, arsRows.length, usdRows.length]);
  const compositionRows = compositionCurrency === "ARS" ? arsRows : usdRows;
  const compositionPieData = compositionCurrency === "ARS" ? arsPieData : usdPieData;
  const compositionTotal = compositionCurrency === "ARS" ? totalArsValue : totalUsdValue;
  const pageCount = Math.ceil(rows.length / PAGE_SIZE);
  const currentPage = Math.min(page, Math.max(1, pageCount));
  const pageStart = (currentPage - 1) * PAGE_SIZE;
  const pageRows = rows.slice(pageStart, pageStart + PAGE_SIZE);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
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

        {rows.length > 0 && (
          <section className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-lg font-semibold">Composición de la cartera</h2>
              <div role="group" aria-label="Moneda de la composición" className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={compositionCurrency === "ARS" ? "default" : "outline"}
                  aria-pressed={compositionCurrency === "ARS"}
                  disabled={arsRows.length === 0}
                  onClick={() => setCompositionCurrency("ARS")}
                >
                  ARS
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={compositionCurrency === "USD" ? "default" : "outline"}
                  aria-pressed={compositionCurrency === "USD"}
                  disabled={usdRows.length === 0}
                  onClick={() => setCompositionCurrency("USD")}
                >
                  USD
                </Button>
              </div>
            </div>
            <div className="grid items-start gap-8 md:grid-cols-2">
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-muted-foreground">Posiciones en {compositionCurrency}</h3>
                  <div className="mx-auto h-72 max-w-md">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={compositionPieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={100} paddingAngle={0} minAngle={8} stroke="var(--background)" strokeWidth={2}>
                          {compositionPieData.map((entry) => (
                            <Cell key={entry.name} fill={getAssetColor(colorBySymbol, entry.name)} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(v: number) => fmt(v, compositionCurrency)}
                          contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                          itemStyle={{ color: "var(--foreground)" }}
                          labelStyle={{ color: "var(--foreground)" }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
              <ul className="max-h-72 space-y-3 overflow-y-auto text-sm md:pt-1">
                {compositionRows.map((r) => {
                  return (
                    <li key={r.symbol} className="flex items-center justify-between gap-4">
                      <span className="flex min-w-0 items-center gap-2">
                        <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: getAssetColor(colorBySymbol, r.symbol) }} />
                        <b className="shrink-0">{r.symbol}</b>
                        <span className="truncate text-muted-foreground">{r.name}</span>
                        <span className="shrink-0 text-xs text-muted-foreground">{r.currency}</span>
                      </span>
                      <span className="shrink-0 font-mono">{(compositionTotal ? (r.value / compositionTotal) * 100 : 0).toFixed(1)}%</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </section>
        )}

        <section aria-labelledby="portfolio-assets-heading" className="overflow-hidden rounded-xl border border-border bg-card">
          <h2 id="portfolio-assets-heading" className="px-4 py-3 font-display text-lg font-semibold">
            Tus activos
          </h2>
          {rows.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aún no realizaste ninguna inversión.{" "}
              <Link to="/operar" className="text-primary">Comenzar ahora →</Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] text-sm">
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
                  {pageRows.map((r) => (
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
          {pageCount > 1 && (
            <nav aria-label="Paginación de tus activos" className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
              <p aria-live="polite" className="text-sm text-muted-foreground">
                Mostrando {pageStart + 1}–{pageStart + pageRows.length} de {rows.length} activos
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="outline" size="sm" disabled={currentPage === 1}
                  onClick={() => setPage(currentPage - 1)}>
                  Anterior
                </Button>
                <span className="text-sm">Página {currentPage} de {pageCount}</span>
                <Button type="button" variant="outline" size="sm" disabled={currentPage === pageCount}
                  onClick={() => setPage(currentPage + 1)}>
                  Siguiente
                </Button>
              </div>
            </nav>
          )}
        </section>
      </main>
    </div>
  );
}
