CREATE TABLE IF NOT EXISTS activo_cotizacion_historica (
    id SERIAL PRIMARY KEY,
    activo_id INT NOT NULL REFERENCES activo(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    precio NUMERIC(15, 6) NOT NULL,
    CONSTRAINT uq_activo_cotizacion_historica_activo_fecha UNIQUE (activo_id, fecha),
    CONSTRAINT chk_activo_cotizacion_historica_precio CHECK (precio > 0)
);

INSERT INTO activo_cotizacion_historica (activo_id, fecha, precio)
SELECT id, fecha_cotizacion, precio_actual
FROM activo
WHERE tipo = 'fci' AND fecha_cotizacion IS NOT NULL AND precio_actual > 0
ON CONFLICT (activo_id, fecha) DO UPDATE SET precio = EXCLUDED.precio;
