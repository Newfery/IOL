ALTER TABLE operacion
    ADD COLUMN IF NOT EXISTS liquidacion_dias INT NOT NULL DEFAULT 0;

ALTER TABLE operacion
    ADD COLUMN IF NOT EXISTS liquidacion_acreditada BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE operacion
    ADD COLUMN IF NOT EXISTS fecha_liquidacion TIMESTAMP NULL;

DO $$ BEGIN
    ALTER TABLE operacion
        ADD CONSTRAINT chk_operacion_liquidacion_dias
        CHECK (liquidacion_dias BETWEEN 0 AND 2);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS ix_operacion_liquidacion_pendiente
    ON operacion (cuenta_id, fecha_liquidacion)
    WHERE liquidacion_acreditada = FALSE;
