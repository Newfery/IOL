import { describe, expect, it } from "vitest";

import { historyForAsset } from "@/lib/asset-history";
import type { HistoryPoint } from "@/lib/api";

describe("asset chart history", () => {
  const history: HistoryPoint[] = [
    { date: "2025-01-01", price: 10 },
    { date: "2025-06-01", price: 15 },
    { date: "2025-12-01", price: 20 },
  ];

  it("keeps all available FCI history instead of applying the hidden 30-day range", () => {
    expect(historyForAsset(history, 30, true)).toEqual(history);
  });

  it("applies the selected range to market assets", () => {
    expect(historyForAsset(history, 30, false)).toEqual([history[2]]);
  });
});
