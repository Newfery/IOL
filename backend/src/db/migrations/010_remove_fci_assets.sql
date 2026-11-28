BEGIN;

LOCK TABLE
    activo,
    operacion,
    tenencia,
    tenencia_grupo,
    activo_cotizacion_historica,
    favoritos,
    dividendo
IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM tenencia_grupo tg
        JOIN activo a ON a.id = tg.activo_id
        WHERE a.tipo = 'fci'
    ) THEN
        RAISE EXCEPTION
            'FCI group holdings must be reconciled before removing FCI assets';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM dividendo d
        JOIN activo a ON a.id = d.activo_id
        WHERE a.tipo = 'fci'
    ) THEN
        RAISE EXCEPTION
            'FCI dividends must be reconciled before removing FCI assets';
    END IF;
END $$;

WITH fci_cash_adjustments AS (
    SELECT
        o.cuenta_id,
        SUM(
            CASE
                WHEN a.moneda = 'ARS' AND o.tipo = 'compra' THEN o.total
                WHEN a.moneda = 'ARS' AND o.tipo = 'venta'
                    AND o.liquidacion_acreditada THEN -o.total
                ELSE 0
            END
        ) AS ars_adjustment,
        SUM(
            CASE
                WHEN a.moneda = 'USD' AND o.tipo = 'compra' THEN o.total
                WHEN a.moneda = 'USD' AND o.tipo = 'venta'
                    AND o.liquidacion_acreditada THEN -o.total
                ELSE 0
            END
        ) AS usd_adjustment
    FROM operacion o
    JOIN activo a ON a.id = o.activo_id
    WHERE a.tipo = 'fci' AND o.estado = 'ejecutada'
    GROUP BY o.cuenta_id
)
UPDATE cuenta c
SET
    saldo_ars = c.saldo_ars + adjustments.ars_adjustment,
    saldo_usd = c.saldo_usd + adjustments.usd_adjustment
FROM fci_cash_adjustments adjustments
WHERE c.id = adjustments.cuenta_id;

DELETE FROM favoritos
WHERE activo_id IN (SELECT id FROM activo WHERE tipo = 'fci');

DELETE FROM tenencia
WHERE activo_id IN (SELECT id FROM activo WHERE tipo = 'fci');

DELETE FROM tenencia_grupo
WHERE activo_id IN (SELECT id FROM activo WHERE tipo = 'fci');

DELETE FROM activo_cotizacion_historica
WHERE activo_id IN (SELECT id FROM activo WHERE tipo = 'fci');

DELETE FROM operacion
WHERE activo_id IN (SELECT id FROM activo WHERE tipo = 'fci');

DELETE FROM activo
WHERE tipo = 'fci';

ALTER TABLE activo
    DROP CONSTRAINT IF EXISTS chk_activo_tipo;

ALTER TABLE activo
    ADD CONSTRAINT chk_activo_tipo
    CHECK (tipo IN ('accion', 'cedear', 'bono', 'etf'));

COMMIT;
