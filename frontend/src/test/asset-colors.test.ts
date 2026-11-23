import { describe, expect, it } from "vitest";

import { createAssetColorMap, getAssetColor } from "@/lib/asset-colors";

describe("asset chart colors", () => {
  it("uses a distinct color for each symbol across currency charts", () => {
    const colors = createAssetColorMap(["ALUA", "AAPL.US", "BYMA", "ALUA"]);
    const arsSymbols = ["ALUA", "BYMA"];
    const usdSymbols = ["AAPL.US"];
    const chartColors = [...arsSymbols, ...usdSymbols].map((symbol) =>
      getAssetColor(colors, symbol),
    );

    expect(new Set(chartColors).size).toBe(chartColors.length);
    expect(getAssetColor(colors, "ALUA")).toBe(chartColors[0]);
  });

  it("returns the same color regardless of symbol input order", () => {
    const first = createAssetColorMap(["ALUA", "BYMA"]);
    const second = createAssetColorMap(["BYMA", "ALUA"]);

    expect(getAssetColor(first, "ALUA")).toBe(getAssetColor(second, "ALUA"));
    expect(getAssetColor(first, "BYMA")).toBe(getAssetColor(second, "BYMA"));
  });
});
