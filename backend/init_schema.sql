-- 1. Habilitar extensión TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 2. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rfid_uid VARCHAR(50) UNIQUE,
    pin VARCHAR(10),
    departamento VARCHAR(100) DEFAULT 'General',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabla de Asistencias
CREATE TABLE IF NOT EXISTS asistencias (
    id SERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_id INT NOT NULL REFERENCES usuarios(id),
    metodo VARCHAR(20) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    dispositivo_id VARCHAR(50) DEFAULT 'ESP32_PORTAL_1',
    PRIMARY KEY (id, timestamp)
);

-- 4. Convertir en Hypertable de TimescaleDB
SELECT create_hypertable('asistencias', 'timestamp', if_not_exists => TRUE);

-- 5. Sembrar usuarios de prueba
INSERT INTO usuarios (documento, nombre, rfid_uid, pin, departamento)
VALUES 
  ('1001', 'Angie Gomez', '86557F05', '1234', 'Ingeniería'),
  ('1002', 'Juan Perez', 'EABB8005', '5678', 'Recursos Humanos'),
  ('1003', 'Maria Lopez', 'F1E2D3C4', '0000', 'Finanzas')
ON CONFLICT (documento) DO NOTHING;

-- 6. Sembrar datos de prueba recientes para que Grafana tenga datos que mostrar
INSERT INTO asistencias (timestamp, usuario_id, metodo, tipo, dispositivo_id)
VALUES
  (NOW() - INTERVAL '3 hours', 1, 'RFID', 'ENTRADA', 'ESP32_PORTAL_1'),
  (NOW() - INTERVAL '2 hours 30 minutes', 2, 'TECLADO', 'ENTRADA', 'ESP32_PORTAL_1'),
  (NOW() - INTERVAL '2 hours', 3, 'RFID', 'ENTRADA', 'ESP32_PORTAL_1'),
  (NOW() - INTERVAL '1 hour 15 minutes', 1, 'RFID', 'SALIDA', 'ESP32_PORTAL_1'),
  (NOW() - INTERVAL '45 minutes', 2, 'TECLADO', 'SALIDA', 'ESP32_PORTAL_1'),
  (NOW() - INTERVAL '10 minutes', 1, 'RFID', 'ENTRADA', 'ESP32_PORTAL_1');
