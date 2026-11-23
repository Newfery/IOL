CREATE TABLE IF NOT EXISTS favoritos (
    inversor_id INT NOT NULL REFERENCES inversor(id) ON DELETE CASCADE,
    activo_id INT NOT NULL REFERENCES activo(id) ON DELETE CASCADE,
    PRIMARY KEY (inversor_id, activo_id)
);

CREATE INDEX IF NOT EXISTS ix_favoritos_activo_id ON favoritos (activo_id);
