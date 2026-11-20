"""Sincroniza activos argentinos y un catálogo amplio de EE. UU. desde Yahoo Finance.

Ejecutar desde backend/: python -m src.db.seeders.yfinance_assets
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import logging
import time

import yfinance as yf
from yfinance import EquityQuery

from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo
# Register the target of Activo.inversores_favoritos for SQLAlchemy.
from src.db.models.inversor_model import Inversor

logger = logging.getLogger("yfinance_assets")

US_EQUITY_LIMIT = 500
US_EQUITY_PAGE_SIZE = 250
US_EQUITY_QUERY = EquityQuery("and", [
    EquityQuery("eq", ["region", "us"]),
    EquityQuery("gte", ["intradaymarketcap", 10_000_000_000]),
])

# Símbolo interno, símbolo Yahoo, nombre y tipo. La disponibilidad se valida
# consultando Yahoo al sincronizar; candidatos discontinuados se omiten.
CATALOG = [
    ("AGRO", "AGRO.BA", "Agrometal", "accion"),
    ("ALUA", "ALUA.BA", "Aluar", "accion"),
    ("BBAR", "BBAR.BA", "Banco BBVA Argentina", "accion"),
    ("BMA", "BMA.BA", "Banco Macro", "accion"),
    ("BYMA", "BYMA.BA", "Bolsas y Mercados Argentinos", "accion"),
    ("CEPU", "CEPU.BA", "Central Puerto", "accion"),
    ("COME", "COME.BA", "Sociedad Comercial del Plata", "accion"),
    ("CRES", "CRES.BA", "Cresud", "accion"),
    ("CVH", "CVH.BA", "Cablevisión Holding", "accion"),
    ("DGCU2", "DGCU2.BA", "Distribuidora de Gas Cuyana", "accion"),
    ("EDN", "EDN.BA", "Edenor", "accion"),
    ("GGAL", "GGAL.BA", "Grupo Galicia", "accion"),
    ("HARG", "HARG.BA", "Holcim Argentina", "accion"),
    ("INVJ", "INVJ.BA", "Inversora Juramento", "accion"),
    ("IRSA", "IRSA.BA", "IRSA", "accion"),
    ("LOMA", "LOMA.BA", "Loma Negra", "accion"),
    ("METR", "METR.BA", "Metrogas", "accion"),
    ("MIRG", "MIRG.BA", "Mirgor", "accion"),
    ("OEST", "OEST.BA", "Grupo Concesionario del Oeste", "accion"),
    ("PAMP", "PAMP.BA", "Pampa Energía", "accion"),
    ("SAMI", "SAMI.BA", "San Miguel", "accion"),
    ("SEMI", "SEMI.BA", "Molinos Juan Semino", "accion"),
    ("SUPV", "SUPV.BA", "Grupo Supervielle", "accion"),
    ("TECO2", "TECO2.BA", "Telecom Argentina", "accion"),
    ("TGNO4", "TGNO4.BA", "Transportadora de Gas del Norte", "accion"),
    ("TGSU2", "TGSU2.BA", "Transportadora de Gas del Sur", "accion"),
    ("TRAN", "TRAN.BA", "Transener", "accion"),
    ("TXAR", "TXAR.BA", "Ternium Argentina", "accion"),
    ("VALO", "VALO.BA", "Grupo Financiero Valores", "accion"),
    ("YPFD", "YPFD.BA", "YPF", "accion"),
    ("AAPL", "AAPL.BA", "Apple (CEDEAR)", "cedear"),
    ("AMZN", "AMZN.BA", "Amazon (CEDEAR)", "cedear"),
    ("AMD", "AMD.BA", "AMD (CEDEAR)", "cedear"),
    ("BABA", "BABA.BA", "Alibaba (CEDEAR)", "cedear"),
    ("DIS", "DIS.BA", "Disney (CEDEAR)", "cedear"),
    ("GOOGL", "GOOGL.BA", "Alphabet (CEDEAR)", "cedear"),
    ("INTC", "INTC.BA", "Intel (CEDEAR)", "cedear"),
    ("JPM", "JPM.BA", "JPMorgan (CEDEAR)", "cedear"),
    ("KO", "KO.BA", "Coca-Cola (CEDEAR)", "cedear"),
    ("MCD", "MCD.BA", "McDonald's (CEDEAR)", "cedear"),
    ("META", "META.BA", "Meta (CEDEAR)", "cedear"),
    ("MSFT", "MSFT.BA", "Microsoft (CEDEAR)", "cedear"),
    ("NFLX", "NFLX.BA", "Netflix (CEDEAR)", "cedear"),
    ("NKE", "NKE.BA", "Nike (CEDEAR)", "cedear"),
    ("NVDA", "NVDA.BA", "NVIDIA (CEDEAR)", "cedear"),
    ("PFE", "PFE.BA", "Pfizer (CEDEAR)", "cedear"),
    ("PYPL", "PYPL.BA", "PayPal (CEDEAR)", "cedear"),
    ("TSLA", "TSLA.BA", "Tesla (CEDEAR)", "cedear"),
    ("V", "V.BA", "Visa (CEDEAR)", "cedear"),
    ("WMT", "WMT.BA", "Walmart (CEDEAR)", "cedear"),
    ("XOM", "XOM.BA", "ExxonMobil (CEDEAR)", "cedear"),
    ("QQQ", "QQQ.BA", "Nasdaq 100 (CEDEAR)", "cedear"),
    ("SPY", "SPY.BA", "S&P 500 (CEDEAR)", "cedear"),
]

US_ETFS = [
    ("AGG", "iShares Core U.S. Aggregate Bond ETF"),
    ("ARKK", "ARK Innovation ETF"),
    ("BND", "Vanguard Total Bond Market ETF"),
    ("DIA", "SPDR Dow Jones Industrial Average ETF"),
    ("EEM", "iShares MSCI Emerging Markets ETF"),
    ("EFA", "iShares MSCI EAFE ETF"),
    ("GLD", "SPDR Gold Shares"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF"),
    ("IVV", "iShares Core S&P 500 ETF"),
    ("IWM", "iShares Russell 2000 ETF"),
    ("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF"),
    ("QQQ", "Invesco QQQ Trust"),
    ("QQQM", "Invesco NASDAQ 100 ETF"),
    ("SCHD", "Schwab U.S. Dividend Equity ETF"),
    ("SLV", "iShares Silver Trust"),
    ("SMH", "VanEck Semiconductor ETF"),
    ("SOXX", "iShares Semiconductor ETF"),
    ("SPY", "SPDR S&P 500 ETF Trust"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF"),
    ("VTI", "Vanguard Total Stock Market ETF"),
    ("VO", "Vanguard Mid-Cap ETF"),
    ("VOO", "Vanguard S&P 500 ETF"),
    ("VNQ", "Vanguard Real Estate ETF"),
    ("VT", "Vanguard Total World Stock ETF"),
    ("VUG", "Vanguard Growth ETF"),
    ("VTV", "Vanguard Value ETF"),
    ("VWO", "Vanguard FTSE Emerging Markets ETF"),
    ("XLE", "Energy Select Sector SPDR Fund"),
    ("XLF", "Financial Select Sector SPDR Fund"),
    ("XLK", "Technology Select Sector SPDR Fund"),
    ("XLRE", "Real Estate Select Sector SPDR Fund"),
    ("XLV", "Health Care Select Sector SPDR Fund"),
    ("XLY", "Consumer Discretionary Select Sector SPDR Fund"),
]


@dataclass(frozen=True)
class AssetQuote:
    ticker: str
    name: str
    asset_type: str
    currency: str
    price: Decimal
    change: Decimal


def fetch_price(item: tuple[str, str, str, str, str]) -> AssetQuote | None:
    ticker, yahoo_symbol, name, asset_type, currency = item
    last_error = None
    for attempt in range(3):
        try:
            prices = yf.Ticker(yahoo_symbol).history(
                period="5d", interval="1d", auto_adjust=True, raise_errors=True
            )["Close"].dropna()
            if prices.empty:
                return None
            price = Decimal(str(prices.iloc[-1])).quantize(Decimal("0.01"))
            if not price.is_finite() or price <= 0:
                return None
            change = Decimal("0")
            if len(prices) > 1:
                previous = Decimal(str(prices.iloc[-2]))
                if previous != 0:
                    change = (
                        (price - previous) / previous * Decimal("100")
                    ).quantize(Decimal("0.0001"))
            return AssetQuote(
                ticker=ticker,
                name=name,
                asset_type=asset_type,
                currency=currency,
                price=price,
                change=change,
            )
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    logger.info("Se omite %s: Yahoo Finance no devolvió un precio válido (%s)", yahoo_symbol, last_error)
    return None


def fetch_us_equities() -> list[AssetQuote]:
    first_page = yf.screen(
        US_EQUITY_QUERY,
        offset=0,
        size=US_EQUITY_PAGE_SIZE,
        sortField="intradaymarketcap",
        sortAsc=False,
    )
    total = first_page.get("total")
    if not isinstance(total, int) or total < 0:
        raise RuntimeError("Yahoo Finance devolvió un total inválido para acciones de EE. UU.")

    raw_quotes = list(first_page.get("quotes", []))
    target = min(total, US_EQUITY_LIMIT)
    if target and not raw_quotes:
        raise RuntimeError("Yahoo Finance no devolvió cotizaciones de acciones de EE. UU.")
    for offset in range(US_EQUITY_PAGE_SIZE, target, US_EQUITY_PAGE_SIZE):
        page = yf.screen(
            US_EQUITY_QUERY,
            offset=offset,
            size=min(US_EQUITY_PAGE_SIZE, target - offset),
            sortField="intradaymarketcap",
            sortAsc=False,
        )
        page_quotes = page.get("quotes", [])
        if not page_quotes:
            raise RuntimeError(
                f"Yahoo Finance devolvió una página vacía de acciones de EE. UU. (offset {offset})."
            )
        raw_quotes.extend(page_quotes)

    quotes_by_ticker: dict[str, AssetQuote] = {}
    for quote in raw_quotes[:target]:
        symbol = quote.get("symbol")
        currency = quote.get("currency")
        if not isinstance(symbol, str) or not symbol or currency != "USD":
            continue
        try:
            price = Decimal(str(quote["regularMarketPrice"])).quantize(Decimal("0.01"))
            change = Decimal(str(quote.get("regularMarketChangePercent") or 0)).quantize(
                Decimal("0.0001")
            )
        except (KeyError, InvalidOperation, TypeError, ValueError):
            continue
        if not price.is_finite() or price <= 0 or not change.is_finite():
            continue
        ticker = f"{symbol}.US"
        if len(ticker) > 20:
            continue
        quote_type = quote.get("quoteType")
        asset_type = "etf" if quote_type == "ETF" else "accion"
        quotes_by_ticker[ticker] = AssetQuote(
            ticker=ticker,
            name=quote.get("shortName") or quote.get("longName") or symbol,
            asset_type=asset_type,
            currency="USD",
            price=price,
            change=change,
        )
    return list(quotes_by_ticker.values())


def sync_assets() -> tuple[int, int, list[str], int]:
    local_candidates = [(*item, "ARS") for item in CATALOG]
    etf_candidates = [
        (f"{symbol}.US", symbol, name, "etf", "USD")
        for symbol, name in US_ETFS
    ]
    with ThreadPoolExecutor(max_workers=6) as pool:
        quote_results = list(
            pool.map(fetch_price, local_candidates + etf_candidates)
        )
    quotes_by_ticker = {
        quote.ticker: quote for quote in quote_results if quote is not None
    }

    us_equities = fetch_us_equities()
    for quote in us_equities:
        quotes_by_ticker.setdefault(quote.ticker, quote)
    quotes = list(quotes_by_ticker.values())

    inserted = updated = 0
    db = SessionLocal()
    try:
        for quote in quotes:
            asset = db.query(Activo).filter(
                Activo.ticker == quote.ticker
            ).one_or_none()
            if asset is None:
                asset = Activo(
                    ticker=quote.ticker,
                    nombre=quote.name,
                    tipo=quote.asset_type,
                    moneda=quote.currency,
                    precio_actual=quote.price,
                    variacion_porcentual=quote.change,
                    nivel_riesgo=3 if quote.asset_type in ("accion", "etf") else 4,
                    activo=True,
                )
                db.add(asset)
                inserted += 1
            else:
                asset.nombre = quote.name
                asset.tipo = quote.asset_type
                asset.moneda = quote.currency
                asset.precio_actual = quote.price
                asset.variacion_porcentual = quote.change
                asset.activo = True
                updated += 1
        db.commit()
        valid_tickers = set(quotes_by_ticker)
        skipped = [
            ticker
            for ticker, _, _, _ in CATALOG
            if ticker not in valid_tickers
        ]
        skipped.extend(
            f"{symbol}.US"
            for symbol, _ in US_ETFS
            if f"{symbol}.US" not in valid_tickers
        )
        return inserted, updated, skipped, len(us_equities)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    inserted, updated, skipped, us_equities = sync_assets()
    print(f"Acciones de EE. UU. validadas: {us_equities}")
    print(f"Activos nuevos: {inserted}; actualizados: {updated}; no disponibles en Yahoo: {len(skipped)}")
    if skipped:
        print("Omitidos: " + ", ".join(skipped))


if __name__ == "__main__":
    main()
