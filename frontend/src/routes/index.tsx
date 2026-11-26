import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth";
import { createMovimiento, getAssets, getCuenta, getDolarQuotes, getPortfolio, type Asset, type Cuenta, type DolarQuotes, type Holding } from "@/lib/api";
import { createAssetColorMap, getAssetColor } from "@/lib/asset-colors";

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
const signedMoney = (n: number, currency: "ARS" | "USD") => {
  const sign = n >= 0 ? "+" : "-";
  const absolute = Math.abs(n);
  return `${sign}${currency === "USD" ? usd(absolute) : ars(absolute)}`;
};

function Home() {
  const { user } = useAuth();
  const [cuenta, setCuenta] = useState<Cuenta | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [quotes, setQuotes] = useState<DolarQuotes>({ mep: null, ccl: null });
  const [quoteError, setQuoteError] = useState(false);
  const [moneda, setMoneda] = useState<Moneda>("ARS");
  const [moneyAction, setMoneyAction] = useState<"deposit" | "withdraw" | null>(null);
  const [moneyCurrency, setMoneyCurrency] = useState<"ARS" | "USD">("ARS");
  const [moneyAmount, setMoneyAmount] = useState("");
  const [moneySubmitting, setMoneySubmitting] = useState(false);
  const [moneyError, setMoneyError] = useState("");
  const [moneySuccess, setMoneySuccess] = useState("");

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
  const pieData = rows.map((r) => ({ name: r.symbol, value: r.valueArs }));
  const colorBySymbol = useMemo(
    () => createAssetColorMap(rows.map((row) => row.symbol)),
    [rows],
  );

  function openMoneyDialog(action: "deposit" | "withdraw") {
    setMoneyAction(action);
    setMoneyCurrency("ARS");
    setMoneyAmount("");
    setMoneyError("");
    setMoneySuccess("");
  }

  async function submitMoneyMovement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || !cuenta || !moneyAction || moneySubmitting) return;

    const amount = Number(moneyAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setMoneyError("Ingresá un monto mayor a cero.");
      return;
    }

    setMoneySubmitting(true);
    setMoneyError("");
    try {
      await createMovimiento({
        cuenta_id: cuenta.id,
        tipo: moneyAction === "deposit" ? "deposito" : "extraccion",
        moneda: moneyCurrency,
        monto: amount,
      });
      setMoneySuccess(moneyAction === "deposit" ? "Depósito registrado correctamente." : "Retiro registrado correctamente.");
      try {
        setCuenta(await getCuenta(user.id));
      } catch {
        setMoneyError("El movimiento se registró, pero no se pudo actualizar el saldo. Cerrá este diálogo y recargá la página.");
      }
    } catch (error) {
      setMoneyError(error instanceof Error ? error.message : "No se pudo registrar el movimiento.");
    } finally {
      setMoneySubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        <div>
          <h1 className="font-display text-2xl font-semibold">Hola, {user?.nombre}</h1>
          <p className="text-sm text-muted-foreground">Comitente N° {cuenta?.numero_comitente} · Perfil {user?.perfil_riesgo}</p>
        </div>

        <section className="rounded-xl border border-border bg-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Total</p>
              <p className="mt-2 break-all font-display text-3xl font-semibold leading-tight sm:text-4xl">{shownTotal}</p>
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
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,1fr)]">
            <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="min-w-0 rounded-xl border border-border bg-card p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Pesos</p>
                <p className="mt-2 break-all font-display text-xl font-semibold tabular-nums sm:text-2xl">
                  {cuenta ? ars(cuenta.saldo_ars) : "—"}
                </p>
              </div>
              <div className="min-w-0 rounded-xl border border-border bg-card p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Dólares</p>
                <p className="mt-2 break-all font-display text-xl font-semibold tabular-nums sm:text-2xl">
                  {cuenta ? usd(cuenta.saldo_usd) : "—"}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2" aria-label="Movimientos de dinero">
              <Button
                size="lg"
                onClick={() => openMoneyDialog("deposit")}
                className="h-full min-h-14 w-full whitespace-nowrap px-3 text-sm sm:text-base [&_svg]:size-4"
              >
                <ArrowDownToLine />Ingresar plata
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => openMoneyDialog("withdraw")}
                className="h-full min-h-14 w-full whitespace-nowrap px-3 text-sm sm:text-base [&_svg]:size-4"
              >
                <ArrowUpFromLine />Retirar plata
              </Button>
            </div>
          </div>
        </section>

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
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Composición por valor actual</h3>
                  <div className="h-80 w-full md:h-96" aria-label="Composición de cartera por activo">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" innerRadius="48%" outerRadius="85%" paddingAngle={0} minAngle={8} stroke="var(--background)" strokeWidth={2} isAnimationActive={false}>
                          {pieData.map((entry) => (
                            <Cell key={entry.name} fill={getAssetColor(colorBySymbol, entry.name)} />
                          ))}
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
                    return (
                      <li key={r.symbol} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:py-5">
                        <span className="flex min-w-0 items-center gap-3">
                          <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: getAssetColor(colorBySymbol, r.symbol) }} />
                          <span className="min-w-0">
                            <Link
                              to="/activos/$symbol"
                              params={{ symbol: r.symbol }}
                              className="font-semibold hover:text-primary"
                            >
                              {r.symbol}
                            </Link>
                            <span className="mt-1 block break-words text-xs text-muted-foreground">{r.name}</span>
                          </span>
                        </span>
                        <span className={`self-end text-right font-mono text-sm font-semibold sm:shrink-0 sm:whitespace-nowrap sm:text-base ${r.pnl >= 0 ? "text-gain" : "text-loss"}`}>
                          {signedMoney(r.pnl, r.currency)} ({r.pnlPct >= 0 ? "+" : ""}{r.pnlPct.toFixed(1)}%)
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
              Registrá un movimiento en el saldo de prueba de tu cuenta.
            </DialogDescription>
          </DialogHeader>
          {moneySuccess ? (
            <div className="space-y-4">
              <p role="status" className="text-sm text-gain">{moneySuccess}</p>
              {moneyError && <p role="alert" className="text-sm text-loss">{moneyError}</p>}
              <DialogFooter>
                <DialogClose asChild><Button variant="outline">Cerrar</Button></DialogClose>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={submitMoneyMovement} className="space-y-4">
              <label className="block space-y-1 text-sm">
                <span>Moneda</span>
                <select
                  value={moneyCurrency}
                  onChange={(event) => {
                    if (event.target.value === "ARS" || event.target.value === "USD") {
                      setMoneyCurrency(event.target.value);
                    }
                  }}
                  disabled={moneySubmitting}
                  className="w-full rounded-md border border-input bg-background px-3 py-2"
                >
                  <option value="ARS">Pesos (ARS)</option>
                  <option value="USD">Dólares (USD)</option>
                </select>
              </label>
              <label className="block space-y-1 text-sm">
                <span>Monto</span>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                  value={moneyAmount}
                  onChange={(event) => setMoneyAmount(event.target.value)}
                  disabled={moneySubmitting}
                  className="w-full rounded-md border border-input bg-background px-3 py-2"
                />
              </label>
              {cuenta && (
                <p className="text-xs text-muted-foreground">
                  Saldo disponible: {moneyCurrency === "ARS" ? ars(cuenta.saldo_ars) : usd(cuenta.saldo_usd)}
                </p>
              )}
              {moneyError && <p role="alert" className="text-sm text-loss">{moneyError}</p>}
              <DialogFooter>
                <DialogClose asChild><Button variant="outline" type="button" disabled={moneySubmitting}>Cancelar</Button></DialogClose>
                <Button type="submit" disabled={!cuenta || moneySubmitting}>
                  {moneySubmitting ? "Procesando..." : moneyAction === "deposit" ? "Ingresar" : "Retirar"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
