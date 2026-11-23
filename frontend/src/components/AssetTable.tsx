import { Link } from "@tanstack/react-router";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Asset } from "@/lib/api";

const fmt = (value: number, currency: Asset["currency"]) =>
  value.toLocaleString("es-AR", { style: "currency", currency, maximumFractionDigits: 2 });

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
        </tr>
      </thead>
      <tbody>
        {assets.length === 0 && (
          <tr>
            <td colSpan={5} className="p-4 text-center text-sm text-muted-foreground">
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
            </td>
            <td className="p-4 text-muted-foreground">{asset.type}</td>
            <td className="p-4 text-right font-mono">{fmt(asset.price, asset.currency)}</td>
            <td className={`p-4 text-right font-mono ${asset.change >= 0 ? "text-gain" : "text-loss"}`}>
              {asset.change >= 0 ? "+" : ""}{asset.change.toFixed(2)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
