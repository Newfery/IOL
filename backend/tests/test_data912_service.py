from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
from src.routers.dashboard_router import market_asset_history
from src.utils.errors import NotFoundError
from src.services.data912_service import (
    DATA912_ENDPOINTS,
    Data912HistoricalQuote,
    Data912HistoryNotFoundError,
    Data912Quote,
    parse_data912_bond_history,
    parse_data912_quotes,
    sync_data912_quotes,
)


class Data912ServiceTests(unittest.TestCase):
    def test_bond_history_parser_sorts_rows_and_maps_ohlc(self):
        quotes = parse_data912_bond_history(
            [
                {"date": "2026-11-24", "o": "102.5", "h": "104", "l": "101", "c": "103.25"},
                {"date": "2026-11-23", "o": "100", "h": "103", "l": "99.5", "c": "102"},
            ],
            "AL30",
        )

        self.assertEqual(
            quotes,
            [
                Data912HistoricalQuote(
                    date(2026, 11, 23),
                    Decimal("102.000000"),
                    Decimal("100.000000"),
                    Decimal("103.000000"),
                    Decimal("99.500000"),
                ),
                Data912HistoricalQuote(
                    date(2026, 11, 24),
                    Decimal("103.250000"),
                    Decimal("102.500000"),
                    Decimal("104.000000"),
                    Decimal("101.000000"),
                ),
            ],
        )

    def test_bond_history_parser_reports_unsupported_ticker(self):
        with self.assertRaises(Data912HistoryNotFoundError):
            parse_data912_bond_history(
                {"Error": "Nahh no tengo ese ticker loko"},
                "UNKNOWN",
            )

    def test_bond_history_endpoint_uses_data912_history(self):
        engine = create_engine("sqlite:///:memory:")
        Activo.__table__.create(engine)
        ActivoCotizacionHistorica.__table__.create(engine)
        db = sessionmaker(bind=engine)()
        try:
            db.add(Activo(
                ticker="AL30",
                nombre="Bono AL30",
                tipo="bono",
                moneda="ARS",
                precio_actual=Decimal("103"),
                nivel_riesgo=3,
            ))
            db.commit()
            history = [
                Data912HistoricalQuote(
                    date(2026, 11, 23),
                    Decimal("102"),
                    Decimal("100"),
                    Decimal("103"),
                    Decimal("99.5"),
                ),
                Data912HistoricalQuote(
                    date(2026, 11, 24),
                    Decimal("103.25"),
                    Decimal("102.5"),
                    Decimal("104"),
                    Decimal("101"),
                ),
            ]

            with (
                patch("src.routers.dashboard_router.fetch_data912_bond_history", return_value=history) as data912,
                patch("src.routers.dashboard_router.yf.Ticker") as yahoo_ticker,
            ):
                quotes = market_asset_history("AL30", db)

            data912.assert_called_once_with("AL30")
            yahoo_ticker.assert_not_called()
            self.assertEqual(quotes, [
                {
                    "date": "2026-11-23",
                    "price": 102.0,
                    "open": 100.0,
                    "high": 103.0,
                    "low": 99.5,
                },
                {
                    "date": "2026-11-24",
                    "price": 103.25,
                    "open": 102.5,
                    "high": 104.0,
                    "low": 101.0,
                },
            ])

            with (
                patch(
                    "src.routers.dashboard_router.fetch_data912_bond_history",
                    side_effect=Data912HistoryNotFoundError("unsupported"),
                ),
                patch("src.routers.dashboard_router.yf.Ticker") as yahoo_ticker,
            ):
                with self.assertRaises(NotFoundError):
                    market_asset_history("AL30", db)
            yahoo_ticker.assert_not_called()
        finally:
            db.close()
            engine.dispose()

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
                yahoo_ticker.return_value.history.return_value = pd.DataFrame(
                    {
                        "Open": [10.5, 11],
                        "High": [11, 12],
                        "Low": [10, 10.5],
                        "Close": [10.75, 11.5],
                    },
                    index=pd.to_datetime(["2026-11-23", "2026-11-24"]),
                )
                quotes = market_asset_history("TEST", db)

            yahoo_ticker.return_value.history.assert_called_once_with(
                period="1y",
                interval="1d",
                auto_adjust=False,
            )
            self.assertEqual(len(quotes), 2)
            self.assertEqual(quotes[0]["date"][:10], "2026-11-23")
            self.assertEqual(quotes[0]["price"], 10.75)
            self.assertEqual(quotes[1], {"date": "2026-11-24", "price": 13.0})
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
