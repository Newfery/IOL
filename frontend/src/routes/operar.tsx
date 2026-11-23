import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { AssetTable } from "@/components/AssetTable";
import { RequireAuth } from "@/components/RequireAuth";
import { getAssets, type Asset } from "@/lib/api";
import { CATEGORIES } from "@/lib/categories";
import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/use-favorites";

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

function Investments() {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [search, setSearch] = useState("");
  const [assetsLoading, setAssetsLoading] = useState(true);
  const [assetsError, setAssetsError] = useState("");
  const {
    favorites,
    pendingFavorites,
    loading: favoritesLoading,
    error: favoriteActionError,
    loadError: favoritesLoadError,
    toggleFavorite,
  } = useFavorites(user?.id, assets);
  const favoritesError = favoritesLoadError || favoriteActionError;

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
    return () => {
      active = false;
    };
  }, []);

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
        {favoritesError && <p role="alert" className="text-sm text-loss">{favoritesError}</p>}
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
              pendingFavorites={pendingFavorites}
              favoriteActionsDisabled={favoritesLoading || Boolean(favoritesLoadError)}
            />
          </section>
        )}
      </main>
    </div>
  );
}
