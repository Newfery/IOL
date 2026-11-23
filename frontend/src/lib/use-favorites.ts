import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createFavorite, deleteFavorite, getFavoriteAssetIds, type Asset } from "@/lib/api";

export function useFavorites(inversorId: number | undefined, assets: Asset[]) {
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);
  const [pendingIds, setPendingIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const favoriteIdsRef = useRef(new Set<number>());
  const pendingIdsRef = useRef(new Set<number>());

  useEffect(() => {
    let active = true;
    favoriteIdsRef.current = new Set();
    pendingIdsRef.current.clear();
    setFavoriteIds([]);
    setPendingIds([]);
    setError("");
    setLoadError("");

    if (inversorId === undefined) {
      setLoading(false);
      return () => {
        active = false;
      };
    }

    setLoading(true);
    getFavoriteAssetIds(inversorId)
      .then((ids) => {
        if (active) {
          favoriteIdsRef.current = new Set(ids);
          setFavoriteIds(ids);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setLoadError(
            reason instanceof Error ? reason.message : "No se pudieron cargar los favoritos.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [inversorId]);

  const favorites = useMemo(
    () => assets.filter((asset) => favoriteIds.includes(asset.id)).map((asset) => asset.symbol),
    [assets, favoriteIds],
  );
  const pendingFavorites = useMemo(
    () => assets.filter((asset) => pendingIds.includes(asset.id)).map((asset) => asset.symbol),
    [assets, pendingIds],
  );

  const toggleFavorite = useCallback(
    async (symbol: string) => {
      if (inversorId === undefined) {
        setError("Iniciá sesión para administrar tus favoritos.");
        return;
      }

      const asset = assets.find((item) => item.symbol === symbol);
      if (!asset) {
        setError("No se encontró el activo seleccionado.");
        return;
      }

      if (pendingIdsRef.current.has(asset.id)) return;
      const wasFavorite = favoriteIdsRef.current.has(asset.id);
      pendingIdsRef.current.add(asset.id);
      setPendingIds((current) => [...current, asset.id]);
      setError("");

      try {
        if (wasFavorite) {
          await deleteFavorite(inversorId, asset.id);
        } else {
          await createFavorite(inversorId, asset.id);
        }

        const next = new Set(favoriteIdsRef.current);
        if (wasFavorite) next.delete(asset.id);
        else next.add(asset.id);
        favoriteIdsRef.current = next;
        setFavoriteIds([...next]);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "No se pudo actualizar el favorito.");
      } finally {
        pendingIdsRef.current.delete(asset.id);
        setPendingIds((current) => current.filter((id) => id !== asset.id));
      }
    },
    [assets, inversorId],
  );

  return { favorites, pendingFavorites, loading, error, loadError, toggleFavorite };
}
