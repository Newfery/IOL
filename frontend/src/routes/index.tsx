import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth";
import { getAssets, getCuenta, getDolarQuotes, getPortfolio, type Asset, type Cuenta, type DolarQuotes, type Holding } from "@/lib/api";

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
const COLORS = ["var(--primary)", "var(--chart-4)", "var(--chart-1)", "var(--chart-2)", "var(--loss)"];

function Home() {
  const { user } = useAuth();
  const [cuenta, setCuenta] = useState<Cuenta | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [quotes, setQuotes] = useState<DolarQuotes>({ mep: null, ccl: null });
  const [quoteError, setQuoteError] = useState(false);
  const [moneda, setMoneda] = useState<Moneda>("ARS");
  const [moneyAction, setMoneyAction] = useState<"deposit" | "withdraw" | null>(null);

  useEffect(() => {
    if (!user) return;
    getCuenta(user.id).then(setCuenta);
    getAssets().then(setAssets);
    getPortfolio().then(setHoldings);
    getDolarQuotes()
      .then((value) => {
        setQuotes(value);
        setQuoteError(value.mep === null || value.mep <= 0);
      })
      .catch(() => setQuoteError(true));
  }, [user]);

  const rows = useMemo(
    () =>
      holdings.map((h) => {
        const a = assets.find((x) => x.symbol === h.symbol);
        const price = a?.price ?? h.avgPrice;
        const currency = a?.currency ?? h.currency;
        const value = price * h.qty;
        const pnl = (price - h.avgPrice) * h.qty;
        const valueArs = currency === "USD" ? value * (quotes.mep ?? 0) : value;
        const pnlArs = currency === "USD" ? pnl * (quotes.mep ?? 0) : pnl;
        return {
          ...h,
          name: a?.name ?? h.symbol,
          price,
          value,
          valueArs,
          pnl,
          pnlArs,
          pnlPct: ((price - h.avgPrice) / h.avgPrice) * 100,
        };
      }),
    [holdings, assets, quotes.mep],
  );

  const invertido = rows.reduce((s, r) => s + r.valueArs, 0);
  const totalArs = cuenta ? cuenta.saldo_ars + cuenta.saldo_usd * (quotes.mep ?? 0) + invertido : 0;
  const totalReady =
    cuenta !== null &&
    ((cuenta.saldo_usd === 0 && !rows.some((r) => r.currency === "USD")) ||
      (quotes.mep !== null && quotes.mep > 0));
  const totalPnl = rows.reduce((s, r) => s + r.pnlArs, 0);
  const conversionRate = moneda === "MEP" ? quotes.mep : quotes.ccl;
  const shownTotal = !totalReady
    ? "—"
    : moneda === "ARS"
      ? ars(totalArs)
      : conversionRate !== null && conversionRate > 0
        ? usd(totalArs / conversionRate)
        : "—";
  const pieData = rows.filter((r) => r.pnlArs > 0).map((r) => ({ name: r.symbol, value: r.pnlArs }));

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
              {cuenta && !totalReady && quoteError && (
                <p className="mt-1 text-sm text-loss">No se pudo obtener la cotización MEP para calcular el total.</p>
              )}
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
                  Cotización {conversionRate !== null ? ars(conversionRate) : "—"}
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

        <div className="mx-auto grid w-full max-w-2xl grid-cols-1 justify-center gap-4 py-2 sm:grid-cols-2" aria-label="Movimientos de dinero">
          <Button size="lg" onClick={() => setMoneyAction("deposit")} className="h-16 w-full px-6 text-lg [&_svg]:size-5">
            <ArrowDownToLine />Ingresar plata
          </Button>
          <Button size="lg" variant="outline" onClick={() => setMoneyAction("withdraw")} className="h-16 w-full px-6 text-lg [&_svg]:size-5">
            <ArrowUpFromLine />Retirar plata
          </Button>
        </div>

        <section className="border-t border-border pt-6">
          <div className="pb-4">
            <h2 className="font-display text-lg font-semibold">Mis inversiones</h2>
          </div>
          {rows.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aún no realizaste ninguna inversión.{" "}
              <Link to="/operar" className="text-primary">Comenzar ahora →</Link>
            </div>
          ) : (
            <>
              <div className="grid items-center gap-6 md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] md:gap-12">
                <div className="min-w-0">
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Rendimientos por activo</h3>
                  <div className="h-80 w-full md:h-96" aria-label="Gráfico de rendimientos por activo">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" innerRadius="48%" outerRadius="85%" paddingAngle={2} stroke="none" isAnimationActive={false}>
                          {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(v: number) => ars(v)}
                          contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                          itemStyle={{ color: "var(--foreground)" }} labelStyle={{ color: "var(--foreground)" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <ul className="w-full divide-y divide-border text-sm" aria-label="Rendimiento de mis activos">
                  {rows.map((r) => {
                    const idx = pieData.findIndex((p) => p.name === r.symbol);
                    return (
                      <li key={r.symbol} className="flex items-center justify-between gap-4 py-5">
                        <span className="flex min-w-0 items-center gap-3">
                          <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: idx >= 0 ? COLORS[idx % COLORS.length] : "var(--muted)" }} />
                          <span className="min-w-0">
                            <b>{r.symbol}</b>
                            <span className="mt-1 block break-words text-xs text-muted-foreground">{r.name}</span>
                          </span>
                        </span>
                        <span className={`shrink-0 font-mono text-base font-semibold ${r.pnl >= 0 ? "text-gain" : "text-loss"}`}>
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
      <Dialog open={moneyAction !== null} onOpenChange={(open) => { if (!open) setMoneyAction(null); }}>
        <DialogContent className="max-w-[calc(100%-2rem)] sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{moneyAction === "deposit" ? "Ingresar plata" : "Retirar plata"}</DialogTitle>
            <DialogDescription>
              {moneyAction === "deposit" ? "El ingreso de dinero" : "El retiro de dinero"} todavía no está habilitado. Esta cuenta utiliza saldos de prueba y no permite transferencias reales.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter><DialogClose asChild><Button variant="outline">Entendido</Button></DialogClose></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
