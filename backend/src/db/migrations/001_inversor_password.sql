ALTER TABLE inversor
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR;

ALTER TABLE inversor
    ADD COLUMN IF NOT EXISTS password_fingerprint VARCHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS uq_inversor_password_fingerprint
    ON inversor (password_fingerprint);
