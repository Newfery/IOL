ALTER TABLE aporte_grupo
    ADD COLUMN IF NOT EXISTS moneda VARCHAR(3) NOT NULL DEFAULT 'ARS';

ALTER TABLE aporte_grupo
    ADD COLUMN IF NOT EXISTS monto_original DECIMAL(15, 2);

ALTER TABLE aporte_grupo
    ADD COLUMN IF NOT EXISTS cotizacion_mep DECIMAL(15, 4);

UPDATE aporte_grupo
SET monto_original = monto
WHERE monto_original IS NULL;

ALTER TABLE aporte_grupo
    ALTER COLUMN monto_original SET NOT NULL;

DO $$ BEGIN
    ALTER TABLE aporte_grupo
        ADD CONSTRAINT chk_aporte_grupo_moneda
        CHECK (moneda IN ('ARS', 'USD'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aporte_grupo
        ADD CONSTRAINT chk_aporte_grupo_monto_original
        CHECK (monto_original > 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aporte_grupo
        ADD CONSTRAINT chk_aporte_grupo_cotizacion_mep
        CHECK (
            (moneda = 'ARS' AND cotizacion_mep IS NULL)
            OR (moneda = 'USD' AND cotizacion_mep > 0)
        );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
