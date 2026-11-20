import { RequireAuth } from "@/components/RequireAuth";
import { createFileRoute } from "@tanstack/react-router";
import { AppHeader } from "@/components/AppHeader";
import { useEffect, useState } from "react";
import { TrendingUp, Globe, Landmark, PieChart, Search, Star, X, type LucideIcon } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  getAssets,
  getHistory,
  getPortfolio,
  placeOrder,
  type Asset,
  type Holding,
  type HistoryPoint,
} from "@/lib/api";

export const Route = createFileRoute("/operar")({
  head: () => ({
    meta: [
      { title: "Operar — Invertix" },
      { name: "description", content: "Operá acciones, CEDEARs y bonos desde tu cuenta online." },
      { property: "og:title", content: "Operar — Invertix" },
      { property: "og:description", content: "Operá acciones, CEDEARs y bonos desde tu cuenta online." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <Index />
    </RequireAuth>
  ),
});

const fmt = (n: number, currency: Asset["currency"]) =>
  n.toLocaleString("es-AR", { style: "currency", currency, maximumFractionDigits: 2 });

const CATEGORIES: { key: string; label: string; desc: string; icon: LucideIcon; matches: (asset: Asset) => boolean }[] = [
  { key: "Favoritos", label: "Favoritos", desc: "Accedé rápido a los activos que más te interesan.", icon: Star, matches: () => true },
  { key: "Acción", label: "Acciones Argentina", desc: "Acciones de empresas argentinas cotizadas en BYMA.", icon: TrendingUp, matches: (asset) => asset.type === "Acción" && asset.currency === "ARS" },
  { key: "CEDEAR", label: "CEDEARs", desc: "Representaciones locales de activos extranjeros.", icon: Globe, matches: (asset) => asset.type === "CEDEAR" },
  { key: "Acción EE.UU.", label: "Acciones EE.UU.", desc: "Acciones estadounidenses operadas en dólares.", icon: TrendingUp, matches: (asset) => asset.type === "Acción" && asset.currency === "USD" },
  { key: "ETF", label: "ETFs", desc: "Fondos cotizados de acciones, bonos y otros mercados.", icon: PieChart, matches: (asset) => asset.type === "ETF" },
  { key: "Bono", label: "Bonos", desc: "Títulos de deuda pública con pagos de interés periódicos.", icon: Landmark, matches: (asset) => asset.type === "Bono" },
  { key: "FCI", label: "FCI", desc: "Fondos comunes de inversión administrados por profesionales.", icon: PieChart, matches: (asset) => asset.type === "FCI" },
];

function Index() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [filter, setFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Asset | null>(null);
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [qtyText, setQtyText] = useState("1");
  const qty = Math.max(0, Math.floor(Number(qtyText) || 0));
  const [err, setErr] = useState(false);
  const [msg, setMsg] = useState("");
  const [history, setHistory] = useState<HistoryPoint[]>([]);

  useEffect(() => {
    getAssets().then(setAssets);
    getPortfolio().then(setHoldings);
    try {
      setFavorites(JSON.parse(localStorage.getItem("invertix_favoritos") ?? "[]"));
    } catch { /* sin favoritos guardados */ }
  }, []);

  useEffect(() => {
    if (!selected) { setHistory([]); return; }
    getHistory(selected.symbol).then(setHistory).catch(() => setHistory([]));
  }, [selected]);

  function toggleFavorite(symbol: string) {
    setFavorites((prev) => {
      const next = prev.includes(symbol) ? prev.filter((s) => s !== symbol) : [...prev, symbol];
      localStorage.setItem("invertix_favoritos", JSON.stringify(next));
      return next;
    });
  }

  const shown = filter
    ? assets
        .filter((a) => filter === "Favoritos"
          ? favorites.includes(a.symbol)
          : CATEGORIES.find((category) => category.key === filter)?.matches(a) ?? false)
        .filter(
          (a) =>
            !search ||
            a.symbol.toLowerCase().includes(search.toLowerCase()) ||
            a.name.toLowerCase().includes(search.toLowerCase()),
        )
    : [];

  function openOrder(a: Asset) {
    setSelected(a);
    setSide("buy");
    setQtyText("1");
    setMsg("");
    setErr(false);
  }

  async function submit() {
    if (!selected) return;
    if (qty < 1) { setErr(true); setMsg("Ingresá una cantidad válida"); return; }
    try {
      await placeOrder({ symbol: selected.symbol, side, qty, price: selected.price });
      setErr(false);
      setMsg(`Orden ejecutada (${side === "buy" ? "compra" : "venta"} ${qty} ${selected.symbol})`);
      setHoldings(await getPortfolio());
    } catch (e) {
      setErr(true);
      setMsg((e as Error).message);
    }
  }

  const activeCategory = CATEGORIES.find((c) => c.key === filter);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />

      <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        <section>
          <h2 className="font-display text-2xl font-semibold">¿En qué querés invertir?</h2>
          <div className="relative mt-4 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nombre o símbolo"
              className="w-full rounded-md border border-input bg-card py-2 pl-9 pr-3 text-sm"
            />
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {CATEGORIES.map((c) => {
              const Icon = c.icon;
              const active = filter === c.key;
              return (
                <button
                  key={c.key}
                  onClick={() => setFilter(active ? null : c.key)}
                  className={`rounded-xl border p-5 text-left transition-colors ${
                    active
                      ? "border-primary bg-muted"
                      : "border-border bg-card hover:bg-muted"
                  }`}
                >
                  <Icon className={`h-6 w-6 ${active ? "text-primary" : "text-muted-foreground"}`} />
                  <p className="mt-3 font-display font-semibold">{c.label}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{c.desc}</p>
                </button>
              );
            })}
          </div>
        </section>

        {filter && (
          <section className="rounded-xl border border-border bg-card">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-4">
              <h2 className="font-display text-lg font-semibold">{activeCategory?.label}</h2>
              <button
                onClick={() => setFilter(null)}
                className="rounded-md bg-muted px-3 py-1 text-xs text-muted-foreground"
              >
                Volver a categorías
              </button>
            </div>
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="w-10 p-4"></th>
                  <th className="p-4">Símbolo</th>
                  <th className="p-4">Tipo</th>
                  <th className="p-4 text-right">Último</th>
                  <th className="p-4 text-right">Var. %</th>
                </tr>
              </thead>
              <tbody>
                {shown.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-sm text-muted-foreground">
                      {filter === "Favoritos" && !search
                        ? "Todavía no tenés favoritos. Marcá activos con la estrella."
                        : "No hay activos que coincidan con la búsqueda."}
                    </td>
                  </tr>
                )}
                {shown.map((a) => (
                  <tr
                    key={a.symbol}
                    onClick={() => openOrder(a)}
                    className="cursor-pointer border-t border-border hover:bg-muted"
                  >
                    <td className="p-4">
                      <button
                        onClick={(e) => { e.stopPropagation(); toggleFavorite(a.symbol); }}
                        aria-label={`Marcar ${a.symbol} como favorito`}
                        className="text-muted-foreground hover:text-primary"
                      >
                        <Star
                          className={`h-4 w-4 ${favorites.includes(a.symbol) ? "fill-primary text-primary" : ""}`}
                        />
                      </button>
                    </td>
                    <td className="p-4">
                      <div className="font-semibold">{a.symbol}</div>
                      <div className="text-xs text-muted-foreground">{a.name}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{a.type}</td>
                    <td className="p-4 text-right font-mono">{fmt(a.price, a.currency)}</td>
                    <td className={`p-4 text-right font-mono ${a.change >= 0 ? "text-gain" : "text-loss"}`}>
                      {a.change >= 0 ? "+" : ""}
                      {a.change.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="max-w-md rounded-xl border border-border bg-card p-5">
          <h2 className="font-display text-lg font-semibold">Mi cartera</h2>
          <ul className="mt-3 space-y-3 text-sm">
            {holdings.map((h) => {
              const p = assets.find((a) => a.symbol === h.symbol)?.price ?? h.avgPrice;
              const pnl = ((p - h.avgPrice) / h.avgPrice) * 100;
              return (
                <li key={h.symbol} className="flex justify-between">
                  <span>
                    <b>{h.symbol}</b> <span className="text-muted-foreground">x{h.qty}</span>
                  </span>
                  <span className={`font-mono ${pnl >= 0 ? "text-gain" : "text-loss"}`}>
                    {pnl.toFixed(1)}%
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      </main>

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-border bg-card p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-display text-lg font-semibold">Operar {selected.symbol}</h2>
                <p className="text-sm text-muted-foreground">
                  {selected.name} · {fmt(selected.price, selected.currency)}
                </p>
              </div>
              <button
                onClick={() => setSelected(null)}
                aria-label="Cerrar"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                onClick={() => setSide("buy")}
                className={`rounded-md py-2 text-sm font-semibold ${side === "buy" ? "bg-gain text-background" : "bg-muted"}`}
              >
                Comprar
              </button>
              <button
                onClick={() => setSide("sell")}
                className={`rounded-md py-2 text-sm font-semibold ${side === "sell" ? "bg-loss text-background" : "bg-muted"}`}
              >
                Vender
              </button>
            </div>
            {history.length > 0 && (
              <div className="mt-4 h-40 rounded-lg bg-background p-2" aria-label={`Historial de precio de ${selected.symbol}`}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={["auto", "auto"]} width={60} tick={{ fontSize: 10 }} />
                    <Tooltip
                      formatter={(value: number) => fmt(value, selected.currency)}
                      labelFormatter={(label) => String(label)}
                      contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--foreground)" }}
                      itemStyle={{ color: "var(--foreground)" }}
                      labelStyle={{ color: "var(--foreground)" }}
                    />
                    <Line type="monotone" dataKey="price" stroke="var(--primary)" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            <label className="mt-4 block text-xs text-muted-foreground">Cantidad</label>
            <input
              type="number"
              min={1}
              value={qtyText}
              onChange={(e) => setQtyText(e.target.value)}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
            />
            <div className="mt-3 flex justify-between text-sm">
              <span className="text-muted-foreground">Total estimado</span>
              <span className="font-mono">{fmt(selected.price * qty, selected.currency)}</span>
            </div>
            <button
              onClick={submit}
              className="mt-4 w-full rounded-md bg-primary py-2 font-semibold text-primary-foreground"
            >
              Confirmar orden
            </button>
            {msg && <p className={`mt-3 text-xs ${err ? "text-loss" : "text-gain"}`}>{msg}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
