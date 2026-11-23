import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowDownRight, ArrowLeft, ArrowUpRight } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AppHeader } from "@/components/AppHeader";
import { OrderDialog } from "@/components/OrderDialog";
import { RequireAuth } from "@/components/RequireAuth";
import { Button } from "@/components/ui/button";
import { getAssets, getHistory, type Asset, type HistoryPoint } from "@/lib/api";
import { categoryForAsset } from "@/lib/categories";
import { HISTORY_RANGES, historyForRange } from "@/lib/asset-history";

export const Route = createFileRoute("/activos/$symbol")({
  head: ({ params }) => {
    const title = `${params.symbol} — Detalle del activo — Invertix`;
    const description = `Cotización e historial de precios de ${params.symbol} en Invertix.`;
    return {
      meta: [
        { title },
        { name: "description", content: description },
        { property: "og:title", content: title },
        { property: "og:description", content: description },
        { property: "og:type", content: "website" },
        { name: "twitter:card", content: "summary" },
      ],
    };
  },
  component: () => (
    <RequireAuth>
      <AssetDetail />
    </RequireAuth>
  ),
});

const fmt = (value: number, currency: Asset["currency"]) =>
  value.toLocaleString("es-AR", { style: "currency", currency, maximumFractionDigits: 2 });
const dateLabel = (value: string) =>
  new Date(`${value.slice(0, 10)}T00:00:00Z`).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  });

function AssetDetail() {
  const { symbol } = Route.useParams();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [days, setDays] = useState<number>(30);
  const [orderOpen, setOrderOpen] = useState(false);

  useEffect(() => {
    let active = true;
    setAsset(null);
    setHistory([]);
    setError("");
    setHistoryError("");
    setLoading(true);

    async function load() {
      try {
        const assets = await getAssets();
        if (!active) return;
        const matched = assets.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase());
        if (!matched) {
          setError("El activo que buscás no está disponible.");
          return;
        }
        setAsset(matched);

        try {
          const points = await getHistory(matched.symbol);
          if (active) {
            setHistory(
              points
                .map((point) => ({ ...point, date: point.date.slice(0, 10) }))
                .sort((left, right) => left.date.localeCompare(right.date)),
            );
          }
        } catch (reason) {
          if (active) {
            setHistoryError(reason instanceof Error ? reason.message : "No se pudo cargar el historial.");
          }
        }
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "No se pudo cargar el activo.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [symbol]);

  const points = historyForRange(history, days);
  const first = points[0];
  const last = points[points.length - 1];
  const change = first && last && first.price !== 0 ? (last.price / first.price - 1) * 100 : 0;
  const category = asset ? categoryForAsset(asset) : null;
  const prices = points.map((point) => point.price);
  const chartColor = change >= 0 ? "var(--gain)" : "var(--loss)";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
        {asset && category && (
          <Button asChild variant="outline">
            <Link to="/operar/$categoria" params={{ categoria: category.slug }}>
              <ArrowLeft /> Volver a {category.label}
            </Link>
          </Button>
        )}

        {loading && <p role="status" className="text-sm text-muted-foreground">Cargando activo…</p>}
        {error && (
          <section className="space-y-4">
            <p role="alert" className="text-sm text-loss">{error}</p>
            <Button asChild variant="outline"><Link to="/operar"><ArrowLeft /> Volver a Invertir</Link></Button>
          </section>
        )}

        {!loading && !error && asset && (
          <>
            <section className="flex flex-wrap items-start justify-between gap-6 border-b border-border pb-8">
              <div>
                <p className="mb-2 text-sm text-muted-foreground">{asset.type} · {asset.currency} · Cotización del mercado</p>
                <h1 className="font-display text-3xl font-semibold">{asset.symbol}</h1>
                <p className="mt-1 text-lg text-muted-foreground">{asset.name}</p>
              </div>
              <div className="space-y-3 sm:text-right">
                <p className="text-sm text-muted-foreground">Precio actual</p>
                <p className="font-mono text-3xl font-semibold">{fmt(asset.price, asset.currency)}</p>
                <p className={`flex items-center gap-1 text-sm sm:justify-end ${asset.change >= 0 ? "text-gain" : "text-loss"}`}>
                  {asset.change >= 0 ? <ArrowUpRight className="size-4" /> : <ArrowDownRight className="size-4" />}
                  {asset.change > 0 ? "+" : ""}{asset.change.toFixed(2)}% hoy
                </p>
                <Button onClick={() => setOrderOpen(true)}>Comprar / Vender</Button>
              </div>
            </section>

            <section aria-label="Historial de precios" className="space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="font-display text-xl font-semibold">Evolución del precio</h2>
                  <p className={`mt-1 font-mono text-sm ${change >= 0 ? "text-gain" : "text-loss"}`}>
                    {change >= 0 ? "+" : ""}{change.toFixed(2)}% en el período
                  </p>
                </div>
                <div className="flex flex-wrap gap-1" role="group" aria-label="Rango de tiempo">
                  {HISTORY_RANGES.map((range) => (
                    <Button
                      key={range.days}
                      size="sm"
                      variant={days === range.days ? "default" : "ghost"}
                      aria-pressed={days === range.days}
                      onClick={() => setDays(range.days)}
                    >
                      {range.label}
                    </Button>
                  ))}
                </div>
              </div>
              {historyError ? (
                <p role="alert" className="text-sm text-loss">{historyError}</p>
              ) : points.length > 0 ? (
                <>
                  <div className="h-80 w-full sm:h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={points} margin={{ top: 12, right: 12, bottom: 8, left: 0 }}>
                        <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tickFormatter={dateLabel}
                          minTickGap={45}
                          stroke="var(--muted-foreground)"
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          domain={["auto", "auto"]}
                          tickFormatter={(value: number) => value.toLocaleString("es-AR", { maximumFractionDigits: 0 })}
                          width={72}
                          stroke="var(--muted-foreground)"
                          tick={{ fontSize: 12 }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <Tooltip
                          formatter={(value: number) => fmt(value, asset.currency)}
                          labelFormatter={(label) => dateLabel(String(label))}
                          contentStyle={{
                            background: "var(--card)",
                            border: "1px solid var(--border)",
                            borderRadius: 8,
                            color: "var(--foreground)",
                          }}
                        />
                        <Line
                          type="linear"
                          dataKey="price"
                          stroke={chartColor}
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4 }}
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {first?.date} — {last?.date} · {asset.currency}
                  </p>
                </>
              ) : (
                <p className="py-12 text-muted-foreground">No hay cotizaciones históricas disponibles para este período.</p>
              )}
            </section>

            <section className="border-t border-border pt-6">
              <h2 className="mb-5 font-display text-xl font-semibold">Datos del activo</h2>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-6 md:grid-cols-4">
                {[
                  ["Ticker", asset.symbol],
                  ["Nombre", asset.name],
                  ["Tipo", asset.type],
                  ["Moneda", asset.currency],
                  ["Precio actual", fmt(asset.price, asset.currency)],
                  ["Variación diaria", `${asset.change > 0 ? "+" : ""}${asset.change.toFixed(2)}%`],
                  ["Mínimo del período", prices.length ? fmt(Math.min(...prices), asset.currency) : "—"],
                  ["Máximo del período", prices.length ? fmt(Math.max(...prices), asset.currency) : "—"],
                ].map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className="text-xs text-muted-foreground">{label}</dt>
                    <dd className="mt-1 break-words text-sm font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </>
        )}
      </main>
      {orderOpen && asset && <OrderDialog asset={asset} onClose={() => setOrderOpen(false)} />}
    </div>
  );
}
