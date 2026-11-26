import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth";
import {
  getBalance,
  getDolarQuotes,
  getPlazos,
  getOrdenesPendientes,
  getPortfolio,
  type DolarQuotes,
  type Holding,
} from "@/lib/api";

export const Route = createFileRoute("/mi-dinero")({
  head: () => ({
    meta: [
      { title: "Invertix — Mi dinero" },
      { name: "description", content: "Tu dinero disponible, plazos y dinero invertido en activos." },
      { property: "og:title", content: "Invertix — Mi dinero" },
      { property: "og:description", content: "Disponible, plazos y dinero invertido en activos." },
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

function MiDinero() {
  const { user } = useAuth();
  const [balance, setBalance] = useState<{ ars: number; usd: number } | null>(null);
  const [quotes, setQuotes] = useState<DolarQuotes>({ mep: null, ccl: null });
  const [mepUnavailable, setMepUnavailable] = useState(false);
  const [moneda, setMoneda] = useState<Moneda>("ARS");
  const [oculto, setOculto] = useState(false);
  const [plazos, setPlazos] = useState<Awaited<ReturnType<typeof getPlazos>>>([]);
  const [pendientes, setPendientes] = useState<Awaited<ReturnType<typeof getOrdenesPendientes>>>([]);
  const [cartera, setCartera] = useState<Holding[] | null>(null);
  const [comprometidoReady, setComprometidoReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    Promise.allSettled([getBalance(), getDolarQuotes(), getPlazos(), getOrdenesPendientes(), getPortfolio()])
      .then(([b, q, p, o, h]) => {
        if (b.status === "fulfilled") setBalance(b.value);
        if (q.status === "fulfilled") {
          setQuotes(q.value);
          setMepUnavailable(q.value.mep === null || q.value.mep <= 0);
        }
        if (p.status === "fulfilled") setPlazos(p.value);
        if (o.status === "fulfilled") setPendientes(o.value);
        if (h.status === "fulfilled") setCartera(h.value);
        setComprometidoReady(o.status === "fulfilled" && h.status === "fulfilled");
        const failed = [b, q, p, o, h].find((result) => result.status === "rejected");
        if (failed?.status === "rejected") setError((failed.reason as Error).message);
      });
  }, [user]);

  const totalArs = balance?.ars ?? 0;
  const totalUsd = balance?.usd ?? 0;
  const fmt = (n: number) => (moneda === "ARS" ? ars(n) : usd(n));
  const monto = (a: number, u: number) => (moneda === "ARS" ? a : u);
  const ocultar = (s: string) => (oculto ? s.replace(/[0-9]/g, "*") : s);

  const invertidoArs = cartera?.reduce(
    (total, holding) => total + (holding.currency === "ARS" ? holding.qty * holding.avgPrice : 0),
    0,
  ) ?? 0;
  const invertidoUsd = cartera?.reduce(
    (total, holding) => total + (holding.currency === "USD" ? holding.qty * holding.avgPrice : 0),
    0,
  ) ?? 0;
  const comprometidoArs = invertidoArs + pendientes.reduce((s, p) => s + p.ars, 0);
  const comprometidoUsd = invertidoUsd + pendientes.reduce((s, p) => s + p.usd, 0);
  const tenenciasEnMoneda = cartera?.filter((holding) => holding.currency === moneda) ?? [];
  const pendientesEnMoneda = pendientes.filter((pending) => monto(pending.ars, pending.usd) > 0);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        <h1 className="font-display text-2xl font-semibold">Mi dinero</h1>
        {error && <p role="alert" className="text-sm text-loss">{error}</p>}

        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {(["ARS", "USD"] as Moneda[]).map((m) => (
            <button key={m} onClick={() => setMoneda(m)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-semibold ${moneda === m ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>
              {m === "ARS" ? "Pesos" : "Dólares"}
            </button>
          ))}
        </div>

        <section className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Tu disponible total</p>
              <p className="mt-2 break-all font-display text-3xl font-semibold leading-tight sm:text-4xl">
                {balance ? ocultar(fmt(moneda === "ARS" ? totalArs : totalUsd)) : "—"}
              </p>
              {moneda === "ARS" && balance && quotes.mep !== null && quotes.mep > 0 && (
                <p className="mt-1 text-sm text-muted-foreground">≈ {ocultar(usd(totalArs / quotes.mep))} al MEP</p>
              )}
              {moneda === "ARS" && balance && mepUnavailable && (
                <p className="mt-1 text-sm text-loss">Cotización MEP no disponible.</p>
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
            {plazos.map((p) => {
              const m = moneda === "ARS" ? p.ars : p.usd;
              return (
                <li key={p.label} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold">{p.label}</p>
                    <p className="text-xs text-muted-foreground">{p.detalle}</p>
                  </div>
                  <p className="break-all font-mono text-sm sm:text-right">{balance ? ocultar(fmt(m)) : "—"}</p>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border p-4">
            <h2 className="font-display text-lg font-semibold">Dinero comprometido</h2>
            <p className="text-xs text-muted-foreground">Invertido en activos a precio promedio y operaciones pendientes</p>
          </div>
          <div className="p-4">
            <p className="font-display text-2xl font-semibold">
              {comprometidoReady ? ocultar(fmt(monto(comprometidoArs, comprometidoUsd))) : "—"}
            </p>
            <ul className="mt-4 space-y-2">
              {tenenciasEnMoneda.map((holding) => (
                <li key={`holding-${holding.symbol}`} className="flex items-center justify-between gap-3 rounded-lg bg-muted px-4 py-3 text-sm">
                  <span className="min-w-0 break-words">{holding.symbol} · {holding.qty} unidades</span>
                  <span className="shrink-0 font-mono">{ocultar(fmt(holding.qty * holding.avgPrice))}</span>
                </li>
              ))}
              {pendientesEnMoneda.map((p) => (
                <li key={p.desc} className="flex items-center justify-between gap-3 rounded-lg bg-muted px-4 py-3 text-sm">
                  <span className="min-w-0 break-words">{p.desc}</span>
                  <span className="shrink-0 font-mono">{ocultar(fmt(monto(p.ars, p.usd)))}</span>
                </li>
              ))}
              {comprometidoReady && tenenciasEnMoneda.length === 0 && pendientesEnMoneda.length === 0 && (
                <li className="py-4 text-center text-sm text-muted-foreground">No tenés inversiones ni operaciones pendientes en esta moneda.</li>
              )}
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}
