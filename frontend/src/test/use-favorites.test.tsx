import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createFavorite, deleteFavorite, getFavoriteAssetIds, type Asset } from "@/lib/api";
import { useFavorites } from "@/lib/use-favorites";

vi.mock("@/lib/api", () => ({
  createFavorite: vi.fn(),
  deleteFavorite: vi.fn(),
  getFavoriteAssetIds: vi.fn(),
}));

const asset: Asset = {
  id: 45,
  symbol: "AAPL.US",
  name: "Apple",
  price: 100,
  change: 1,
  type: "Acción",
  currency: "USD",
};

describe("useFavorites", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads saved favorites and persists removals for the investor", async () => {
    vi.mocked(getFavoriteAssetIds).mockResolvedValue([asset.id]);
    vi.mocked(deleteFavorite).mockResolvedValue(undefined);

    const { result } = renderHook(() => useFavorites(12, [asset]));

    await waitFor(() => expect(result.current.favorites).toEqual([asset.symbol]));
    await act(async () => result.current.toggleFavorite(asset.symbol));

    expect(deleteFavorite).toHaveBeenCalledWith(12, asset.id);
    expect(result.current.favorites).toEqual([]);
  });

  it("does not mark an asset as favorite when saving fails", async () => {
    vi.mocked(getFavoriteAssetIds).mockResolvedValue([]);
    vi.mocked(createFavorite).mockRejectedValue(new Error("No se pudo guardar."));

    const { result } = renderHook(() => useFavorites(12, [asset]));

    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => result.current.toggleFavorite(asset.symbol));

    expect(createFavorite).toHaveBeenCalledWith(12, asset.id);
    expect(result.current.favorites).toEqual([]);
    expect(result.current.error).toBe("No se pudo guardar.");
  });
});
