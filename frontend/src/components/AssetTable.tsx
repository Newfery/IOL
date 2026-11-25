import { Link } from "@tanstack/react-router";
import { ExternalLink, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Asset } from "@/lib/api";

const fmt = (asset: Asset) =>
  asset.price.toLocaleString("es-AR", {
    style: "currency",
    currency: asset.currency,
    maximumFractionDigits: asset.type === "FCI" ? 6 : 2,
  });
const quoteDateLabel = (value: string) => {
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
};
const tradingViewSearchUrl = (asset: Asset) => {
  const symbol = asset.symbol.replace(/\.US$/i, "");
  const query = asset.currency === "ARS" && asset.type !== "FCI" ? `BCBA:${symbol}` : symbol;
  return `https://www.tradingview.com/search/?query=${encodeURIComponent(query)}`;
};

export function AssetTable({
  assets,
  favorites,
  onToggleFavorite,
  emptyMessage,
  pendingFavorites = [],
  favoriteActionsDisabled = false,
}: {
  assets: Asset[];
  favorites: string[];
  onToggleFavorite: (symbol: string) => void | Promise<void>;
  emptyMessage: string;
  pendingFavorites?: string[];
  favoriteActionsDisabled?: boolean;
}) {
  return (
    <table className="w-full text-sm">
      <thead className="text-left text-xs uppercase text-muted-foreground">
        <tr>
          <th className="w-10 p-4" aria-label="Favorito" />
          <th className="p-4">Símbolo</th>
          <th className="p-4">Tipo</th>
          <th className="p-4 text-right">Último</th>
          <th className="p-4 text-right">Var. %</th>
          <th className="p-4 text-right">TradingView</th>
        </tr>
      </thead>
      <tbody>
        {assets.length === 0 && (
          <tr>
            <td colSpan={6} className="p-4 text-center text-sm text-muted-foreground">
              {emptyMessage}
            </td>
          </tr>
        )}
        {assets.map((asset) => (
          <tr key={asset.symbol} className="relative border-t border-border hover:bg-muted">
            <td className="p-4">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                disabled={favoriteActionsDisabled || pendingFavorites.includes(asset.symbol)}
                onClick={() => onToggleFavorite(asset.symbol)}
                aria-label={`${favorites.includes(asset.symbol) ? "Quitar" : "Marcar"} ${asset.symbol} ${favorites.includes(asset.symbol) ? "de" : "como"} favorito`}
                className="relative z-10 text-muted-foreground hover:text-primary"
              >
                <Star className={`h-4 w-4 ${favorites.includes(asset.symbol) ? "fill-primary text-primary" : ""}`} />
              </Button>
            </td>
            <td className="p-4">
              <Link
                to="/activos/$symbol"
                params={{ symbol: asset.symbol }}
                className="font-semibold after:absolute after:inset-0 focus-visible:outline-none focus-visible:after:ring-2 focus-visible:after:ring-ring"
              >
                {asset.symbol}
              </Link>
              <div className="text-xs text-muted-foreground">{asset.name}</div>
              {asset.type === "FCI" && asset.quoteDate && (
                <div className="text-xs text-muted-foreground">
                  Cuotaparte al {quoteDateLabel(asset.quoteDate)}
                </div>
              )}
            </td>
            <td className="p-4 text-muted-foreground">{asset.type}</td>
            <td className="p-4 text-right font-mono">{fmt(asset)}</td>
            <td className={`p-4 text-right font-mono ${asset.change >= 0 ? "text-gain" : "text-loss"}`}>
              {asset.change >= 0 ? "+" : ""}{asset.change.toFixed(2)}%
            </td>
            <td className="p-4 text-right">
              <a
                href={tradingViewSearchUrl(asset)}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Buscar ${asset.symbol} en TradingView`}
                className="relative z-10 inline-flex items-center gap-1 text-primary hover:underline"
              >
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                Abrir
              </a>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
