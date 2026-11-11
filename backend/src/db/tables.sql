-- 1. Tabla Inversor
    CREATE TABLE inversor (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        nombre VARCHAR(255) NOT NULL,
        cuit VARCHAR(11) UNIQUE NOT NULL,
        perfil_riesgo VARCHAR(20) NOT NULL,
        fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
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
        precio_actual DECIMAL(15, 4) NOT NULL,
        nivel_riesgo INT NOT NULL,
        activo BOOLEAN DEFAULT TRUE NOT NULL,
        
        -- HU2: Tipos y monedas válidas
        CONSTRAINT chk_activo_tipo CHECK (tipo IN ('accion', 'cedear', 'bono')),
        CONSTRAINT chk_activo_moneda CHECK (moneda IN ('ARS', 'USD')),
        -- HU2: Precio mayor a 0 y riesgo de 1 a 5
        CONSTRAINT chk_precio_actual CHECK (precio_actual > 0),
        CONSTRAINT chk_nivel_riesgo CHECK (nivel_riesgo BETWEEN 1 AND 5)
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
        CONSTRAINT chk_dividendo_monto CHECK (monto_por_unidad > 0)
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