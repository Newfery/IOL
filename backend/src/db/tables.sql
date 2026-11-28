-- 1. Tabla Inversor
    CREATE TABLE inversor (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        nombre VARCHAR(255) NOT NULL,
        cuit VARCHAR(11) UNIQUE NOT NULL,
        perfil_riesgo VARCHAR(20) NOT NULL,
        password_hash VARCHAR NOT NULL,
        password_fingerprint VARCHAR(64) NOT NULL,
        fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT uq_inversor_password_fingerprint UNIQUE (password_fingerprint),
        -- HU1: El CUIT debe tener exactamente 11 dígitos numéricos
        CONSTRAINT chk_cuit_length CHECK (cuit ~ '^[0-9]{11}$'),
        -- HU1: Perfiles válidos
        CONSTRAINT chk_perfil_riesgo CHECK (perfil_riesgo IN ('conservador', 'moderado', 'agresivo'))
    );

    -- 2. Tabla Cuenta
    CREATE TABLE cuenta (
        id SERIAL PRIMARY KEY,
        inversor_id INT UNIQUE NOT NULL, -- UNIQUE porque es 1 a 1
        numero_comitente VARCHAR(50) UNIQUE NOT NULL,
        saldo_ars DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
        saldo_usd DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
        
        CONSTRAINT fk_cuenta_inversor FOREIGN KEY (inversor_id) REFERENCES inversor(id) ON DELETE CASCADE,
        -- HU3 y HU4: El saldo no puede ser negativo (se restringe extracción mayor al saldo)
        CONSTRAINT chk_saldo_ars CHECK (saldo_ars >= 0),
        CONSTRAINT chk_saldo_usd CHECK (saldo_usd >= 0)
    );

    -- 3. Tabla Activo
    CREATE TABLE activo (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) UNIQUE NOT NULL,
        nombre VARCHAR(255) NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        moneda VARCHAR(3) NOT NULL,
        precio_actual DECIMAL(15, 6) NOT NULL,
        fecha_cotizacion DATE NULL,
        variacion_porcentual DECIMAL(8, 4) NOT NULL DEFAULT 0,
        nivel_riesgo INT NOT NULL,
        activo BOOLEAN DEFAULT TRUE NOT NULL,
        
        -- HU2: Tipos y monedas válidas
        CONSTRAINT chk_activo_tipo CHECK (tipo IN ('accion', 'cedear', 'bono', 'etf')),
        CONSTRAINT chk_activo_moneda CHECK (moneda IN ('ARS', 'USD')),
        -- HU2: Precio mayor a 0 y riesgo de 1 a 5
        CONSTRAINT chk_precio_actual CHECK (precio_actual > 0),
        CONSTRAINT chk_nivel_riesgo CHECK (nivel_riesgo BETWEEN 1 AND 5)
    );

    CREATE TABLE activo_cotizacion_historica (
        id SERIAL PRIMARY KEY,
        activo_id INT NOT NULL REFERENCES activo(id) ON DELETE CASCADE,
        fecha DATE NOT NULL,
        precio DECIMAL(15, 6) NOT NULL,
        CONSTRAINT uq_activo_cotizacion_historica_activo_fecha UNIQUE (activo_id, fecha),
        CONSTRAINT chk_activo_cotizacion_historica_precio CHECK (precio > 0)
    );

    -- 4. Tabla Operacion
    CREATE TABLE operacion (
        id SERIAL PRIMARY KEY,
        cuenta_id INT NOT NULL,
        activo_id INT NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        cantidad DECIMAL(18, 4) NOT NULL,
        precio_unitario DECIMAL(15, 4) NOT NULL,
        comision DECIMAL(15, 2) NOT NULL,
        total DECIMAL(15, 2) NOT NULL,
        resultado_realizado DECIMAL(15, 2), -- HU6: Para guardar ganancia/pérdida en ventas
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado VARCHAR(20) NOT NULL,
        liquidacion_dias INT NOT NULL DEFAULT 0 CHECK (liquidacion_dias BETWEEN 0 AND 2),
        liquidacion_acreditada BOOLEAN NOT NULL DEFAULT TRUE,
        fecha_liquidacion TIMESTAMP NULL,
        
        CONSTRAINT fk_operacion_cuenta FOREIGN KEY (cuenta_id) REFERENCES cuenta(id),
        CONSTRAINT fk_operacion_activo FOREIGN KEY (activo_id) REFERENCES activo(id),
        
        CONSTRAINT chk_operacion_tipo CHECK (tipo IN ('compra', 'venta')),
        CONSTRAINT chk_operacion_cantidad CHECK (cantidad > 0),
        CONSTRAINT chk_operacion_precio CHECK (precio_unitario > 0),
        CONSTRAINT chk_operacion_comision CHECK (comision >= 0),
        CONSTRAINT chk_operacion_estado CHECK (estado IN ('pendiente', 'ejecutada', 'rechazada'))
    );

    -- 5. Tabla Movimiento (Depósitos, extracciones, dividendos)
    CREATE TABLE movimiento (
        id SERIAL PRIMARY KEY,
        cuenta_id INT NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        moneda VARCHAR(3) NOT NULL,
        monto DECIMAL(15, 2) NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        descripcion TEXT,
        
        CONSTRAINT fk_movimiento_cuenta FOREIGN KEY (cuenta_id) REFERENCES cuenta(id),
        
        -- HU3: Movimientos son positivos. Las extracciones descuentan mediante lógica, pero el registro del monto absoluto es > 0.
        CONSTRAINT chk_movimiento_monto CHECK (monto > 0),
        CONSTRAINT chk_movimiento_tipo CHECK (tipo IN ('deposito', 'extraccion', 'dividendo')),
        CONSTRAINT chk_movimiento_moneda CHECK (moneda IN ('ARS', 'USD'))
    );

    -- 6. Tabla Dividendo
    CREATE TABLE dividendo (
        id SERIAL PRIMARY KEY,
        activo_id INT NOT NULL,
        monto_por_unidad DECIMAL(15, 4) NOT NULL,
        fecha_pago TIMESTAMP NOT NULL,
        
        CONSTRAINT fk_dividendo_activo FOREIGN KEY (activo_id) REFERENCES activo(id),
        CONSTRAINT chk_dividendo_monto CHECK (monto_por_unidad > 0),
        CONSTRAINT uq_dividendo_activo_fecha_pago UNIQUE (activo_id, fecha_pago)
    );

    -- 7. Tabla Intermedia: Tenencias (Cuenta - Activo)
    CREATE TABLE tenencia (
        cuenta_id INT NOT NULL,
        activo_id INT NOT NULL,
        cantidad DECIMAL(18, 4) NOT NULL,
        precio_promedio DECIMAL(15, 4) NOT NULL,
        
        PRIMARY KEY (cuenta_id, activo_id),
        CONSTRAINT fk_tenencia_cuenta FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE,
        CONSTRAINT fk_tenencia_activo FOREIGN KEY (activo_id) REFERENCES activo(id),
        
        CONSTRAINT chk_tenencia_cantidad CHECK (cantidad >= 0),
        CONSTRAINT chk_tenencia_precio CHECK (precio_promedio >= 0)
    );

    -- 8. Tabla Intermedia: Favoritos (Inversor - Activo)
    CREATE TABLE favoritos (
        inversor_id INT NOT NULL,
        activo_id INT NOT NULL,
        
        PRIMARY KEY (inversor_id, activo_id),
        CONSTRAINT fk_favoritos_inversor FOREIGN KEY (inversor_id) REFERENCES inversor(id) ON DELETE CASCADE,
        CONSTRAINT fk_favoritos_activo FOREIGN KEY (activo_id) REFERENCES activo(id) ON DELETE CASCADE
    );

