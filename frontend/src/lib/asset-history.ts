import type { HistoryPoint } from "./api";

export const HISTORY_RANGES = [
  { label: "1 semana", days: 7 },
  { label: "1 mes", days: 30 },
  { label: "3 meses", days: 90 },
  { label: "6 meses", days: 180 },
  { label: "1 año", days: 365 },
] as const;

export function historyForRange(history: HistoryPoint[], days: number): HistoryPoint[] {
  const last = history[history.length - 1];
  if (!last) return [];

  const lastDay = last.date.slice(0, 10);
  const cutoff = new Date(`${lastDay}T00:00:00Z`);
  cutoff.setUTCDate(cutoff.getUTCDate() - days);
  const cutoffDay = cutoff.toISOString().slice(0, 10);

  return history.filter((point) => point.date.slice(0, 10) >= cutoffDay);
}

export function historyForAsset(
  history: HistoryPoint[],
  days: number,
  isFci: boolean,
): HistoryPoint[] {
  return isFci ? history : historyForRange(history, days);
}
