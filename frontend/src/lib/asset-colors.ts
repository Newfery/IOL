export function createAssetColorMap(symbols: Iterable<string>): Map<string, string> {
  const colorBySymbol = new Map<string, string>();
  const uniqueSymbols = [...new Set(symbols)].sort();

  uniqueSymbols.forEach((symbol, index) => {
    const hue = (index * 137.508) % 360;
    colorBySymbol.set(symbol, `hsl(${hue}, 70%, 52%)`);
  });

  return colorBySymbol;
}

export function getAssetColor(colors: ReadonlyMap<string, string>, symbol: string): string {
  return colors.get(symbol) ?? "var(--muted)";
}