-- Grupo de inversión
CREATE TABLE grupo_de_inversion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    codigo_union VARCHAR(50) UNIQUE NOT NULL,
    creador_id INT NOT NULL,
    password_hash VARCHAR(255),
    plata_disponible DECIMAL(15, 2) DEFAULT 0.00 NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_grupo_creador
        FOREIGN KEY (creador_id) REFERENCES inversor(id),

    CONSTRAINT chk_grupo_plata
        CHECK (plata_disponible >= 0)
);

CREATE TABLE aporte_grupo (
    id SERIAL PRIMARY KEY,
    grupo_id INT NOT NULL REFERENCES grupo_de_inversion(id) ON DELETE CASCADE,
    inversor_id INT NOT NULL REFERENCES inversor(id) ON DELETE CASCADE,
    monto DECIMAL(15, 2) NOT NULL CHECK (monto > 0),
    moneda VARCHAR(3) NOT NULL DEFAULT 'ARS'
        CHECK (moneda IN ('ARS', 'USD')),
    monto_original DECIMAL(15, 2) NOT NULL CHECK (monto_original > 0),
    cotizacion_mep DECIMAL(15, 4),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_aporte_grupo_cotizacion_mep CHECK (
        (moneda = 'ARS' AND cotizacion_mep IS NULL)
        OR (moneda = 'USD' AND cotizacion_mep > 0)
    )
);

CREATE INDEX ix_aporte_grupo_grupo_inversor ON aporte_grupo (grupo_id, inversor_id);

-- Integrantes del grupo
CREATE TABLE grupo_inversor (
    grupo_id INT NOT NULL,
    inversor_id INT NOT NULL,
    fecha_union TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (grupo_id, inversor_id),

    CONSTRAINT fk_grupo_inversor_grupo
        FOREIGN KEY (grupo_id) REFERENCES grupo_de_inversion(id) ON DELETE CASCADE,

    CONSTRAINT fk_grupo_inversor_inversor
        FOREIGN KEY (inversor_id) REFERENCES inversor(id) ON DELETE CASCADE
);

-- Acciones y otros activos que posee el grupo
CREATE TABLE tenencia_grupo (
    grupo_id INT NOT NULL,
    activo_id INT NOT NULL,
    cantidad DECIMAL(18, 4) NOT NULL,
    precio_promedio DECIMAL(15, 4) NOT NULL,

    PRIMARY KEY (grupo_id, activo_id),

    CONSTRAINT fk_tenencia_grupo_grupo
        FOREIGN KEY (grupo_id) REFERENCES grupo_de_inversion(id) ON DELETE CASCADE,

    CONSTRAINT fk_tenencia_grupo_activo
        FOREIGN KEY (activo_id) REFERENCES activo(id),

    CONSTRAINT chk_tenencia_grupo_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_tenencia_grupo_precio CHECK (precio_promedio >= 0)
);
