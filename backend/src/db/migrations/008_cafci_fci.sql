ALTER TABLE activo
    DROP CONSTRAINT IF EXISTS chk_activo_tipo;

ALTER TABLE activo
    ADD CONSTRAINT chk_activo_tipo
    CHECK (tipo IN ('accion', 'cedear', 'bono', 'etf', 'fci'));

ALTER TABLE activo
    ALTER COLUMN precio_actual TYPE NUMERIC(15, 6);

ALTER TABLE activo
    ADD COLUMN IF NOT EXISTS fecha_cotizacion DATE NULL;
