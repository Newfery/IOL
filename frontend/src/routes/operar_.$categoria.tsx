import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, Search } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { AssetTable } from "@/components/AssetTable";
import { RequireAuth } from "@/components/RequireAuth";
import { getAssets, type Asset } from "@/lib/api";
import { findCategory } from "@/lib/categories";
import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/use-favorites";

export const Route = createFileRoute("/operar_/$categoria")({
  head: ({ params }) => {
    const category = findCategory(params.categoria);
    const title = category ? `${category.label} — Invertix` : "Categoría no disponible — Invertix";
    const description = category?.desc ?? "La categoría que buscás no está disponible.";
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
  loader: ({ params }) => {
    if (!findCategory(params.categoria)) throw notFound();
  },
  component: () => (
    <RequireAuth>
      <CategoryPage />
    </RequireAuth>
  ),
});

function CategoryPage() {
  const { categoria } = Route.useParams();
  const category = findCategory(categoria);
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
        if (active) setError(reason instanceof Error ? reason.message : "No se pudieron cargar los activos.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const categoryAssets = category?.type === "Favoritos"
    ? assets.filter((asset) => favorites.includes(asset.symbol))
    : assets.filter((asset) => category?.matches(asset) ?? false);
  const query = search.trim().toLowerCase();
  const shown = categoryAssets.filter(
    (asset) => !query
      || asset.symbol.toLowerCase().includes(query)
      || asset.name.toLowerCase().includes(query),
  );
  const emptyMessage = category?.type === "Favoritos" && !query
    ? "Todavía no tenés favoritos. Marcá activos con la estrella."
    : query
      ? "No hay activos que coincidan con la búsqueda."
      : "Todavía no hay activos en esta categoría.";
  const showTable = !loading
    && !error
    && !(category?.type === "Favoritos" && (favoritesLoading || favoritesLoadError));

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <Link
          to="/operar"
          className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a Invertir
        </Link>

        <section>
          <h1 className="font-display text-2xl font-semibold">{category?.label}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{category?.desc}</p>
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
        </section>

        {error && <p role="alert" className="text-sm text-loss">{error}</p>}
        {favoritesError && <p role="alert" className="text-sm text-loss">{favoritesError}</p>}
        {loading && <p role="status" className="text-sm text-muted-foreground">Cargando activos…</p>}
        {category?.type === "Favoritos" && favoritesLoading && (
          <p role="status" className="text-sm text-muted-foreground">Cargando favoritos…</p>
        )}
        {showTable && (
          <section className="overflow-x-auto rounded-lg border border-border bg-card">
            <AssetTable
              assets={shown}
              favorites={favorites}
              onToggleFavorite={toggleFavorite}
              emptyMessage={emptyMessage}
              pendingFavorites={pendingFavorites}
              favoriteActionsDisabled={favoritesLoading || Boolean(favoritesLoadError)}
            />
          </section>
        )}
      </main>
    </div>
  );
}
