import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { AssetTable } from "@/components/AssetTable";
import { RequireAuth } from "@/components/RequireAuth";
import { getAssets, getPortfolio, type Asset, type Holding } from "@/lib/api";
import { CATEGORIES } from "@/lib/categories";

const FAVORITES_KEY = "invertix_favoritos";

export const Route = createFileRoute("/operar")({
  head: () => ({
    meta: [
      { title: "Invertir — Invertix" },
      { name: "description", content: "Explorá activos, categorías e inversiones disponibles en Invertix." },
      { property: "og:title", content: "Invertir — Invertix" },
      { property: "og:description", content: "Explorá activos, categorías e inversiones disponibles en Invertix." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <Investments />
    </RequireAuth>
  ),
});

const fmt = (value: number, currency: Asset["currency"]) =>
  value.toLocaleString("es-AR", { style: "currency", currency, maximumFractionDigits: 2 });

function Investments() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [assetsLoading, setAssetsLoading] = useState(true);
  const [assetsError, setAssetsError] = useState("");
  const [portfolioError, setPortfolioError] = useState("");

  useEffect(() => {
    let active = true;
    getAssets()
      .then((result) => {
        if (active) setAssets(result);
      })
      .catch((reason: unknown) => {
        if (active) setAssetsError(reason instanceof Error ? reason.message : "No se pudieron cargar los activos.");
      })
      .finally(() => {
        if (active) setAssetsLoading(false);
      });
    getPortfolio()
      .then((result) => {
        if (active) setHoldings(result);
      })
      .catch((reason: unknown) => {
        if (active) setPortfolioError(reason instanceof Error ? reason.message : "No se pudo cargar la cartera.");
      });
    try {
      const saved = JSON.parse(localStorage.getItem(FAVORITES_KEY) ?? "[]");
      if (Array.isArray(saved)) setFavorites(saved.filter((item): item is string => typeof item === "string"));
    } catch {
      setFavorites([]);
    }

    return () => {
      active = false;
    };
  }, []);

  function toggleFavorite(symbol: string) {
    setFavorites((previous) => {
      const next = previous.includes(symbol)
        ? previous.filter((item) => item !== symbol)
        : [...previous, symbol];
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(next));
      return next;
    });
  }

  const query = search.trim().toLowerCase();
  const results = assets.filter(
    (asset) => asset.symbol.toLowerCase().includes(query)
      || asset.name.toLowerCase().includes(query),
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        <section>
          <h1 className="font-display text-2xl font-semibold">¿En qué querés invertir?</h1>
          <p className="mt-1 text-sm text-muted-foreground">Explorá las categorías o buscá un activo por nombre o símbolo.</p>
          <div className="relative mt-4 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por nombre o símbolo"
              className="w-full rounded-md border border-input bg-card py-2 pl-9 pr-3 text-sm"
            />
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {CATEGORIES.map((category) => {
              const Icon = category.icon;
              return (
                <Link
                  key={category.slug}
                  to="/operar/$categoria"
                  params={{ categoria: category.slug }}
                  className="rounded-xl border border-border bg-card p-5 text-left transition-colors hover:bg-muted"
                >
                  <Icon className="h-6 w-6 text-muted-foreground" />
                  <p className="mt-3 font-display font-semibold">{category.label}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{category.desc}</p>
                </Link>
              );
            })}
          </div>
        </section>

        {assetsError && <p role="alert" className="text-sm text-loss">{assetsError}</p>}
        {assetsLoading && <p role="status" className="text-sm text-muted-foreground">Cargando activos…</p>}
        {query && !assetsLoading && !assetsError && (
          <section className="overflow-x-auto rounded-xl border border-border bg-card">
            <div className="border-b border-border p-4">
              <h2 className="font-display text-lg font-semibold">Resultados de búsqueda</h2>
            </div>
            <AssetTable
              assets={results}
              favorites={favorites}
              onToggleFavorite={toggleFavorite}
              emptyMessage="No hay activos que coincidan con la búsqueda."
            />
          </section>
        )}

        <section className="max-w-2xl rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-lg font-semibold">Mi cartera</h2>
            <Link to="/mis-inversiones" className="text-sm text-primary hover:underline">Ver detalle</Link>
          </div>
          {portfolioError && <p role="alert" className="mt-3 text-sm text-loss">{portfolioError}</p>}
          {!portfolioError && holdings.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">Todavía no tenés activos en tu cartera.</p>
          ) : (
            <ul className="mt-3 space-y-3 text-sm">
              {holdings.map((holding) => {
                const asset = assets.find((item) => item.symbol === holding.symbol);
                const price = asset?.price ?? holding.avgPrice;
                const currency = asset?.currency ?? holding.currency;
                const pnl = holding.avgPrice > 0 ? ((price - holding.avgPrice) / holding.avgPrice) * 100 : 0;
                return (
                  <li key={holding.symbol} className="flex justify-between gap-4">
                    <span>
                      <Link
                        to="/activos/$symbol"
                        params={{ symbol: holding.symbol }}
                        className="font-semibold hover:text-primary"
                      >
                        {holding.symbol}
                      </Link>
                      <span className="ml-2 text-muted-foreground">x{holding.qty}</span>
                    </span>
                    <span className={`font-mono ${pnl >= 0 ? "text-gain" : "text-loss"}`}>
                      {fmt(price * holding.qty, currency)} · {pnl.toFixed(1)}%
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
