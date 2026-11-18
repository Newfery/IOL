ALTER TABLE grupo_de_inversion ADD COLUMN password_hash VARCHAR(255);

CREATE TABLE aporte_grupo (
    id SERIAL PRIMARY KEY,
    grupo_id INT NOT NULL REFERENCES grupo_de_inversion(id) ON DELETE CASCADE,
    inversor_id INT NOT NULL REFERENCES inversor(id) ON DELETE CASCADE,
    monto DECIMAL(15, 2) NOT NULL CHECK (monto > 0),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_aporte_grupo_grupo_inversor ON aporte_grupo (grupo_id, inversor_id);
