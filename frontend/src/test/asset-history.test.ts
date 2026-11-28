import { describe, expect, it } from "vitest";

import { historyForRange } from "@/lib/asset-history";
import type { HistoryPoint } from "@/lib/api";

describe("asset chart history", () => {
  const history: HistoryPoint[] = [
    { date: "2025-01-01", price: 10 },
    { date: "2025-06-01", price: 15 },
    { date: "2025-12-01", price: 20 },
  ];

  it("applies the selected range to asset history", () => {
    expect(historyForRange(history, 30)).toEqual([history[2]]);
  });
});
