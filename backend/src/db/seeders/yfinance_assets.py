"""Sincroniza acciones BYMA y CEDEARs disponibles en Yahoo Finance al catálogo local.

Ejecutar desde backend/: python -m src.db.seeders.yfinance_assets
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import logging
import time

import yfinance as yf

from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo

logger = logging.getLogger("yfinance_assets")

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


def fetch_price(item: tuple[str, str, str, str]):
    ticker, yahoo_symbol, name, asset_type = item
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
            return ticker, name, asset_type, price
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    logger.info("Se omite %s: Yahoo Finance no devolvió un precio válido (%s)", yahoo_symbol, last_error)
    return None


def sync_assets() -> tuple[int, int, list[str]]:
    with ThreadPoolExecutor(max_workers=6) as pool:
        quotes = [quote for quote in pool.map(fetch_price, CATALOG) if quote is not None]

    inserted = updated = 0
    db = SessionLocal()
    try:
        for ticker, name, asset_type, price in quotes:
            asset = db.query(Activo).filter(Activo.ticker == ticker).one_or_none()
            if asset is None:
                asset = Activo(
                    ticker=ticker,
                    nombre=name,
                    tipo=asset_type,
                    moneda="ARS",
                    precio_actual=price,
                    nivel_riesgo=3 if asset_type == "accion" else 4,
                    activo=True,
                )
                db.add(asset)
                inserted += 1
            else:
                asset.nombre = name
                asset.tipo = asset_type
                asset.moneda = "ARS"
                asset.precio_actual = price
                asset.activo = True
                updated += 1
        db.commit()
        valid_tickers = {quote[0] for quote in quotes}
        skipped = [ticker for ticker, _, _, _ in CATALOG if ticker not in valid_tickers]
        return inserted, updated, skipped
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    inserted, updated, skipped = sync_assets()
    print(f"Activos nuevos: {inserted}; actualizados: {updated}; no disponibles en Yahoo: {len(skipped)}")
    if skipped:
        print("Omitidos: " + ", ".join(skipped))


if __name__ == "__main__":
    main()
