from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
from src.routers.dashboard_router import market_asset_history
from src.services.data912_service import (
    DATA912_ENDPOINTS,
    Data912Quote,
    parse_data912_quotes,
    sync_data912_quotes,
)


class Data912ServiceTests(unittest.TestCase):
    def test_parser_namespaces_us_tickers_and_uses_available_quote_if_close_is_missing(self):
        payloads = {
            path: [{
                "symbol": f"T{index}",
                "c": 10,
                "px_bid": 9,
                "px_ask": 11,
                "pct_change": 1.25,
            }]
            for index, (path, _) in enumerate(DATA912_ENDPOINTS)
        }
        payloads["/live/arg_cedears"][0].update(
            symbol="CEDEAR",
            c=0,
            px_bid=12,
            px_ask=0,
        )
        payloads["/live/usa_stocks"][0]["symbol"] = "AAPL"

        quotes = parse_data912_quotes(payloads, date(2026, 11, 24))
        quotes_by_ticker = {quote.ticker: quote for quote in quotes}

        self.assertEqual(quotes_by_ticker["AAPL.US"].price, Decimal("10.000000"))
        self.assertEqual(quotes_by_ticker["CEDEAR"].price, Decimal("12.000000"))
        self.assertEqual(quotes_by_ticker["CEDEAR"].quote_date, date(2026, 11, 24))

    def test_sync_updates_current_price_and_upserts_daily_history(self):
        engine = create_engine("sqlite:///:memory:")
        Activo.__table__.create(engine)
        ActivoCotizacionHistorica.__table__.create(engine)
        db = sessionmaker(bind=engine)()
        try:
            db.add(Activo(
                ticker="TEST",
                nombre="Test",
                tipo="accion",
                moneda="ARS",
                precio_actual=Decimal("10"),
                nivel_riesgo=3,
            ))
            db.commit()

            quote = Data912Quote(
                ticker="TEST",
                price=Decimal("12.500000"),
                change=Decimal("2.50"),
                quote_date=date(2026, 11, 24),
            )
            missing_quote = Data912Quote(
                ticker="MISSING",
                price=Decimal("5"),
                change=Decimal("0"),
                quote_date=date(2026, 11, 24),
            )
            self.assertEqual(sync_data912_quotes(db, [quote, missing_quote]), (1, 1))

            updated_quote = Data912Quote(
                ticker="TEST",
                price=Decimal("13.000000"),
                change=Decimal("4.00"),
                quote_date=date(2026, 11, 24),
            )
            sync_data912_quotes(db, [updated_quote])

            asset = db.query(Activo).filter(Activo.ticker == "TEST").one()
            history = db.query(ActivoCotizacionHistorica).filter(
                ActivoCotizacionHistorica.activo_id == asset.id
            ).one()
            self.assertEqual(asset.precio_actual, Decimal("13.000000"))
            self.assertEqual(asset.variacion_porcentual, Decimal("4.0000"))
            self.assertEqual(asset.fecha_cotizacion, date(2026, 11, 24))
            self.assertEqual(history.precio, Decimal("13.000000"))

            with patch("src.routers.dashboard_router.yf.Ticker") as yahoo_ticker:
                quotes = market_asset_history("TEST", db)

            yahoo_ticker.assert_not_called()
            self.assertEqual(quotes, [{"date": "2026-11-24", "price": 13.0}])
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
