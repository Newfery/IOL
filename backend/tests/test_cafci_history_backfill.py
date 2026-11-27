from datetime import date
from decimal import Decimal
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
from src.services.cafci_history_backfill import (
    FciComparisonPoint,
    _interpolated_price,
    _save_backfill_group,
    parse_comparator_html,
    reconstruct_nav_points,
)
from src.services.cafci_service import FciHistoricalPoint


class CafciHistoryBackfillTests(unittest.TestCase):
    def test_parse_comparator_html_keeps_available_weekly_returns(self):
        content = """
        <table>
          <tr><th>Fecha</th><th>Fondo A</th><th>Fondo B</th></tr>
          <tr><td>2025-11-28</td><td>+0,00 %</td><td>—</td></tr>
          <tr><td>2025-12-05</td><td>+2.50 %</td><td>-1.25 %</td></tr>
        </table>
        """

        result = parse_comparator_html(content, [101, 202])

        self.assertEqual(
            result[101],
            (
                FciComparisonPoint(date(2025, 11, 28), Decimal("0.00")),
                FciComparisonPoint(date(2025, 12, 5), Decimal("2.50")),
            ),
        )
        self.assertEqual(
            result[202],
            (FciComparisonPoint(date(2025, 12, 5), Decimal("-1.25")),),
        )

    def test_parse_comparator_html_logs_and_skips_an_invalid_cell(self):
        content = """
        <table>
          <tr><th>Fecha</th><th>Fondo A</th><th>Fondo B</th></tr>
          <tr><td>2025-11-28</td><td>+59.71.4.43 %</td><td>+1.00 %</td></tr>
        </table>
        """

        with self.assertLogs("src.services.cafci_history_backfill", level="WARNING"):
            result = parse_comparator_html(content, [101, 202])

        self.assertEqual(result[101], ())
        self.assertEqual(
            result[202],
            (FciComparisonPoint(date(2025, 11, 28), Decimal("1.00")),),
        )

    def test_parse_comparator_html_accepts_grouped_percentage_values(self):
        content = """
        <table>
          <tr><th>Fecha</th><th>Fondo A</th><th>Fondo B</th><th>Fondo C</th></tr>
          <tr>
            <td>2025-11-28</td>
            <td>+53.267.31 %</td>
            <td>+53.267,31 %</td>
            <td>+1,234.56 %</td>
          </tr>
        </table>
        """

        result = parse_comparator_html(content, [101, 202, 303])

        self.assertEqual(
            result[101],
            (FciComparisonPoint(date(2025, 11, 28), Decimal("53267.31")),),
        )
        self.assertEqual(
            result[202],
            (FciComparisonPoint(date(2025, 11, 28), Decimal("53267.31")),),
        )
        self.assertEqual(
            result[303],
            (FciComparisonPoint(date(2025, 11, 28), Decimal("1234.56")),),
        )

    def test_reconstruct_nav_points_anchors_cumulative_return_to_current_quote(self):
        result = reconstruct_nav_points(
            Decimal("110.000000"),
            (
                FciComparisonPoint(date(2025, 11, 28), Decimal("0")),
                FciComparisonPoint(date(2026, 11, 26), Decimal("10")),
            ),
            date(2026, 11, 26),
        )

        self.assertEqual(
            result,
            (
                FciHistoricalPoint(date(2025, 11, 28), Decimal("100.000000")),
                FciHistoricalPoint(date(2026, 11, 26), Decimal("110.000000")),
            ),
        )

    def test_reconstruct_nav_points_rejects_mismatched_anchor_date(self):
        result = reconstruct_nav_points(
            Decimal("110"),
            (FciComparisonPoint(date(2026, 11, 25), Decimal("10")),),
            date(2026, 11, 26),
        )

        self.assertEqual(result, ())

    def test_interpolated_price_only_uses_nearby_comparator_points(self):
        prices = (
            FciHistoricalPoint(date(2026, 11, 20), Decimal("100")),
            FciHistoricalPoint(date(2026, 11, 27), Decimal("107")),
        )
        self.assertEqual(
            _interpolated_price(date(2026, 11, 23), prices),
            Decimal("103"),
        )
        self.assertIsNone(_interpolated_price(date(2026, 11, 1), prices))

    def test_saving_backfill_preserves_plausible_prices_and_removes_percentage_outlier(self):
        engine = create_engine("sqlite:///:memory:")
        Activo.__table__.create(engine)
        ActivoCotizacionHistorica.__table__.create(engine)
        db = sessionmaker(bind=engine)()
        try:
            asset = Activo(
                ticker="FCI-1234",
                nombre="Fondo de prueba",
                tipo="fci",
                moneda="ARS",
                precio_actual=Decimal("107"),
                fecha_cotizacion=date(2026, 11, 27),
                variacion_porcentual=Decimal("0"),
                nivel_riesgo=3,
                activo=True,
            )
            db.add(asset)
            db.flush()
            db.add_all([
                ActivoCotizacionHistorica(
                    activo_id=asset.id,
                    fecha=date(2026, 11, 20),
                    precio=Decimal("102"),
                ),
                ActivoCotizacionHistorica(
                    activo_id=asset.id,
                    fecha=date(2026, 11, 23),
                    precio=Decimal("0.282"),
                ),
            ])
            db.commit()
            points = (
                FciHistoricalPoint(date(2026, 11, 20), Decimal("100")),
                FciHistoricalPoint(date(2026, 11, 27), Decimal("107")),
            )

            result = _save_backfill_group(db, [(asset, points)])

            self.assertEqual(result, (1, 0, 1))
            stored = db.query(ActivoCotizacionHistorica).filter(
                ActivoCotizacionHistorica.activo_id == asset.id,
            ).order_by(ActivoCotizacionHistorica.fecha).all()
            self.assertEqual(
                [(record.fecha, record.precio) for record in stored],
                [
                    (date(2026, 11, 20), Decimal("102.000000")),
                    (date(2026, 11, 27), Decimal("107.000000")),
                ],
            )
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
