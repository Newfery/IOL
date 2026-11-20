ALTER TABLE activo
    ADD COLUMN IF NOT EXISTS variacion_porcentual NUMERIC(8, 4) NOT NULL DEFAULT 0;

DO $$
DECLARE
    existing_constraint RECORD;
BEGIN
    FOR existing_constraint IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'activo'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%tipo%'
    LOOP
        EXECUTE format(
            'ALTER TABLE activo DROP CONSTRAINT %I',
            existing_constraint.conname
        );
    END LOOP;
END $$;

ALTER TABLE activo
    ADD CONSTRAINT chk_activo_tipo
    CHECK (tipo IN ('accion', 'cedear', 'bono', 'etf'));
